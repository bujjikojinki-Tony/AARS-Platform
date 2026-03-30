# 微信连接 Codex 示例

这是一个最小可运行的 Node.js 示例，用来把微信公众号的消息转发给 Codex/OpenAI，再把回复以微信 XML 的形式返回。

建议使用 Node.js 18 或更高版本运行，因为示例直接用了内置 `fetch`。

## 这个示例能做什么

- 支持微信服务器 `GET` 校验
- 支持接收微信 `POST` 文本消息
- 调用 OpenAI `Responses API`
- 为每个微信用户保留一份内存态会话上下文
- 支持用户发送 `/reset` 或 `重置会话` 来清空上下文

## 文件说明

- `server.js`: 主程序，零第三方依赖
- `.env.example`: 环境变量模板

## 使用方式

1. 进入目录：

```bash
cd /Users/maolei/AARS-Platform/examples/wechat-codex-bridge
```

2. 准备配置：

- 新建 `.env`
- 参考 `.env.example` 填入 `WECHAT_TOKEN` 和 `OPENAI_API_KEY`
- `WECHAT_TOKEN` 必须和微信公众平台后台配置一致

3. 启动服务：

```bash
node server.js
```

4. 在微信公众平台里配置服务器：

- URL: `https://你的域名/wechat`
- Token: 与 `.env` 里的 `WECHAT_TOKEN` 保持一致
- 本示例按“明文模式”编写，未实现微信加解密模式的消息体解密

## 重要说明

- 这个示例默认只处理文本消息，图片、语音、菜单点击等消息没有展开实现。
- 这个示例没有实现微信加解密模式。如果你在后台启用了安全模式，还需要补 `msg_signature` 校验与 AES 解密逻辑。
- 会话上下文目前保存在进程内存里，服务重启后会丢失；生产环境建议改成 Redis 或数据库。
- 微信被动回复通常对超时较敏感，所以这里把 OpenAI 超时默认设为 `4500ms`。如果你的模型响应较慢，生产上更建议改成异步处理，再通过客服消息或其他主动消息机制回推结果。
- 这个示例主要面向“微信聊天接入 Codex”的原型验证。如果你要做企业微信、服务号客服、网页扫码登录，接法会不一样。

## 快速测试

服务启动后，可以先访问：

```bash
curl http://localhost:3000/health
```

如果返回 JSON，就说明本地服务已经起来了。

## 可改的几个点

- 想让它更像编程助手：改 `SYSTEM_PROMPT`
- 想节省成本：改 `OPENAI_MODEL`
- 想保留更长对话：把 `sessions` 改成持久化存储
- 想支持更多消息类型：扩展 `handleWechatMessage`
