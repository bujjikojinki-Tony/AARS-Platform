# Round_PWB-10_Accepted_Path_Inventory
## 1. Purpose
This document freezes the accepted files and implementation paths for Round PWB-10 — Governed Activation Readiness Review v0.

## 2. Accepted Backend Model Files

`backend/models/activation_readiness_review.py`

Accepted objects:

- `ActivationReadinessReviewRecord`
- `ActivationReadinessReviewSummary`
- `ActivationReadinessReviewBundle`

Accepted enums:

- `ActivationReadinessReviewStatus`
- `ActivationReadinessRecommendation`

## 3. Accepted Storage Extensions

Accepted table:

- `activation_readiness_review_records`

Accepted indexes:

- `idx_activation_readiness_review_records_market_id`
- `idx_activation_readiness_review_records_reviewed_at`
- `idx_activation_readiness_review_records_readiness_status`
- `idx_activation_readiness_review_records_recommendation`
- `idx_activation_readiness_review_records_approval_status`
- `idx_activation_readiness_review_records_decision_id`
- `idx_activation_readiness_review_records_candidate_id`

## 4. Accepted Repository Methods

Accepted repository methods:

- `save_activation_readiness_review_record`
- `list_activation_readiness_review_records`
- `get_latest_activation_readiness_review_for_market`
- `get_activation_readiness_review_by_id`
- `get_activation_readiness_review_bundle`
- `get_activation_readiness_review_summary`
- `list_distinct_market_ids_for_activation_readiness_review`

## 5. Accepted Service

Accepted file:

- `backend/activation_readiness_review/activation_readiness_review_service.py`

Accepted class:

- `ActivationReadinessReviewService`

Accepted methods:

- `build_for_market`
- `build_all_eligible`
- `list_reviews`
- `get_market_bundle`
- `get_summary`

## 6. Accepted API Surface

Accepted file:

- `backend/api/routes_activation_readiness_review.py`

Accepted endpoints:

- `GET /api/activation-readiness-review/summary`
- `GET /api/activation-readiness-review/reviews`
- `GET /api/activation-readiness-review/market/{market_id}`
- `POST /api/activation-readiness-review/build`
- `POST /api/activation-readiness-review/build-all`

## 7. Accepted Dashboard Files

Accepted dashboard panel:

- `weather-dashboard/src/weather_dashboard/ui/activation_readiness_review_panel.py`

Accepted page integration:

- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## 8. Accepted Tests

Accepted tests include:

- activation-readiness review model serialization
- table creation
- repository save/list/bundle/summary
- service smoke
- API smoke
- dashboard panel smoke

## 9. Inventory Status

PWB-10 accepted path inventory is complete.
