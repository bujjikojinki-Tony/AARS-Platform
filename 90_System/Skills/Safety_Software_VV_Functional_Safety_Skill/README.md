# Safety Software V&V and Functional Safety Skill

This package turns the Safety Software V&V / Functional Safety baseline into an executable Codex skill.

## What it is for

- safety-related software V&V analysis
- IEEE 1012 / IEC 61508 / IEC 61511 application support
- SIS / SIF / SIL reasoning
- safety requirements and SRS drafting
- safety validation and evidence review
- change impact and gap analysis
- governed safety-engineering deliverables for AARS

## Package layout

- `SKILL.md`: executable skill instructions
- `templates/`: reusable output skeletons for governed document generation
- `references/`: compressed standard-logic summaries for stable judgement
- repo baseline documents:
  - `02_Knowledge/Skills/Safety_Engineering/01_Safety_Software_VV_Functional_Safety_Skill_v0.md`
  - `90_System/AARS/Capabilities/02_CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY.md`
  - `90_System/AARS/Prompt_Packs/03_Safety_VV_Functional_Safety_Prompt_Pack_v0.md`

## How to use

Ask Codex to use this skill when you want:

- a V&V plan
- a Safety Requirements Specification
- a SIF SRS
- a SIL claim review
- a safety evidence matrix
- a Safety Validation Report
- a change impact analysis
- a lifecycle gap review

Example:

> Use the Safety Software V&V and Functional Safety Skill to review whether our burner management logic change requires regression V&V and updated validation evidence.

## Notes

This package is advisory and engineering-support oriented. It helps produce structured, reviewable outputs but does not replace certification or regulatory review.
