# PWB-07 Backlog

## 1. Round Summary
PWB-07 is a read-only governed execution-decision review round.

It follows the accepted command-review baseline and exposes execution-decision context without changing runtime behavior.

## 2. Deliverables
- execution-decision review models
- SQLite tables and indexes
- repository methods
- read-only execution-decision review service
- read-only execution-decision review APIs
- dashboard shell visibility
- acceptance tests
- freeze docs

## 3. Phase A/B - Models and Storage
- define execution-decision review models and enums
- extend SQLite schema with decision review tables
- add repository save/list/bundle/summary helpers
- add latest-lookups for review context

## 4. Phase C/D - Service and APIs
- add read-only execution-decision review service
- add read-only execution-decision review endpoints
- ensure responses carry safety flags
- preserve no-execution boundary

## 5. Phase E/F - UI and Verification
- add dashboard shell execution-decision panel
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
Start with PWB-07 Phase A/B after the charter is accepted.
