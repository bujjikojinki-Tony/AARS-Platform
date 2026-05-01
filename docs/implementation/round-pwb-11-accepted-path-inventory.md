# Round_PWB-11_Accepted_Path_Inventory
## 1. Purpose
This document freezes the accepted files and implementation paths for Round PWB-11 — Governed Activation Authorization Review v0.

## 2. Accepted Backend Model Files

`backend/models/activation_authorization_review.py`

Accepted objects:

- `ActivationAuthorizationReviewRecord`
- `ActivationAuthorizationReviewSummary`
- `ActivationAuthorizationReviewBundle`

Accepted enums:

- `ActivationAuthorizationReviewStatus`
- `ActivationAuthorizationRecommendation`

## 3. Accepted Storage Extensions

Accepted table:

- `activation_authorization_review_records`

Accepted indexes:

- `idx_activation_authorization_review_records_market_id`
- `idx_activation_authorization_review_records_reviewed_at`
- `idx_activation_authorization_review_records_authorization_status`
- `idx_activation_authorization_review_records_recommendation`
- `idx_activation_authorization_review_records_approval_status`
- `idx_activation_authorization_review_records_decision_id`
- `idx_activation_authorization_review_records_candidate_id`

## 4. Accepted Repository Methods

Accepted repository methods:

- `save_activation_authorization_review_record`
- `list_activation_authorization_review_records`
- `get_latest_activation_authorization_review_for_market`
- `get_activation_authorization_review_by_id`
- `get_activation_authorization_review_bundle`
- `get_activation_authorization_review_summary`
- `list_distinct_market_ids_for_activation_authorization_review`

## 5. Accepted Service

Accepted file:

- `backend/activation_authorization_review/activation_authorization_review_service.py`

Accepted class:

- `ActivationAuthorizationReviewService`

Accepted methods:

- `build_for_market`
- `build_all_eligible`
- `list_reviews`
- `get_market_bundle`
- `get_summary`

## 6. Accepted API Surface

Accepted file:

- `backend/api/routes_activation_authorization_review.py`

Accepted endpoints:

- `GET /api/activation-authorization-review/summary`
- `GET /api/activation-authorization-review/reviews`
- `GET /api/activation-authorization-review/market/{market_id}`
- `POST /api/activation-authorization-review/build`
- `POST /api/activation-authorization-review/build-all`

## 7. Accepted Dashboard Files

Accepted dashboard panel:

- `weather-dashboard/src/weather_dashboard/ui/activation_authorization_review_panel.py`

Accepted page integration:

- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## 8. Accepted Tests

Accepted tests include:

- activation-authorization review model serialization
- table creation
- repository save/list/bundle/summary
- service smoke
- API smoke
- dashboard panel smoke

## 9. Inventory Status

PWB-11 accepted path inventory is complete.
