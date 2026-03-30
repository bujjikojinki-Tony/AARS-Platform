const http = require("http");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

loadDotEnv(path.join(__dirname, ".env"));

const PORT = Number(process.env.PORT || 3000);
const WECHAT_PATH = process.env.WECHAT_PATH || "/wechat";
const WECHAT_TOKEN = process.env.WECHAT_TOKEN || "";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "";
const OPENAI_MODEL = process.env.OPENAI_MODEL || "gpt-5.1-codex-mini";
const OPENAI_TIMEOUT_MS = Number(process.env.OPENAI_TIMEOUT_MS || 4500);
const OPENAI_MAX_OUTPUT_TOKENS = Number(
  process.env.OPENAI_MAX_OUTPUT_TOKENS || 600
);
const OPENAI_REASONING_EFFORT =
  process.env.OPENAI_REASONING_EFFORT || "";
const SYSTEM_PROMPT =
  process.env.SYSTEM_PROMPT ||
  [
    "你是接入微信的 Codex 助手。",
    "回答要默认使用简体中文，优先给出直接可执行的答案。",
    "如果用户问编程问题，尽量提供代码和步骤。",
    "单次回复尽量控制在微信里易读的长度，必要时先给结论再给细节。",
  ].join("\n");

const sessions = new Map();

if (!WECHAT_TOKEN) {
  console.warn("[warn] 未设置 WECHAT_TOKEN，微信签名校验会失败。");
}

if (!OPENAI_API_KEY) {
  console.warn("[warn] 未设置 OPENAI_API_KEY，调用 Codex/OpenAI 会失败。");
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  if (url.pathname === "/health") {
    return sendJson(res, 200, {
      ok: true,
      service: "wechat-codex-bridge",
      model: OPENAI_MODEL,
      time: new Date().toISOString(),
    });
  }

  if (url.pathname !== WECHAT_PATH) {
    return sendText(res, 404, "Not Found");
  }

  try {
    if (req.method === "GET") {
      return handleWechatVerify(req, res, url);
    }

    if (req.method === "POST") {
      return handleWechatMessage(req, res, url);
    }

    return sendText(res, 405, "Method Not Allowed");
  } catch (error) {
    console.error("[server_error]", error);
    return sendText(res, 500, "Internal Server Error");
  }
});

server.listen(PORT, () => {
  console.log(
    `[ready] WeChat bridge listening on http://localhost:${PORT}${WECHAT_PATH}`
  );
  console.log(`[ready] Health check: http://localhost:${PORT}/health`);
});

function handleWechatVerify(_req, res, url) {
  const signature = url.searchParams.get("signature") || "";
  const timestamp = url.searchParams.get("timestamp") || "";
  const nonce = url.searchParams.get("nonce") || "";
  const echostr = url.searchParams.get("echostr") || "";

  if (!isValidWechatSignature(WECHAT_TOKEN, signature, timestamp, nonce)) {
    return sendText(res, 401, "invalid signature");
  }

  return sendText(res, 200, echostr);
}

async function handleWechatMessage(req, res, url) {
  const signature = url.searchParams.get("signature") || "";
  const timestamp = url.searchParams.get("timestamp") || "";
  const nonce = url.searchParams.get("nonce") || "";

  if (!isValidWechatSignature(WECHAT_TOKEN, signature, timestamp, nonce)) {
    return sendText(res, 401, "invalid signature");
  }

  const rawXml = await readRequestBody(req);
  const message = parseWechatXml(rawXml);

  if (!message.FromUserName || !message.ToUserName || !message.MsgType) {
    return sendText(res, 400, "bad request");
  }

  let replyText = "暂时无法识别这条消息。";

  if (message.MsgType === "event") {
    replyText = handleWechatEvent(message);
  } else if (message.MsgType === "text") {
    replyText = await handleWechatText(message);
  } else {
    replyText = "目前只演示处理文本消息。你可以直接发送文字给我。";
  }

  const replyXml = buildWechatTextReply({
    toUserName: message.FromUserName,
    fromUserName: message.ToUserName,
    content: replyText,
  });

  res.writeHead(200, { "Content-Type": "application/xml; charset=utf-8" });
  res.end(replyXml);
}

function handleWechatEvent(message) {
  if (message.Event === "subscribe") {
    return [
      "你好，Codex 微信助手已连接成功。",
      "直接发送问题给我即可。",
      "发送 /reset 可以清空当前会话上下文。",
    ].join("\n");
  }

  if (message.Event === "unsubscribe") {
    sessions.delete(message.FromUserName);
    return "";
  }

  return `收到事件：${message.Event || "unknown"}`;
}

async function handleWechatText(message) {
  const senderId = message.FromUserName;
  const userText = (message.Content || "").trim();

  if (!userText) {
    return "你可以直接发送文本问题给我。";
  }

  if (userText === "/reset" || userText === "重置会话") {
    sessions.delete(senderId);
    return "当前会话上下文已清空。";
  }

  if (!OPENAI_API_KEY) {
    return "服务端还没有配置 OPENAI_API_KEY。";
  }

  const previousResponseId = sessions.get(senderId);

  try {
    const result = await createOpenAIResponse({
      input: userText,
      previousResponseId,
      safetyIdentifier: sha256(senderId),
    });

    if (result.responseId) {
      sessions.set(senderId, result.responseId);
    }

    return result.outputText || "我收到了你的消息，但这次没有生成可显示的回复。";
  } catch (error) {
    console.error("[openai_error]", error);
    return "Codex 当前有点忙，请稍后再试。";
  }
}

async function createOpenAIResponse({
  input,
  previousResponseId,
  safetyIdentifier,
}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), OPENAI_TIMEOUT_MS);

  try {
    const payload = {
      model: OPENAI_MODEL,
      input,
      instructions: SYSTEM_PROMPT,
      max_output_tokens: OPENAI_MAX_OUTPUT_TOKENS,
      text: { verbosity: "medium" },
      store: true,
      safety_identifier: safetyIdentifier,
    };

    if (previousResponseId) {
      payload.previous_response_id = previousResponseId;
    }

    if (OPENAI_REASONING_EFFORT) {
      payload.reasoning = { effort: OPENAI_REASONING_EFFORT };
    }

    const response = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        `OpenAI API ${response.status}: ${JSON.stringify(data).slice(0, 500)}`
      );
    }

    return {
      responseId: data.id,
      outputText: extractOutputText(data),
    };
  } finally {
    clearTimeout(timer);
  }
}

function extractOutputText(data) {
  if (typeof data.output_text === "string" && data.output_text.trim()) {
    return data.output_text.trim();
  }

  const texts = [];
  const output = Array.isArray(data.output) ? data.output : [];

  for (const item of output) {
    if (item.type !== "message" || !Array.isArray(item.content)) {
      continue;
    }

    for (const content of item.content) {
      if (content.type === "output_text" && typeof content.text === "string") {
        texts.push(content.text);
      }
    }
  }

  return texts.join("\n").trim();
}

function buildWechatTextReply({ toUserName, fromUserName, content }) {
  const safeContent = content || "";
  return [
    "<xml>",
    cdataNode("ToUserName", toUserName),
    cdataNode("FromUserName", fromUserName),
    textNode("CreateTime", Math.floor(Date.now() / 1000)),
    cdataNode("MsgType", "text"),
    cdataNode("Content", safeContent),
    "</xml>",
  ].join("");
}

function cdataNode(tag, value) {
  return `<${tag}><![CDATA[${String(value ?? "")}]]></${tag}>`;
}

function textNode(tag, value) {
  return `<${tag}>${String(value ?? "")}</${tag}>`;
}

function parseWechatXml(xml) {
  return {
    ToUserName: readXmlTag(xml, "ToUserName"),
    FromUserName: readXmlTag(xml, "FromUserName"),
    CreateTime: readXmlTag(xml, "CreateTime"),
    MsgType: readXmlTag(xml, "MsgType"),
    Content: readXmlTag(xml, "Content"),
    MsgId: readXmlTag(xml, "MsgId"),
    Event: readXmlTag(xml, "Event"),
    EventKey: readXmlTag(xml, "EventKey"),
    MediaId: readXmlTag(xml, "MediaId"),
  };
}

function readXmlTag(xml, tag) {
  const cdataPattern = new RegExp(
    `<${tag}><!\\[CDATA\\[([\\s\\S]*?)\\]\\]><\\/${tag}>`
  );
  const textPattern = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`);

  const cdataMatch = xml.match(cdataPattern);
  if (cdataMatch) {
    return cdataMatch[1].trim();
  }

  const textMatch = xml.match(textPattern);
  if (textMatch) {
    return textMatch[1].trim();
  }

  return "";
}

function isValidWechatSignature(token, signature, timestamp, nonce) {
  if (!token || !signature || !timestamp || !nonce) {
    return false;
  }

  const raw = [token, timestamp, nonce].sort().join("");
  const expected = crypto.createHash("sha1").update(raw).digest("hex");
  return expected === signature;
}

function sha256(text) {
  return crypto.createHash("sha256").update(text).digest("hex");
}

function readRequestBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";

    req.setEncoding("utf8");
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function sendText(res, statusCode, text) {
  res.writeHead(statusCode, { "Content-Type": "text/plain; charset=utf-8" });
  res.end(text);
}

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(data, null, 2));
}

function loadDotEnv(filePath) {
  if (!fs.existsSync(filePath)) {
    return;
  }

  const content = fs.readFileSync(filePath, "utf8");
  const lines = content.split(/\r?\n/);

  for (const line of lines) {
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const index = trimmed.indexOf("=");
    if (index === -1) {
      continue;
    }

    const key = trimmed.slice(0, index).trim();
    const rawValue = trimmed.slice(index + 1).trim();
    const value = rawValue.replace(/^['"]|['"]$/g, "");

    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}
