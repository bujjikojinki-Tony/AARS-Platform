# 05 HMI Automation AI Interface Guideline v0

Source: `90_System/Guides/HMI/05_HMI_Automation_AI_Interface_Guideline_v0.md`

## Stable rules

- automation should always expose mode, input, reasoning, output, confidence, boundary, and human override
- recommendations should be card-like objects, not opaque labels
- higher autonomy requires tighter human control
- high-risk actions should not be fully autonomous by default
- AI output should be auditable

## How this file is used

Read this reference when designing AI assistant surfaces, recommendation cards, or automation state indicators.
