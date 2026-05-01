# PWB-09 Backlog

## 1. Round Summary
PWB-09 is a read-only governed approval-window review round.

It follows the accepted execution-queue review baseline and exposes approval-window context without changing runtime behavior.

## 2. Deliverables
- approval-window review models
- SQLite tables and indexes
- repository methods
- read-only approval-window review service
- read-only approval-window review APIs
- dashboard shell visibility
- acceptance tests
- freeze docs

## 3. Phase A/B - Models and Storage
- define approval-window review models and enums
- extend SQLite schema with approval review tables
- add repository save/list/bundle/summary helpers
- add latest-lookups for approval context

## 4. Phase C/D - Service and APIs
- add read-only approval-window review service
- add read-only approval-window review endpoints
- ensure responses carry safety flags
- preserve no-execution boundary

## 5. Phase E/F - UI and Verification
- add dashboard shell approval-window panel
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
Start with PWB-09 Phase A/B after the charter is accepted.
