# Round_PWB-07_Accepted_Path_Inventory
## 1. Purpose
This document freezes the accepted files and implementation paths for Round PWB-07 — Governed Execution Decision Review v0.

## 2. Accepted Backend Model Files

`backend/models/execution_decision_review.py`

Accepted objects:

- `ExecutionDecisionReviewRecord`
- `ExecutionDecisionReviewSummary`
- `ExecutionDecisionReviewBundle`

Accepted enums:

- `ExecutionDecisionReviewStatus`
- `ExecutionApprovalStatus`
- `ExecutionGateStatus`
- `ExecutionDecisionReviewRecommendation`

## 3. Accepted Storage Extensions

Accepted table:

- `execution_decision_review_records`

Accepted indexes:

- `idx_execution_decision_review_market_id`
- `idx_execution_decision_review_reviewed_at`
- `idx_execution_decision_review_review_status`
- `idx_execution_decision_review_approval_status`
- `idx_execution_decision_review_gate_status`
- `idx_execution_decision_review_execution_status`
- `idx_execution_decision_review_decision_id`
- `idx_execution_decision_review_candidate_id`

## 4. Accepted Repository Methods

Accepted repository methods:

- `save_execution_decision_review_record`
- `list_execution_decision_review_records`
- `get_latest_execution_decision_review_for_market`
- `get_execution_decision_review_bundle`
- `get_execution_decision_review_summary`
- `get_latest_execution_decision_for_market`

## 5. Accepted Service

Accepted file:

- `backend/execution_decision_review/execution_decision_review_service.py`

Accepted class:

- `ExecutionDecisionReviewService`

Accepted methods:

- `build_for_market`
- `build_all_eligible`
- `list_reviews`
- `get_market_bundle`
- `get_summary`

## 6. Accepted API Surface

Accepted file:

- `backend/api/routes_execution_decision_review.py`

Accepted endpoints:

- `GET /api/execution-decision-review/summary`
- `GET /api/execution-decision-review/reviews`
- `GET /api/execution-decision-review/market/{market_id}`
- `POST /api/execution-decision-review/build`
- `POST /api/execution-decision-review/build-all`

## 7. Accepted Dashboard Files

Accepted dashboard panel:

- `weather-dashboard/src/weather_dashboard/ui/execution_decision_review_panel.py`

Accepted page integration:

- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## 8. Accepted Tests

Accepted tests include:

- execution-decision review model serialization
- table creation
- repository save/list/bundle/summary
- latest execution-decision lookup
- service smoke
- API smoke
- dashboard panel smoke

## 9. Inventory Status

PWB-07 accepted path inventory is complete.
