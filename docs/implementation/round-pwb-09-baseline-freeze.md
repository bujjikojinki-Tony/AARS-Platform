# Round_PWB-09_Baseline_Freeze
## 1. Freeze Decision
Round PWB-09 — Governed Approval Window Review v0 is frozen.

Status:

ACCEPTED BASELINE

## 2. Freeze Scope

The accepted baseline includes:

- Approval-window review models
- Approval-window review SQLite table
- Approval-window review indexes
- Approval-window review repository methods
- ApprovalWindowReviewService
- Approval-window review APIs
- Approval-window review dashboard panel
- PWB-09 acceptance tests

## 3. Stable Architecture

Accepted PWB-09 architecture:

ExecutionDecision
→ CommandReview
→ ExecutionDecisionReview
→ ExecutionQueueReview
→ ApprovalWindowReviewRecord

## 4. Stable API Boundary

Accepted APIs:

- `GET /api/approval-window-review/summary`
- `GET /api/approval-window-review/reviews`
- `GET /api/approval-window-review/market/{market_id}`
- `POST /api/approval-window-review/build`
- `POST /api/approval-window-review/build-all`

Accepted API boundary:

Approval-window review APIs may save and read review records.
Approval-window review APIs must not generate strategy signals.
Approval-window review APIs must not generate opportunity candidates.
Approval-window review APIs must not simulate.
Approval-window review APIs must not execute.
Approval-window review APIs must not trade.

## 5. Stable Safety Boundary

The following remain frozen:

LIVE_EXECUTE remains rejected.
No wallet.
No private key.
No signing.
No order placement.
No order cancellation.
No auto trading.
No live execution.

PWB-09 additionally freezes:

Review is passive.
Review must not drive action.

## 6. Baseline Acceptance Criteria

PWB-09 baseline is accepted if:

1. ApprovalWindowReviewRecord serializes.
2. approval_window_review_records table exists.
3. repository can save and query approval-window review records.
4. approval-window review summary returns expected counts.
5. approval-window review bundle can be queried by market.
6. approval-window review service can build records.
7. approval-window review APIs work.
8. dashboard shell can view approval-window review data.
9. LIVE_EXECUTE remains rejected.

## 7. No Further Expansion Rule

After this freeze:

Do not add execution or trading logic to PWB-09.
Do not add wallet, signing, order, or cancel logic to PWB-09.
Do not add calibration or promotion logic to PWB-09.
