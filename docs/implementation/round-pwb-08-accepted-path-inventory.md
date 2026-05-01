# Round_PWB-08_Accepted_Path_Inventory
## 1. Purpose
This document freezes the accepted files and implementation paths for Round PWB-08 — Governed Execution Queue Review v0.

## 2. Accepted Backend Model Files

`backend/models/execution_queue_review.py`

Accepted objects:

- `ExecutionQueueReviewRecord`
- `ExecutionQueueReviewSummary`
- `ExecutionQueueReviewBundle`

Accepted enums:

- `ExecutionQueueReviewStatus`
- `ExecutionQueueApprovalStatus`
- `ExecutionQueueGateStatus`
- `ExecutionQueueReviewRecommendation`

## 3. Accepted Storage Extensions

Accepted table:

- `execution_queue_review_records`

Accepted indexes:

- `idx_execution_queue_review_records_market_id`
- `idx_execution_queue_review_records_reviewed_at`
- `idx_execution_queue_review_records_review_status`
- `idx_execution_queue_review_records_approval_status`
- `idx_execution_queue_review_records_gate_status`
- `idx_execution_queue_review_records_execution_status`
- `idx_execution_queue_review_records_decision_id`
- `idx_execution_queue_review_records_candidate_id`

## 4. Accepted Repository Methods

Accepted repository methods:

- `save_execution_queue_review_record`
- `list_execution_queue_review_records`
- `get_latest_execution_queue_review_for_market`
- `get_execution_queue_review_bundle`
- `get_execution_queue_review_summary`
- `get_execution_decision_review_by_id`
- `list_distinct_market_ids_for_execution_queue_review`

## 5. Accepted Service

Accepted file:

- `backend/execution_queue_review/execution_queue_review_service.py`

Accepted class:

- `ExecutionQueueReviewService`

Accepted methods:

- `build_for_market`
- `build_all_eligible`
- `list_reviews`
- `get_market_bundle`
- `get_summary`

## 6. Accepted API Surface

Accepted file:

- `backend/api/routes_execution_queue_review.py`

Accepted endpoints:

- `GET /api/execution-queue-review/summary`
- `GET /api/execution-queue-review/reviews`
- `GET /api/execution-queue-review/market/{market_id}`
- `POST /api/execution-queue-review/build`
- `POST /api/execution-queue-review/build-all`

## 7. Accepted Dashboard Files

Accepted dashboard panel:

- `weather-dashboard/src/weather_dashboard/ui/execution_queue_review_panel.py`

Accepted page integration:

- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## 8. Accepted Tests

Accepted tests include:

- execution-queue review model serialization
- table creation
- repository save/list/bundle/summary
- latest execution decision lookup for queue context
- service smoke
- API smoke
- dashboard panel smoke

## 9. Inventory Status

PWB-08 accepted path inventory is complete.
