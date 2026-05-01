# PWB-08 Backlog

## 1. Round Summary
PWB-08 is a read-only governed execution queue review round.

It follows the accepted execution-decision review baseline and exposes queue context without changing runtime behavior.

## 2. Deliverables
- execution queue review models
- SQLite tables and indexes
- repository methods
- read-only execution queue review service
- read-only execution queue review APIs
- dashboard shell visibility
- acceptance tests
- freeze docs

## 3. Phase A/B - Models and Storage
- define execution queue review models and enums
- extend SQLite schema with queue review tables
- add repository save/list/bundle/summary helpers
- add latest-lookups for queue context

## 4. Phase C/D - Service and APIs
- add read-only execution queue review service
- add read-only execution queue review endpoints
- ensure responses carry safety flags
- preserve no-execution boundary

## 5. Phase E/F - UI and Verification
- add dashboard shell execution queue panel
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
Start with PWB-08 Phase A/B after the charter is accepted.
