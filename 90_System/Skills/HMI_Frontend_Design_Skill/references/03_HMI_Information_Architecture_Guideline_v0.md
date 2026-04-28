# 03 HMI Information Architecture Guideline v0

Source: `90_System/Guides/HMI/03_HMI_Information_Architecture_Guideline_v0.md`

## Stable rules

- use a four-layer hierarchy: overview, current task, diagnosis, raw data
- keep highest risk visible in the overview
- show current value, threshold, trend, freshness, source, confidence, risk explanation, and recommended action for key metrics
- sort tables by risk by default
- keep raw data out of the main overview

## Default layout

```text
Top Bar -> system status / time / freshness / automation mode
Left Panel -> object list / task list
Center Panel -> selected object main situation
Right Panel -> alarm / risk / opportunity queue
Bottom Bar -> latest stable view / step / quick action / recovery path
```

## How this file is used

Read this reference when organizing a page, deciding where information belongs, or defining component placement.
