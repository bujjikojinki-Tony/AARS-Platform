import {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  layers,
  panel,
  text,
  shape,
  chart,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  grow,
  fr,
  auto,
  drawSlideToCtx,
} from '@oai/artifact-tool';
import { Canvas } from '../node_modules/@oai/artifact-tool/node_modules/skia-canvas/lib/index.mjs';

const W = 1920;
const H = 1080;
const OUT = 'output/output.pptx';
const PREVIEW_DIR = 'scratch/previews';

const C = {
  ink: '#17202A',
  muted: '#5F6B7A',
  pale: '#EFF4F8',
  paper: '#F7FAFC',
  navy: '#17324D',
  blue: '#2B6CB0',
  cyan: '#1F9BB4',
  green: '#2F855A',
  amber: '#B7791F',
  red: '#C2410C',
  line: '#CBD5E1',
  white: '#FFFFFF',
  black: '#0B1020',
};

const font = 'Aptos';
const cnFont = 'PingFang SC';

function t(value, opts = {}) {
  return text(value, {
    width: opts.width ?? fill,
    height: opts.height ?? hug,
    ...opts,
    style: {
      typeface: opts.cn ? cnFont : font,
      fontSize: opts.size ?? 28,
      color: opts.color ?? C.ink,
      bold: opts.bold ?? false,
      alignment: opts.align,
      lineSpacing: opts.lineSpacing ?? 1.15,
      ...opts.style,
    },
  });
}

function footer(label = 'Source: thesis PDF; review lens: npp-cybersecurity-ai skill') {
  return row({ width: fill, height: hug, gap: 20 }, [
    rule({ width: fixed(160), stroke: C.line, weight: 2 }),
    t(label, { width: fill, size: 15, color: '#7A8796' }),
  ]);
}

function addSlide(p, body, bg = C.paper) {
  const slide = p.slides.add();
  slide.compose(
    layers({ width: fill, height: fill }, [
      shape({ name: 'background', width: fill, height: fill, fill: bg, stroke: 'none' }),
      body,
    ]),
    { frame: { left: 0, top: 0, width: W, height: H }, baseUnit: 8 },
  );
  return slide;
}

function titleStack(kicker, title, subtitle) {
  return column({ width: fill, height: hug, gap: 14 }, [
    t(kicker, { size: 18, color: C.cyan, bold: true, style: { letterSpacing: 0 } }),
    t(title, { size: 52, color: C.ink, bold: true, cn: true, width: wrap(1420), lineSpacing: 1.03 }),
    subtitle ? t(subtitle, { size: 24, color: C.muted, cn: true, width: wrap(1280), lineSpacing: 1.25 }) : null,
  ].filter(Boolean));
}

function bulletList(items, color = C.ink, size = 26) {
  return column({ width: fill, height: hug, gap: 16 }, items.map((item, i) =>
    row({ width: fill, height: hug, gap: 14 }, [
      t(String(i + 1).padStart(2, '0'), { width: fixed(42), size: 17, color: C.cyan, bold: true }),
      t(item, { width: fill, size, color, cn: true, lineSpacing: 1.22 }),
    ])
  ));
}

function tag(label, color) {
  return panel({ width: hug, height: hug, padding: { x: 18, y: 8 }, fill: color, borderRadius: 18 },
    t(label, { size: 17, color: C.white, bold: true, cn: true, width: hug }));
}

function verdictPill(label, score, color) {
  return column({ width: fill, height: hug, gap: 8 }, [
    row({ width: fill, height: hug, gap: 12 }, [
      t(label, { width: fill, size: 25, color: C.ink, bold: true, cn: true }),
      t(score, { width: fixed(78), size: 26, color, bold: true, align: 'right' }),
    ]),
    rule({ width: fill, stroke: '#D9E3EC', weight: 1 }),
  ]);
}

function chapterSlide(p, num, title, focus, points, review, accent = C.blue) {
  addSlide(p,
    column({ width: fill, height: fill, padding: { x: 86, y: 62 }, gap: 42 }, [
      titleStack(`CHAPTER ${num}`, title, focus),
      grid({ width: fill, height: grow(1), columns: [fr(1.12), fr(0.88)], rows: [fr(1)], columnGap: 58 }, [
        column({ width: fill, height: fill, gap: 22 }, [
          t('概要与重点', { size: 24, color: accent, bold: true, cn: true }),
          bulletList(points, C.ink, 25),
        ]),
        panel({ width: fill, height: fill, padding: { x: 34, y: 30 }, fill: C.white, borderRadius: 22, stroke: '#D9E3EC' },
          column({ width: fill, height: fill, gap: 22 }, [
            t('评审判断', { size: 24, color: C.ink, bold: true, cn: true }),
            t(review, { size: 27, color: C.ink, cn: true, lineSpacing: 1.28 }),
          ])),
      ]),
      footer(`Thesis chapter ${num}; extracted and reviewed from the supplied PDF`),
    ])
  );
}

function evaluationSlide(p, title, score, judgment, strengths, gaps, color) {
  addSlide(p,
    column({ width: fill, height: fill, padding: { x: 86, y: 62 }, gap: 36 }, [
      titleStack('REVIEW DIMENSION', title, judgment),
      row({ width: fill, height: grow(1), gap: 50 }, [
        column({ width: fixed(360), height: fill, gap: 20 }, [
          t(score, { size: 94, color, bold: true, width: fill, align: 'center' }),
          t('综合评分', { size: 24, color: C.muted, cn: true, align: 'center' }),
          rule({ width: fill, stroke: color, weight: 5 }),
          t('基于核电 OT 网络安全与 AI 治理技能包：AI 仅作为可解释、可审计、人工复核的证据生成能力。', { size: 22, color: C.muted, cn: true, lineSpacing: 1.3 }),
        ]),
        grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [fr(1)], columnGap: 36 }, [
          panel({ width: fill, height: fill, padding: { x: 32, y: 28 }, fill: '#FFFFFF', borderRadius: 20, stroke: '#D8E2EC' },
            column({ width: fill, height: fill, gap: 22 }, [
              t('成立之处', { size: 26, color: C.green, bold: true, cn: true }),
              bulletList(strengths, C.ink, 23),
            ])),
          panel({ width: fill, height: fill, padding: { x: 32, y: 28 }, fill: '#FFFFFF', borderRadius: 20, stroke: '#D8E2EC' },
            column({ width: fill, height: fill, gap: 22 }, [
              t('需要补强', { size: 26, color: C.red, bold: true, cn: true }),
              bulletList(gaps, C.ink, 23),
            ])),
        ]),
      ]),
      footer('Review dimensions: innovation, correctness, implementability, verifiability'),
    ])
  );
}

const p = Presentation.create({ slideSize: { width: W, height: H } });

// 1 Cover
addSlide(p,
  layers({ width: fill, height: fill }, [
    shape({ width: fill, height: fill, fill: '#0B1220', stroke: 'none' }),
    shape({ name: 'left-field', width: fixed(760), height: fill, fill: '#15314A', stroke: 'none' }),
    column({ width: fill, height: fill, padding: { x: 90, y: 78 }, gap: 46 }, [
      row({ width: fill, height: hug, gap: 16 }, [tag('论文大纲 PPT', C.cyan), tag('核电 OT / AI 异常检测评审', C.green)]),
      t('面向核电厂的人工智能异常检测\n与可解释网络安全分析', { size: 60, color: C.white, bold: true, cn: true, width: wrap(1160), lineSpacing: 1.05 }),
      t('章节概要、研究重点与四维评审判断', { size: 34, color: '#BFD7EA', cn: true, width: wrap(900) }),
      row({ width: fill, height: grow(1), gap: 52 }, [
        column({ width: fixed(560), height: hug, gap: 20 }, [
          t('核心评判', { size: 22, color: '#7DD3FC', bold: true, cn: true }),
          t('方向成立，架构有价值；但目前证据仍是方法可行性与实验室原型，不能直接等同于核电现场可部署成熟度。', { size: 30, color: C.white, cn: true, lineSpacing: 1.25 }),
        ]),
        column({ width: fixed(620), height: hug, gap: 22 }, [
          verdictPill('创新性', '4/5', '#7DD3FC'),
          verdictPill('正确性', '3/5', '#FBBF24'),
          verdictPill('可实施性', '2.5/5', '#FDBA74'),
          verdictPill('可验证性', '2.5/5', '#FDBA74'),
        ]),
      ]),
      t('Based on supplied thesis PDF | Review lens: NPP Cybersecurity AI Skill Pack', { size: 17, color: '#7E93AA' }),
    ]),
  ]), '#0B1220'
);

// 2 overview
addSlide(p,
  column({ width: fill, height: fill, padding: { x: 86, y: 62 }, gap: 34 }, [
    titleStack('EXECUTIVE READ', '这篇论文的主线：从跨层可观测到可治理规则', '不是“AI 接管核电网络安全”，而是把 AI 限定为异常发现、结构化解释与规则工程辅助。'),
    grid({ width: fill, height: grow(1), columns: [fr(1), fr(1), fr(1)], rows: [fr(1)], columnGap: 30 }, [
      panel({ width: fill, height: fill, padding: 30, fill: C.white, borderRadius: 20, stroke: '#D8E2EC' }, column({ width: fill, height: fill, gap: 20 }, [
        t('技术支柱一', { size: 24, color: C.blue, bold: true, cn: true }),
        t('跨层异常检测', { size: 36, color: C.ink, bold: true, cn: true }),
        t('网络、PLC、过程变量同步成 10 Hz 多变量序列；以正常样本训练 Dual TCN + Transformer 重构模型。', { size: 24, color: C.muted, cn: true, lineSpacing: 1.28 }),
      ])),
      panel({ width: fill, height: fill, padding: 30, fill: C.white, borderRadius: 20, stroke: '#D8E2EC' }, column({ width: fill, height: fill, gap: 20 }, [
        t('技术支柱二', { size: 24, color: C.green, bold: true, cn: true }),
        t('结构化规则合成', { size: 36, color: C.ink, bold: true, cn: true }),
        t('CauseCard 将遥测窗口转成可解析 JSON；LLM 仅用于离线结构化生成，再作为规则接口。', { size: 24, color: C.muted, cn: true, lineSpacing: 1.28 }),
      ])),
      panel({ width: fill, height: fill, padding: 30, fill: C.white, borderRadius: 20, stroke: '#D8E2EC' }, column({ width: fill, height: fill, gap: 20 }, [
        t('评审结论', { size: 24, color: C.red, bold: true, cn: true }),
        t('可作为方法论文', { size: 36, color: C.ink, bold: true, cn: true }),
        t('需要补齐法规标准映射、工程部署边界、独立验证集、V&V 门禁和告警治理对象。', { size: 24, color: C.muted, cn: true, lineSpacing: 1.28 }),
      ])),
    ]),
    footer('论文摘要、Chapter 1、Chapter 6-7'),
  ])
);

chapterSlide(p, '1', 'Introduction：问题定义与研究目标', '核电 OT 事件被定义为网络、控制器与物理过程耦合传播的问题。', [
  '研究动机：核电 OT 需要跨网络、控制、过程层的安全监测。',
  '核心问题：既要发现未知异常，又要输出可审查、可部署的监测知识。',
  '研究目标：构建闭环试验环境、normal-only 异常检测、结构化 CauseCard 与规则接口。',
], '问题设定准确，且主动声明不是现场可部署系统。建议进一步明确安全相关系统边界、CDA 范围和合规审查对象。', C.blue);

chapterSlide(p, '2', 'Background：相关工作与论文定位', '论文把核电 OT 网络安全放在 CPS 异常检测、XAI、OT-SIEM 和 LLM 辅助分析之间。', [
  '强调核电网络安全不是传统 IT 检测，而是 cyber-physical 监测。',
  '引用 TCN、Transformer、TranAD、DTAAD、POT 等方法基础。',
  '对 LLM 的定位较谨慎：生成受约束中间对象，而不是运行时自由决策。',
], '文献综述能支撑技术路线，但核电网络安全标准体系明显不足。应补 IEC 62645、IEC 62859、IAEA NSS、IEC 62443 与中国关保/等保映射。', C.cyan);

chapterSlide(p, '3', 'Testbed：跨层试验环境与数据基础', 'Asherah 仿真器 + 模拟 Siemens S7-1500 PLC + OPC UA + 抓包，形成三层同步数据。', [
  '三类数据：IT/network、PLC/controller、process/physical。',
  '10 Hz 对齐，16 分钟共 9600 行；10 分钟正常训练，3 个 2 分钟攻击评估。',
  '攻击场景：IT 网络扰动、PLC/ICS 操作、过程侧 false data injection。',
], '实验环境结构清楚，适合作方法验证；但正常数据时长和攻击覆盖太窄，不能代表真实机组长期工况、维护窗口、漂移和噪声。', C.green);

// 6 Chapter 4 with chart
addSlide(p,
  column({ width: fill, height: fill, padding: { x: 86, y: 62 }, gap: 34 }, [
    titleStack('CHAPTER 4', 'Data-driven anomaly detection：跨层异常检测', 'Dual TCN + Transformer 用重构误差发现异常，再用分组残差给出粗粒度域级诊断。'),
    grid({ width: fill, height: grow(1), columns: [fr(0.9), fr(1.1)], rows: [fr(1)], columnGap: 50 }, [
      column({ width: fill, height: fill, gap: 18 }, [
        t('重点', { size: 24, color: C.blue, bold: true, cn: true }),
        bulletList([
          '输入：100 步窗口，对应 10 秒跨层序列。',
          '阈值：POT 极值理论校准异常分数。',
          '诊断：按 IT / PLC / Process 三组聚合残差。',
          '结果：F1 0.945，ROC-AUC 0.985；域级诊断 accuracy 0.88。',
        ], C.ink, 24),
        t('评审：检测结果强于无监督基线，但 diagnosis 不是因果根因分析，只能作为 triage cue。', { size: 25, color: C.red, cn: true, lineSpacing: 1.26 }),
      ]),
      chart({
        name: 'f1-chart', width: fill, height: fill, chartType: 'bar',
        config: {
          title: 'Overall F1 comparison',
          categories: ['Proposed', 'TranAD', 'LSTM AE', 'WAN', 'CNN+Attn'],
          series: [{ name: 'F1', values: [0.945, 0.895, 0.799, 0.920, 0.890] }],
        },
      }),
    ]),
    footer('Thesis Table 4.2 and Table 4.4'),
  ])
);

chapterSlide(p, '5', 'CauseCard：结构化知识形式化与 LLM 辅助规则合成', 'LLM 被约束为离线生成 CauseCard JSON，运行时逻辑仍应是确定性规则。', [
  'Schema：label、cause.type、evidence[field, pattern]。',
  '模型：Llama-3-8B-Instruct，4-bit + LoRA 微调。',
  '评估：480 个 prepared corpus 样本上 JSON 有效率和分类指标均为 1.0。',
], '结构化生成思路很好，但评估过于乐观：最终混淆矩阵不是严格独立测试，且规则导出只到 schema-level interface。', C.green);

chapterSlide(p, '6-7', 'Discussion & Conclusion：混合监测架构的主张', '论文最终主张：异常检测负责发现，确定性规则负责治理与部署。', [
  '明确承认不是完整生产系统，证据来自仿真和实验室。',
  '提出未来架构：遥测基础层、异常发现层、结构化解释层、确定性规则层。',
  '结论克制：AI 是增强可视性、发现和审计逻辑生成的工具。',
], '总体结论方向正确，符合核电 OT 对可审计、可治理的要求。还需补充人类复核流程、变更控制、模型漂移和证据链管理。', C.amber);

// Architecture summary slide
addSlide(p,
  column({ width: fill, height: fill, padding: { x: 86, y: 62 }, gap: 34 }, [
    titleStack('ARCHITECTURE READ', '论文实际贡献是一条“发现到规则”的研究链', '最有价值的是把 anomaly score、结构化解释和规则治理放在同一条方法路径中。'),
    row({ width: fill, height: grow(1), gap: 22 }, [
      ['Telemetry\nfoundation', '网络 / PLC / 过程变量\n10 Hz 同步', C.blue],
      ['Anomaly\ndiscovery', 'Dual TCN + Transformer\nnormal-only reconstruction', C.cyan],
      ['Coarse\ndiagnosis', 'Grouped residual\nIT / PLC / Process', C.green],
      ['CauseCard\nformalization', '受约束 JSON\n原因 + 证据元组', C.amber],
      ['Rule\ninterface', '可审查、可测试\nOT-SIEM 规则雏形', C.red],
    ].map(([h, b, c]) => column({ width: grow(1), height: fill, gap: 18 }, [
      rule({ width: fill, stroke: c, weight: 7 }),
      t(h, { size: 33, color: C.ink, bold: true, width: fill, lineSpacing: 1.05 }),
      t(b, { size: 23, color: C.muted, cn: true, width: fill, lineSpacing: 1.22 }),
    ]))),
    footer('Synthesized from Chapters 3-6'),
  ])
);

// Review slides

evaluationSlide(p, '创新性评审：架构组合有价值，算法原创性中等偏上', '4/5', '创新主要体现在核电 OT 场景化集成，而非单一模型突破。', [
  '跨层遥测统一建模符合核电 cyber-physical 特征。',
  'CauseCard 将解释压缩为可审查中间对象。',
  'LLM 被限制为离线结构化生成，治理姿态正确。',
], [
  'Dual TCN + Transformer 与已有 DTAAD/TranAD 思路边界需讲清。',
  'CauseCard 与 LLM-LADE 的差异需要更明确。',
  '“核电厂”特色应通过标准、资产和工况进一步固化。',
], C.blue);

evaluationSlide(p, '正确性评审：方法自洽，但实验外推应保持克制', '3/5', '论文内部逻辑较严谨，最大问题是证据强度不足以支撑工程级结论。', [
  'normal-only 设定符合核电攻击标签稀缺现实。',
  'POT 阈值、训练集归一化、分组残差表述较规范。',
  '多处主动承认仿真/实验室限制，避免过度宣称。',
], [
  '10 分钟正常训练过短，难覆盖真实运行变化。',
  '第 5 章最终指标基于 prepared corpus，泛化证据弱。',
  'grouped residual 不应被表述为根因或因果归因。',
], C.amber);

evaluationSlide(p, '可实施性评审：原型路径清楚，工程部署边界不足', '2.5/5', '可做实验室原型或离线分析工具，但还不是核电 OT 现场部署方案。', [
  '被动采集、normal-only、确定性规则接口具备工程方向。',
  'LLM 不在运行时保护路径，降低自动化风险。',
  'SIEM-like rule interface 提供了后续落地入口。',
], [
  '未定义 OT 分区、工业 DMZ、单向传输和只读接口。',
  '未给出 CDA 清单、通信矩阵和远程访问边界。',
  '缺少告警生命周期、人类复核、审计导出和变更控制流程。',
], C.red);

evaluationSlide(p, '可验证性评审：有实验指标，缺 V&V 门禁', '2.5/5', '论文证明了“能跑通”，尚未证明“可被核电工程流程接受”。', [
  '第 4 章有对比基线、消融和诊断指标。',
  '第 5 章有 JSON 有效性和结构化输出评估。',
  '论文明确区分方法证据与现场部署证据。',
], [
  '缺少独立测试集、跨工况、噪声、缺失数据和漂移测试。',
  '缺少检测延迟、事件级评分和误报负担评估。',
  '缺少模型卡、数据卡、规则版本、阈值变更和回归验证记录。',
], C.red);

// Risk register
addSlide(p,
  column({ width: fill, height: fill, padding: { x: 86, y: 62 }, gap: 34 }, [
    titleStack('GAP REGISTER', '作为核电 OT 安全方案，还缺哪些关键证据', '这些不是否定论文，而是从方法论文走向工程方案必须补齐的门槛。'),
    grid({ width: fill, height: grow(1), columns: [fr(0.62), fr(1), fr(1)], rows: [auto, auto, auto, auto, auto], columnGap: 20, rowGap: 16 }, [
      t('类别', { size: 22, bold: true, color: C.navy, cn: true }),
      t('当前不足', { size: 22, bold: true, color: C.navy, cn: true }),
      t('建议补充', { size: 22, bold: true, color: C.navy, cn: true }),
      ...[
        ['法规', '核电网络安全标准映射不足', '补 IEC 62645 / IAEA NSS / IEC 62443 / 中国关保等保'],
        ['架构', '未给 OT 部署边界和 CDA 范围', '补分区分域、工业 DMZ、通信矩阵、只读采集'],
        ['模型', '泛化与漂移证据弱', '补长周期正常工况、噪声、缺失、漂移和未见攻击'],
        ['治理', '告警、人审、变更流程不足', '补告警对象、证据链、人工复核、模型/规则版本控制'],
      ].flatMap(([a,b,c]) => [
        t(a, { size: 24, bold: true, color: C.blue, cn: true }),
        t(b, { size: 23, color: C.ink, cn: true }),
        t(c, { size: 23, color: C.ink, cn: true }),
      ]),
    ]),
    footer('Mapped to NPP Cybersecurity AI Skill Pack constraints'),
  ])
);

// Revision path and final judgment
addSlide(p,
  column({ width: fill, height: fill, padding: { x: 86, y: 62 }, gap: 38 }, [
    titleStack('RECOMMENDED NEXT STEP', '建议把论文定位为“方法可行性 + 架构价值”', '若要增强答辩/评审说服力，优先补证据链，而不是继续堆模型复杂度。'),
    grid({ width: fill, height: grow(1), columns: [fr(1), fr(1)], rows: [fr(1)], columnGap: 46 }, [
      column({ width: fill, height: fill, gap: 24 }, [
        t('修改优先级', { size: 28, color: C.blue, bold: true, cn: true }),
        bulletList([
          '增加核电网络安全合规基线与标准映射。',
          '补充工程部署图：OT 只读采集、DMZ、规则执行区、审计库。',
          '把 CauseCard 扩展为完整 Alert Object。',
          '重新设计第 5 章独立验证与泛化测试。',
          '增加 V&V gates、模型卡、数据卡和变更控制。',
        ], C.ink, 24),
      ]),
      panel({ width: fill, height: fill, padding: { x: 36, y: 34 }, fill: '#102033', borderRadius: 24, stroke: 'none' }, column({ width: fill, height: fill, gap: 26 }, [
        t('最终评判', { size: 28, color: '#7DD3FC', bold: true, cn: true }),
        t('可通过为一篇有价值的方法研究论文；不宜宣称已形成核电厂可直接部署的成熟网络安全 AI 系统。', { size: 36, color: C.white, bold: true, cn: true, lineSpacing: 1.18 }),
        rule({ width: fill, stroke: '#365F7A', weight: 2 }),
        t('最好的表述是：提供跨层可观测、未知异常发现、结构化解释和规则工程之间的研究路径。', { size: 26, color: '#C6D7E5', cn: true, lineSpacing: 1.25 }),
      ])),
    ]),
    footer('Final review judgment'),
  ])
);

const pptxBlob = await PresentationFile.exportPptx(p);
await pptxBlob.save(OUT);

await import('node:fs').then(fs => fs.promises.mkdir(PREVIEW_DIR, { recursive: true }));
for (let i = 0; i < p.slides.items.length; i++) {
  const canvas = new Canvas(W, H);
  const ctx = canvas.getContext('2d');
  await drawSlideToCtx(p.slides.items[i], p, ctx);
  await canvas.toFile(`${PREVIEW_DIR}/slide-${String(i + 1).padStart(2, '0')}.png`);
}
console.log(JSON.stringify({ pptx: OUT, slides: p.slides.items.length, previews: PREVIEW_DIR }, null, 2));
