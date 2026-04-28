# Skill: NPP Cybersecurity Regulatory Review

## Skill Purpose

Use this skill to review nuclear power plant cybersecurity laws, regulations, standards, guides, and compliance requirements.

The skill helps produce:

- regulatory baseline reports
- standards mapping tables
- compliance gap analysis
- design input requirements
- audit-ready review notes

## When to Use

Use this skill when the user asks to:

- 调研核电网络安全法规标准
- 建立核电 OT 网络安全合规基线
- 对比 IAEA / IEC / NRC / NIST / IEC 62443 / 中国标准
- 形成核电厂网络安全设计依据
- 判断某个系统是否需要纳入网络安全审查
- 为 AI 或 OT 系统建立法规标准依据

## Inputs Required

Ask or infer the following:

```text
1. Country / regulatory jurisdiction
2. Plant lifecycle phase
3. System type
4. Whether the system is safety-related, security-related, emergency-related, or operationally important
5. Whether OT, I&C, IT, AI, data platform, or remote access is involved
6. Required output type
```

If jurisdiction is not specified, provide both:

- International baseline
- China-oriented baseline

## Reference Framework

Use the following regulatory families:

International Nuclear Security:

- IAEA Nuclear Security Series
- IAEA NSS 42-G
- IAEA NSS 17-T Rev.1
- IAEA NSS 33-T

Nuclear I&C Cybersecurity:

- IEC 62645
- IEC 62859
- IEC 61513
- IEC 62138
- IEC 62566

US Nuclear Cybersecurity:

- NRC 10 CFR 73.54
- NRC RG 5.71
- NEI 08-09

OT / ICS Cybersecurity:

- NIST SP 800-82
- ISA/IEC 62443
- NIST CSF
- CISA CPG

China:

- 网络安全法
- 数据安全法
- 个人信息保护法
- 关键信息基础设施安全保护条例
- GB/T 22239
- GB/T 22240
- GB/T 25058
- GB/T 25070
- GB/T 39204
- GB/T 41241
- NB/T 20428

## Output Structure

Always produce the review in this structure:

```markdown
# Nuclear OT Cybersecurity Regulatory Review
## 1. Review Scope
## 2. Applicable Regulatory Families
## 3. Standards Mapping Table
| Standard / Regulation | Scope | Relevance to NPP OT | Design Implication |
|---|---|---|---|
## 4. Compliance Themes
- asset identification
- critical digital asset protection
- zoning and conduits
- defense in depth
- access control
- remote access
- supply chain security
- logging and monitoring
- vulnerability and patch management
- incident response
- lifecycle V&V
- AI governance if applicable
## 5. Design Input Requirements
## 6. Compliance Gap Questions
## 7. Review Conclusion
## 8. Recommended Next Step
```

## Decision Rules

Use these rules:

- If safety-important I&C is involved, prioritize IEC 62645, IEC 62859, IEC 61513, and IAEA NSS 33-T.
- If critical digital assets are involved, require CDA identification, consequence analysis, and governed protection.
- If remote access is involved, require default prohibition, exception approval, MFA, jump host, session recording, and expiry.
- If AI is involved, require AI risk assessment, model card, V&V, explainability, human review, and data boundary control.
- If OT data leaves the plant or controlled environment, require data classification, minimization, desensitization, and transfer control.

## Prohibited Output

Do not produce:

- Generic IT-only compliance advice.
- Unverified claims that a system is compliant.
- Advice to bypass nuclear safety or cybersecurity review.
- Recommendations for direct public-cloud upload of raw OT-sensitive data.

## Completion Criteria

The skill output is complete when it provides:

1. Applicable standards
2. Regulatory implications
3. Design requirements
4. Gap questions
5. Next engineering step

