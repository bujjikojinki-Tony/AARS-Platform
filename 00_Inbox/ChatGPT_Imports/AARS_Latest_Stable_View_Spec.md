# AARS_Latest_Stable_View_Spec

## 1. Purpose
Define how AARS vNext identifies, represents, selects, and uses the latest stable continuation base across artifacts, threads, capabilities, and project states for recovery, resumption, rollback, and controlled progression.

## 2. View Scopes

### Core Scopes
- Artifact Stable View
- Thread Stable View
- Capability Stable View
- Project Stable View
- Release Stable View

## 3. Stability Model

### Stability States
- active draft
- reviewable
- stable
- conditionally stable
- stale-sensitive stable
- superseded
- unstable
- blocked

### Stability Priority Rule
When selecting a Latest Stable View, stable and conditionally stable states should be preferred over mere recency.

## 4. Stable View Object Schema

### Required Fields
- Stable View ID
- Stable View Scope
- Target Object Name or ID
- Selected Stable Version or Marker
- Stability State
- Stability Basis
- Safe Continuation Use
- Excluded Newer Alternatives Note

## 5. Selection Rules
1. Stability Before Recency
2. Scope Compatibility
3. Risk Compatibility
4. Dependency Compatibility
5. Acceptance Compatibility
6. Explicit Exclusion

## 6. Selection Procedure
1. Define Scope
2. Define Intended Use
3. Identify Candidate States
4. Filter by Blocking Instability
5. Compare Stability Basis
6. Select Preferred Stable Anchor
7. Record Excluded Newer Alternatives

## 7. Integration Rules

### Health Integration
- every health snapshot should identify at least one latest stable view where relevant
- absence of any stable anchor should be treated as a serious ops signal

### Risk Integration
- critical unresolved risk usually disqualifies a candidate from stable selection
- residual risk must be reflected in limitations

### Dependency Integration
- unsatisfied hard dependencies disqualify stable selection for dependent use cases

## 8. Minimal Acceptance Criteria
1. support artifact, thread, capability, project, and release stable views
2. prioritize stability over naive recency
3. integrate with health, risk, dependency, and rollback logic
4. explain why newer alternatives were excluded
5. support resume and recovery workflows with explicit anchors