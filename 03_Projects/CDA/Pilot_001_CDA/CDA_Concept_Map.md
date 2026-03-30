---
title: CDA Concept Map
type: concept-map
status: draft
project: Pilot_001_CDA
tags:
  - aars
  - cda
  - concept-map
  - pilot
created: 2026-03-27
source: canonical CDA pilot concept map
---

# CDA Concept Map

## 1. Purpose

This document provides the initial concept map for the **Pilot_001_CDA** project.

Its purpose is to:
- express the structural relationships among CDA-related concepts
- connect glossary terms and taxonomy categories
- surface category overlap and layer-mixing risks
- provide a bridge from concept structuring to layer validation and architecture expression

This concept map is a **working structural note**, not a final framework.

---

## 2. Scope of the Map

This map focuses on the bounded pilot question:

**How should CDA be conceptually related to assets, properties, consequences, dependencies, methods, and governance concepts so that the pilot can proceed in a stable and reusable way?**

This map does **not** yet attempt:
- full formal ontology
- exhaustive domain decomposition
- detailed implementation architecture
- complete regulatory mapping

---

## 3. Core Structural Position

The core structural position of this pilot is:

**CDA is the central organizing concept.**  
A CDA is understood as a subset of [[Digital Asset]] whose importance emerges through [[Criticality]], consequence relevance, and dependency structure within a system context.

This means the concept map is anchored on the following relation:

```text
Digital Asset
    ↓ (evaluated by criticality, consequence, and dependency)
CDA
