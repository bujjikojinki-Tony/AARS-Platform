# PWB-06 Backlog

## 1. Round Summary
PWB-06 is a read-only governed command review round.

It follows the accepted shadow-evaluation chain and exposes advisory command context without changing runtime behavior.

## 2. Deliverables
- command review models
- SQLite tables and indexes
- repository methods
- read-only command review service
- read-only command review APIs
- dashboard shell visibility
- acceptance tests
- freeze docs

## 3. Phase A/B - Models and Storage
- define command review models and enums
- extend SQLite schema with review tables
- add repository save/list/bundle/summary helpers
- add latest-lookups if needed for review context

## 4. Phase C/D - Service and APIs
- add read-only command review service
- add read-only command review endpoints
- ensure responses carry safety flags
- preserve no-execution boundary

## 5. Phase E/F - UI and Verification
- add dashboard shell command review panel
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
Start with PWB-06 Phase A/B after the charter is accepted.
