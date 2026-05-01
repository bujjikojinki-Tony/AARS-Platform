# Round_PWB-09_Accepted_Path_Inventory
## 1. Purpose
This document freezes the accepted files and implementation paths for Round PWB-09 — Governed Approval Window Review v0.

## 2. Accepted Backend Model Files

`backend/models/approval_window_review.py`

Accepted objects:

- `ApprovalWindowReviewRecord`
- `ApprovalWindowReviewSummary`
- `ApprovalWindowReviewBundle`

Accepted enums:

- `ApprovalWindowReviewStatus`
- `ApprovalWindowState`
- `ApprovalWindowRecommendation`

## 3. Accepted Storage Extensions

Accepted table:

- `approval_window_review_records`

Accepted indexes:

- `idx_approval_window_review_records_market_id`
- `idx_approval_window_review_records_reviewed_at`
- `idx_approval_window_review_records_review_status`
- `idx_approval_window_review_records_window_state`
- `idx_approval_window_review_records_approval_status`
- `idx_approval_window_review_records_decision_id`
- `idx_approval_window_review_records_candidate_id`

## 4. Accepted Repository Methods

Accepted repository methods:

- `save_approval_window_review_record`
- `list_approval_window_review_records`
- `get_latest_approval_window_review_for_market`
- `get_approval_window_review_by_id`
- `get_approval_window_review_bundle`
- `get_approval_window_review_summary`
- `list_distinct_market_ids_for_approval_window_review`

## 5. Accepted Service

Accepted file:

- `backend/approval_window_review/approval_window_review_service.py`

Accepted class:

- `ApprovalWindowReviewService`

Accepted methods:

- `build_for_market`
- `build_all_eligible`
- `list_reviews`
- `get_market_bundle`
- `get_summary`

## 6. Accepted API Surface

Accepted file:

- `backend/api/routes_approval_window_review.py`

Accepted endpoints:

- `GET /api/approval-window-review/summary`
- `GET /api/approval-window-review/reviews`
- `GET /api/approval-window-review/market/{market_id}`
- `POST /api/approval-window-review/build`
- `POST /api/approval-window-review/build-all`

## 7. Accepted Dashboard Files

Accepted dashboard panel:

- `weather-dashboard/src/weather_dashboard/ui/approval_window_review_panel.py`

Accepted page integration:

- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## 8. Accepted Tests

Accepted tests include:

- approval-window review model serialization
- table creation
- repository save/list/bundle/summary
- service smoke
- API smoke
- dashboard panel smoke

## 9. Inventory Status

PWB-09 accepted path inventory is complete.
