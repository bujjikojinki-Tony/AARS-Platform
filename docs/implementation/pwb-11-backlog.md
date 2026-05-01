# PWB-11 Backlog

## 1. Round Summary
PWB-11 is a read-only governed activation-authorization review round.

It follows the accepted activation-readiness review baseline and exposes activation-authorization context without changing runtime behavior.

## 2. Deliverables
- activation-authorization review models
- SQLite tables and indexes
- repository methods
- read-only activation-authorization review service
- read-only activation-authorization review APIs
- dashboard shell visibility
- acceptance tests
- freeze docs

## 3. Phase A/B - Models and Storage
- define activation-authorization review models and enums
- extend SQLite schema with authorization review tables
- add repository save/list/bundle/summary helpers
- add latest-lookups for authorization context

## 4. Phase C/D - Service and APIs
- add read-only activation-authorization review service
- add read-only activation-authorization review endpoints
- ensure responses carry safety flags
- preserve no-execution boundary

## 5. Phase E/F - UI and Verification
- add dashboard shell activation-authorization panel
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
Start with PWB-11 Phase A/B after the charter is accepted.
