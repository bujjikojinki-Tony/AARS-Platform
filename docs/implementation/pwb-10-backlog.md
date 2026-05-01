# PWB-10 Backlog

## 1. Round Summary
PWB-10 is a read-only governed activation-readiness review round.

It follows the accepted approval-window review baseline and exposes activation-readiness context without changing runtime behavior.

## 2. Deliverables
- activation-readiness review models
- SQLite tables and indexes
- repository methods
- read-only activation-readiness review service
- read-only activation-readiness review APIs
- dashboard shell visibility
- acceptance tests
- freeze docs

## 3. Phase A/B - Models and Storage
- define activation-readiness review models and enums
- extend SQLite schema with readiness review tables
- add repository save/list/bundle/summary helpers
- add latest-lookups for readiness context

## 4. Phase C/D - Service and APIs
- add read-only activation-readiness review service
- add read-only activation-readiness review endpoints
- ensure responses carry safety flags
- preserve no-execution boundary

## 5. Phase E/F - UI and Verification
- add dashboard shell activation-readiness panel
- expose summary, recent rows, and bundle lookup
- add acceptance tests
- add freeze docs

## 6. Safety Rules
- no strategy
- no simulation
- no execution
- no promotion
- no trading
- no wallet
- no order placement
- no order cancellation

## 7. Next Action
Start with PWB-10 Phase A/B after the charter is accepted.
