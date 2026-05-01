from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


DEFAULT_DB_PATH = "pwb01.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market_id TEXT NOT NULL,
  question TEXT NOT NULL,
  yes_price REAL NOT NULL,
  no_price REAL NOT NULL,
  liquidity REAL NOT NULL,
  spread REAL NOT NULL,
  source TEXT NOT NULL,
  fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS strategy_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  signal_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  strategy_id TEXT NOT NULL,
  side TEXT NOT NULL,
  model_probability REAL NOT NULL,
  market_probability REAL NOT NULL,
  edge_percent REAL NOT NULL,
  z_score REAL,
  confidence TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opportunity_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id TEXT NOT NULL,
  signal_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  question TEXT NOT NULL,
  side TEXT NOT NULL,
  market_probability REAL NOT NULL,
  model_probability REAL NOT NULL,
  edge_percent REAL NOT NULL,
  z_score REAL,
  liquidity REAL NOT NULL,
  spread REAL NOT NULL,
  confidence_tier TEXT,
  risk_status TEXT,
  action_status TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS execution_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  action TEXT NOT NULL,
  position_size REAL,
  expected_cost REAL,
  risk_status TEXT,
  execution_status TEXT,
  created_at TEXT NOT NULL,
  executed_at TEXT
);
CREATE TABLE IF NOT EXISTS simulation_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  simulation_id TEXT NOT NULL,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  side TEXT NOT NULL,
  entry_price REAL NOT NULL,
  position_size REAL NOT NULL,
  simulated_cost REAL NOT NULL,
  expected_probability REAL,
  expected_value REAL,
  max_loss REAL,
  max_gain REAL,
  result_status TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rule_configs (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS system_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""

WEATHER_SCHEMA = """
CREATE TABLE IF NOT EXISTS weather_descriptors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market_id TEXT NOT NULL,
  question TEXT NOT NULL,
  city TEXT,
  region TEXT,
  country TEXT,
  target_date TEXT,
  metric TEXT,
  threshold REAL,
  upper_threshold REAL,
  unit TEXT,
  direction TEXT,
  confidence TEXT,
  parse_warnings_json TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weather_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  city TEXT NOT NULL,
  target_date TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  valid_time TEXT,
  raw_payload_json TEXT,
  normalized_value REAL,
  unit TEXT,
  freshness_status TEXT,
  trust_level TEXT
);
CREATE TABLE IF NOT EXISTS evidence_packs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_pack_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  descriptor_json TEXT NOT NULL,
  sources_json TEXT NOT NULL,
  evidence_freshness TEXT,
  evidence_conflict_level TEXT,
  raw_refs_json TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weather_views (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  weather_view_id TEXT NOT NULL,
  evidence_pack_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  city TEXT NOT NULL,
  target_date TEXT NOT NULL,
  expected_value REAL NOT NULL,
  expected_range_low REAL NOT NULL,
  expected_range_high REAL NOT NULL,
  sigma REAL NOT NULL,
  threshold REAL,
  direction TEXT,
  unit TEXT,
  confidence TEXT,
  evidence_summary_json TEXT,
  invalidation_rules_json TEXT,
  confirmation_rules_json TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS probability_views (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  probability_view_id TEXT NOT NULL,
  weather_view_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  engine_id TEXT NOT NULL,
  model_probability REAL NOT NULL,
  threshold REAL,
  expected_value REAL NOT NULL,
  sigma REAL NOT NULL,
  direction TEXT,
  confidence TEXT,
  warnings_json TEXT,
  created_at TEXT NOT NULL
);
"""

PROBABILITY_GOVERNANCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS probability_engine_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  engine_id TEXT NOT NULL UNIQUE,
  engine_name TEXT NOT NULL,
  engine_type TEXT NOT NULL,
  version TEXT NOT NULL,
  enabled INTEGER NOT NULL,
  can_be_primary INTEGER NOT NULL,
  description TEXT,
  default_params_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS probability_engine_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  weather_view_id TEXT NOT NULL,
  engine_id TEXT NOT NULL,
  engine_type TEXT NOT NULL,
  model_probability REAL NOT NULL,
  expected_value REAL,
  sigma REAL,
  threshold REAL,
  direction TEXT,
  params_json TEXT,
  warnings_json TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS probability_comparisons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  comparison_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  weather_view_id TEXT NOT NULL,
  active_engine_id TEXT NOT NULL,
  active_probability REAL NOT NULL,
  engine_runs_json TEXT NOT NULL,
  spread_between_engines REAL NOT NULL,
  disagreement_level TEXT NOT NULL,
  selection_reason TEXT,
  warnings_json TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS market_outcomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  outcome_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  resolved_value REAL,
  resolved_direction_hit INTEGER,
  official_source TEXT,
  resolved_at TEXT NOT NULL,
  status TEXT NOT NULL,
  notes TEXT
);
CREATE TABLE IF NOT EXISTS calibration_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  calibration_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  engine_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  outcome_id TEXT NOT NULL,
  predicted_probability REAL NOT NULL,
  actual_outcome INTEGER NOT NULL,
  brier_score REAL NOT NULL,
  absolute_error REAL NOT NULL,
  bucket TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS engine_promotion_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  decision_id TEXT NOT NULL,
  engine_id TEXT NOT NULL,
  current_type TEXT NOT NULL,
  proposed_type TEXT NOT NULL,
  eligible INTEGER NOT NULL,
  decision TEXT NOT NULL,
  evidence_count INTEGER NOT NULL,
  avg_brier_score REAL,
  avg_absolute_error REAL,
  reason TEXT,
  created_at TEXT NOT NULL
);
"""

POLYMARKET_CONNECTOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS polymarket_market_cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  polymarket_market_id TEXT NOT NULL,
  condition_id TEXT,
  question TEXT NOT NULL,
  slug TEXT,
  category TEXT,
  active INTEGER,
  closed INTEGER,
  archived INTEGER,
  end_date TEXT,
  resolution_source TEXT,
  outcomes_json TEXT,
  outcome_prices_json TEXT,
  clob_token_ids_json TEXT,
  liquidity REAL,
  volume REAL,
  raw_payload_json TEXT,
  fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS polymarket_connector_health (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connector_id TEXT NOT NULL,
  gamma_reachable INTEGER,
  clob_reachable INTEGER,
  last_gamma_status INTEGER,
  last_clob_status INTEGER,
  mode TEXT NOT NULL,
  warnings_json TEXT,
  last_checked_at TEXT NOT NULL
);
"""

SNAPSHOT_ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_snapshot_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  source TEXT NOT NULL,
  question TEXT NOT NULL,
  yes_price REAL NOT NULL,
  no_price REAL NOT NULL,
  liquidity REAL NOT NULL,
  spread REAL NOT NULL,
  fetched_at TEXT,
  archived_at TEXT NOT NULL,
  market_source_mode TEXT NOT NULL,
  raw_ref TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_archive_market_id
ON market_snapshot_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_archive_archived_at
ON market_snapshot_archive(archived_at);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_archive_source
ON market_snapshot_archive(source);
"""

WEATHER_ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS weather_forecast_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  forecast_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  weather_view_id TEXT,
  evidence_pack_id TEXT,
  city TEXT,
  target_date TEXT,
  source_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  metric TEXT NOT NULL,
  unit TEXT NOT NULL,
  expected_value REAL,
  expected_range_low REAL,
  expected_range_high REAL,
  sigma REAL,
  fetched_at TEXT,
  archived_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weather_evidence_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  evidence_pack_id TEXT NOT NULL,
  source_ids_json TEXT,
  evidence_summary_json TEXT,
  invalidation_rules_json TEXT,
  confirmation_rules_json TEXT,
  archived_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weather_view_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  weather_view_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  weather_view_id TEXT NOT NULL,
  evidence_pack_id TEXT,
  city TEXT,
  target_date TEXT,
  expected_value REAL,
  expected_range_low REAL,
  expected_range_high REAL,
  sigma REAL,
  threshold REAL,
  direction TEXT NOT NULL,
  unit TEXT NOT NULL,
  confidence TEXT NOT NULL,
  archived_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_archive_market_id
ON weather_forecast_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_archive_weather_view_id
ON weather_forecast_archive(weather_view_id);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_archive_archived_at
ON weather_forecast_archive(archived_at);
CREATE INDEX IF NOT EXISTS idx_weather_evidence_archive_market_id
ON weather_evidence_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_evidence_archive_evidence_pack_id
ON weather_evidence_archive(evidence_pack_id);
CREATE INDEX IF NOT EXISTS idx_weather_view_archive_market_id
ON weather_view_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_view_archive_weather_view_id
ON weather_view_archive(weather_view_id);
"""

OUTCOME_ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_outcome_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market_outcome_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  question TEXT,
  source TEXT NOT NULL,
  resolved_outcome TEXT NOT NULL,
  resolution_status TEXT NOT NULL,
  resolved_value REAL,
  resolved_at TEXT NOT NULL,
  notes TEXT,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE TABLE IF NOT EXISTS weather_actual_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  weather_actual_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  city TEXT,
  target_date TEXT,
  source TEXT NOT NULL,
  metric TEXT NOT NULL,
  unit TEXT NOT NULL,
  actual_value REAL,
  observed_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE TABLE IF NOT EXISTS outcome_resolution_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  outcome_resolution_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  market_outcome_id TEXT,
  weather_actual_id TEXT,
  weather_view_id TEXT,
  threshold REAL,
  direction TEXT NOT NULL,
  actual_value REAL,
  resolved_outcome TEXT NOT NULL,
  resolution_status TEXT NOT NULL,
  resolution_source TEXT NOT NULL,
  resolved_at TEXT NOT NULL,
  notes TEXT,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_market_outcome_records_market_id
ON market_outcome_records(market_id);
CREATE INDEX IF NOT EXISTS idx_market_outcome_records_status
ON market_outcome_records(resolution_status);
CREATE INDEX IF NOT EXISTS idx_market_outcome_records_resolved_at
ON market_outcome_records(resolved_at);
CREATE INDEX IF NOT EXISTS idx_weather_actual_records_market_id
ON weather_actual_records(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_actual_records_observed_at
ON weather_actual_records(observed_at);
CREATE INDEX IF NOT EXISTS idx_weather_actual_records_metric
ON weather_actual_records(metric);
CREATE INDEX IF NOT EXISTS idx_outcome_resolution_records_market_id
ON outcome_resolution_records(market_id);
CREATE INDEX IF NOT EXISTS idx_outcome_resolution_records_status
ON outcome_resolution_records(resolution_status);
CREATE INDEX IF NOT EXISTS idx_outcome_resolution_records_resolved_at
ON outcome_resolution_records(resolved_at);
CREATE INDEX IF NOT EXISTS idx_outcome_resolution_records_weather_actual_id
ON outcome_resolution_records(weather_actual_id);
"""

CALIBRATION_MEMORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS calibration_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  calibration_sample_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  snapshot_archive_id TEXT,
  weather_view_archive_id TEXT,
  weather_forecast_archive_id TEXT,
  probability_run_id TEXT,
  outcome_resolution_id TEXT,
  engine_id TEXT,
  market_probability REAL,
  model_probability REAL,
  actual_outcome_value REAL,
  model_brier_score REAL,
  market_brier_score REAL,
  model_absolute_error REAL,
  market_absolute_error REAL,
  model_beats_market INTEGER,
  resolved_outcome TEXT NOT NULL,
  sample_eligibility TEXT NOT NULL,
  sample_status TEXT NOT NULL,
  sampled_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE TABLE IF NOT EXISTS backtest_memory_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  backtest_memory_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  snapshot_archive_id TEXT,
  weather_view_archive_id TEXT,
  weather_forecast_archive_id TEXT,
  probability_run_id TEXT,
  outcome_resolution_id TEXT,
  engine_id TEXT,
  market_probability REAL,
  model_probability REAL,
  actual_outcome_value REAL,
  edge REAL,
  edge_threshold REAL,
  hypothetical_action TEXT NOT NULL,
  hypothetical_result TEXT NOT NULL,
  sample_eligibility TEXT NOT NULL,
  backtest_status TEXT NOT NULL,
  sampled_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_calibration_samples_market_id
ON calibration_samples(market_id);
CREATE INDEX IF NOT EXISTS idx_calibration_samples_engine_id
ON calibration_samples(engine_id);
CREATE INDEX IF NOT EXISTS idx_calibration_samples_status
ON calibration_samples(sample_status);
CREATE INDEX IF NOT EXISTS idx_calibration_samples_eligibility
ON calibration_samples(sample_eligibility);
CREATE INDEX IF NOT EXISTS idx_calibration_samples_sampled_at
ON calibration_samples(sampled_at);
CREATE INDEX IF NOT EXISTS idx_backtest_memory_records_market_id
ON backtest_memory_records(market_id);
CREATE INDEX IF NOT EXISTS idx_backtest_memory_records_engine_id
ON backtest_memory_records(engine_id);
CREATE INDEX IF NOT EXISTS idx_backtest_memory_records_status
ON backtest_memory_records(backtest_status);
CREATE INDEX IF NOT EXISTS idx_backtest_memory_records_action
ON backtest_memory_records(hypothetical_action);
CREATE INDEX IF NOT EXISTS idx_backtest_memory_records_eligibility
ON backtest_memory_records(sample_eligibility);
CREATE INDEX IF NOT EXISTS idx_backtest_memory_records_sampled_at
ON backtest_memory_records(sampled_at);
"""

DEB_SHADOW_SCHEMA = """
CREATE TABLE IF NOT EXISTS deb_shadow_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  deb_shadow_run_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  calibration_sample_id TEXT,
  engine_id TEXT NOT NULL,
  base_probability REAL,
  deb_probability REAL,
  bias_adjustment REAL,
  calibration_gap REAL,
  sample_count INTEGER NOT NULL,
  run_status TEXT NOT NULL,
  warnings_json TEXT,
  created_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE TABLE IF NOT EXISTS deb_shadow_diagnostics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  deb_shadow_diagnostic_id TEXT NOT NULL,
  deb_shadow_run_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  calibration_sample_id TEXT,
  sample_count INTEGER NOT NULL,
  avg_model_brier_score REAL,
  avg_market_brier_score REAL,
  avg_model_edge REAL,
  avg_probability_error REAL,
  adjustment_weight REAL,
  notes TEXT,
  created_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_runs_market_id
ON deb_shadow_runs(market_id);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_runs_engine_id
ON deb_shadow_runs(engine_id);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_runs_status
ON deb_shadow_runs(run_status);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_runs_created_at
ON deb_shadow_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_runs_calibration_sample_id
ON deb_shadow_runs(calibration_sample_id);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_diagnostics_market_id
ON deb_shadow_diagnostics(market_id);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_diagnostics_run_id
ON deb_shadow_diagnostics(deb_shadow_run_id);
CREATE INDEX IF NOT EXISTS idx_deb_shadow_diagnostics_created_at
ON deb_shadow_diagnostics(created_at);
"""

EMOS_SHADOW_SCHEMA = """
CREATE TABLE IF NOT EXISTS emos_shadow_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  emos_shadow_run_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  calibration_sample_id TEXT,
  engine_id TEXT NOT NULL,
  base_probability REAL,
  emos_probability REAL,
  location_adjustment REAL,
  scale_adjustment REAL,
  sample_count INTEGER NOT NULL,
  run_status TEXT NOT NULL,
  warnings_json TEXT,
  created_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE TABLE IF NOT EXISTS emos_shadow_diagnostics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  emos_shadow_diagnostic_id TEXT NOT NULL,
  emos_shadow_run_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  calibration_sample_id TEXT,
  sample_count INTEGER NOT NULL,
  avg_model_brier_score REAL,
  avg_market_brier_score REAL,
  avg_probability_error REAL,
  avg_absolute_error REAL,
  location_weight REAL,
  scale_weight REAL,
  notes TEXT,
  created_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_runs_market_id
ON emos_shadow_runs(market_id);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_runs_engine_id
ON emos_shadow_runs(engine_id);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_runs_status
ON emos_shadow_runs(run_status);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_runs_created_at
ON emos_shadow_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_runs_calibration_sample_id
ON emos_shadow_runs(calibration_sample_id);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_diagnostics_market_id
ON emos_shadow_diagnostics(market_id);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_diagnostics_run_id
ON emos_shadow_diagnostics(emos_shadow_run_id);
CREATE INDEX IF NOT EXISTS idx_emos_shadow_diagnostics_created_at
ON emos_shadow_diagnostics(created_at);
"""

SHADOW_ENGINE_EVALUATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS shadow_engine_evaluations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  shadow_evaluation_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  calibration_sample_id TEXT,
  outcome_resolution_id TEXT,
  primary_engine_id TEXT NOT NULL,
  deb_engine_id TEXT NOT NULL,
  emos_engine_id TEXT NOT NULL,
  primary_probability REAL,
  deb_probability REAL,
  emos_probability REAL,
  actual_outcome_value REAL,
  primary_brier_score REAL,
  deb_brier_score REAL,
  emos_brier_score REAL,
  primary_absolute_error REAL,
  deb_absolute_error REAL,
  emos_absolute_error REAL,
  best_engine TEXT NOT NULL,
  evaluation_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_shadow_engine_evaluations_market_id
ON shadow_engine_evaluations(market_id);
CREATE INDEX IF NOT EXISTS idx_shadow_engine_evaluations_status
ON shadow_engine_evaluations(evaluation_status);
CREATE INDEX IF NOT EXISTS idx_shadow_engine_evaluations_best_engine
ON shadow_engine_evaluations(best_engine);
CREATE INDEX IF NOT EXISTS idx_shadow_engine_evaluations_created_at
ON shadow_engine_evaluations(created_at);
CREATE INDEX IF NOT EXISTS idx_shadow_engine_evaluations_calibration_sample_id
ON shadow_engine_evaluations(calibration_sample_id);
"""

COMMAND_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS command_review_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  command_review_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  command_name TEXT NOT NULL,
  source_page TEXT NOT NULL,
  target_page TEXT,
  command_path TEXT,
  review_status TEXT NOT NULL,
  approval_status TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  gate_status TEXT NOT NULL,
  active_engine_id TEXT,
  execution_mode TEXT,
  risk_status TEXT,
  approval_window_valid INTEGER,
  approval_valid_until TEXT,
  market_snapshot_archive_id TEXT,
  weather_view_archive_id TEXT,
  weather_forecast_archive_id TEXT,
  probability_run_id TEXT,
  outcome_resolution_id TEXT,
  calibration_sample_id TEXT,
  backtest_memory_id TEXT,
  deb_shadow_run_id TEXT,
  emos_shadow_run_id TEXT,
  shadow_evaluation_id TEXT,
  reviewed_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_command_review_records_market_id
ON command_review_records(market_id);
CREATE INDEX IF NOT EXISTS idx_command_review_records_reviewed_at
ON command_review_records(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_command_review_records_review_status
ON command_review_records(review_status);
CREATE INDEX IF NOT EXISTS idx_command_review_records_approval_status
ON command_review_records(approval_status);
CREATE INDEX IF NOT EXISTS idx_command_review_records_gate_status
ON command_review_records(gate_status);
CREATE INDEX IF NOT EXISTS idx_command_review_records_command_name
ON command_review_records(command_name);
"""

EXECUTION_DECISION_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_decision_review_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  execution_decision_review_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  command_review_id TEXT,
  shadow_evaluation_id TEXT,
  execution_mode TEXT,
  action TEXT,
  position_size REAL,
  expected_cost REAL,
  risk_status TEXT,
  execution_status TEXT,
  review_status TEXT NOT NULL,
  approval_status TEXT NOT NULL,
  gate_status TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  approval_window_valid INTEGER,
  approval_valid_until TEXT,
  reviewed_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_market_id
ON execution_decision_review_records(market_id);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_reviewed_at
ON execution_decision_review_records(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_review_status
ON execution_decision_review_records(review_status);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_approval_status
ON execution_decision_review_records(approval_status);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_gate_status
ON execution_decision_review_records(gate_status);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_execution_status
ON execution_decision_review_records(execution_status);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_decision_id
ON execution_decision_review_records(decision_id);
CREATE INDEX IF NOT EXISTS idx_execution_decision_review_records_candidate_id
ON execution_decision_review_records(candidate_id);
"""

EXECUTION_QUEUE_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_queue_review_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  execution_queue_review_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  command_review_id TEXT,
  execution_decision_review_id TEXT,
  shadow_evaluation_id TEXT,
  execution_mode TEXT,
  action TEXT,
  position_size REAL,
  expected_cost REAL,
  risk_status TEXT,
  execution_status TEXT,
  review_status TEXT NOT NULL,
  approval_status TEXT NOT NULL,
  gate_status TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  approval_window_valid INTEGER,
  approval_valid_until TEXT,
  reviewed_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_market_id
ON execution_queue_review_records(market_id);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_reviewed_at
ON execution_queue_review_records(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_review_status
ON execution_queue_review_records(review_status);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_approval_status
ON execution_queue_review_records(approval_status);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_gate_status
ON execution_queue_review_records(gate_status);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_execution_status
ON execution_queue_review_records(execution_status);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_decision_id
ON execution_queue_review_records(decision_id);
CREATE INDEX IF NOT EXISTS idx_execution_queue_review_records_candidate_id
ON execution_queue_review_records(candidate_id);
"""

APPROVAL_WINDOW_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS approval_window_review_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  approval_window_review_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  command_review_id TEXT,
  execution_decision_review_id TEXT,
  execution_queue_review_id TEXT,
  approval_status TEXT,
  approval_window_valid INTEGER,
  approval_valid_until TEXT,
  review_status TEXT NOT NULL,
  window_state TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  reviewed_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_approval_window_review_records_market_id
ON approval_window_review_records(market_id);
CREATE INDEX IF NOT EXISTS idx_approval_window_review_records_reviewed_at
ON approval_window_review_records(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_approval_window_review_records_review_status
ON approval_window_review_records(review_status);
CREATE INDEX IF NOT EXISTS idx_approval_window_review_records_window_state
ON approval_window_review_records(window_state);
CREATE INDEX IF NOT EXISTS idx_approval_window_review_records_approval_status
ON approval_window_review_records(approval_status);
CREATE INDEX IF NOT EXISTS idx_approval_window_review_records_decision_id
ON approval_window_review_records(decision_id);
CREATE INDEX IF NOT EXISTS idx_approval_window_review_records_candidate_id
ON approval_window_review_records(candidate_id);
"""

ACTIVATION_READINESS_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS activation_readiness_review_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  activation_readiness_review_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  command_review_id TEXT,
  execution_decision_review_id TEXT,
  execution_queue_review_id TEXT,
  approval_window_review_id TEXT,
  approval_status TEXT,
  window_state TEXT,
  review_status TEXT,
  readiness_status TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  reviewed_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_activation_readiness_review_records_market_id
ON activation_readiness_review_records(market_id);
CREATE INDEX IF NOT EXISTS idx_activation_readiness_review_records_reviewed_at
ON activation_readiness_review_records(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_activation_readiness_review_records_readiness_status
ON activation_readiness_review_records(readiness_status);
CREATE INDEX IF NOT EXISTS idx_activation_readiness_review_records_recommendation
ON activation_readiness_review_records(recommendation);
CREATE INDEX IF NOT EXISTS idx_activation_readiness_review_records_approval_status
ON activation_readiness_review_records(approval_status);
CREATE INDEX IF NOT EXISTS idx_activation_readiness_review_records_decision_id
ON activation_readiness_review_records(decision_id);
CREATE INDEX IF NOT EXISTS idx_activation_readiness_review_records_candidate_id
ON activation_readiness_review_records(candidate_id);
"""

ACTIVATION_AUTHORIZATION_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS activation_authorization_review_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  activation_authorization_review_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  command_review_id TEXT,
  execution_decision_review_id TEXT,
  execution_queue_review_id TEXT,
  approval_window_review_id TEXT,
  activation_readiness_review_id TEXT,
  approval_status TEXT,
  window_state TEXT,
  readiness_status TEXT,
  authorization_status TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  reviewed_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_activation_authorization_review_records_market_id
ON activation_authorization_review_records(market_id);
CREATE INDEX IF NOT EXISTS idx_activation_authorization_review_records_reviewed_at
ON activation_authorization_review_records(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_activation_authorization_review_records_authorization_status
ON activation_authorization_review_records(authorization_status);
CREATE INDEX IF NOT EXISTS idx_activation_authorization_review_records_recommendation
ON activation_authorization_review_records(recommendation);
CREATE INDEX IF NOT EXISTS idx_activation_authorization_review_records_approval_status
ON activation_authorization_review_records(approval_status);
CREATE INDEX IF NOT EXISTS idx_activation_authorization_review_records_decision_id
ON activation_authorization_review_records(decision_id);
CREATE INDEX IF NOT EXISTS idx_activation_authorization_review_records_candidate_id
ON activation_authorization_review_records(candidate_id);
"""

DEFAULT_RULES = {
    "min_edge_percent": "10",
    "min_liquidity": "100",
    "max_spread": "0.08",
    "max_position_percent": "2",
    "max_daily_loss_percent": "5",
    "circuit_breaker_loss_percent": "10",
}

DEFAULT_PROBABILITY_ENGINE_CONFIGS = [
    {
        "engine_id": "gaussian_v0",
        "engine_name": "Gaussian Probability v0",
        "engine_type": "PRIMARY",
        "version": "v0",
        "enabled": 1,
        "can_be_primary": 1,
        "description": "Accepted PWB-02 primary Gaussian probability engine.",
        "default_params": {"sigma": 2.5},
    },
    {
        "engine_id": "deb_shadow_v0",
        "engine_name": "DEB Shadow v0",
        "engine_type": "SHADOW",
        "version": "v0",
        "enabled": 1,
        "can_be_primary": 0,
        "description": "Placeholder shadow engine for future dynamic error balancing.",
        "default_params": {"mode": "placeholder_shadow"},
    },
    {
        "engine_id": "emos_shadow_v0",
        "engine_name": "EMOS Shadow v0",
        "engine_type": "SHADOW",
        "version": "v0",
        "enabled": 1,
        "can_be_primary": 0,
        "description": "Placeholder shadow engine for future EMOS calibration.",
        "default_params": {"mode": "placeholder_shadow"},
    },
]


def now_iso_db() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_probability_engine_configs(conn) -> None:
    now = now_iso_db()
    for item in DEFAULT_PROBABILITY_ENGINE_CONFIGS:
        conn.execute(
            """
            INSERT OR IGNORE INTO probability_engine_configs
            (engine_id, engine_name, engine_type, version, enabled, can_be_primary,
             description, default_params_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["engine_id"],
                item["engine_name"],
                item["engine_type"],
                item["version"],
                item["enabled"],
                item["can_be_primary"],
                item["description"],
                json.dumps(item["default_params"], ensure_ascii=False),
                now,
                now,
            ),
        )


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    if "/" in db_path:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.executescript(WEATHER_SCHEMA)
        conn.executescript(PROBABILITY_GOVERNANCE_SCHEMA)
        conn.executescript(POLYMARKET_CONNECTOR_SCHEMA)
        conn.executescript(SNAPSHOT_ARCHIVE_SCHEMA)
        conn.executescript(EXECUTION_DECISION_REVIEW_SCHEMA)
        conn.executescript(EXECUTION_QUEUE_REVIEW_SCHEMA)
        conn.executescript(APPROVAL_WINDOW_REVIEW_SCHEMA)
        conn.executescript(ACTIVATION_READINESS_REVIEW_SCHEMA)
        conn.executescript(ACTIVATION_AUTHORIZATION_REVIEW_SCHEMA)
        conn.executescript(WEATHER_ARCHIVE_SCHEMA)
        conn.executescript(OUTCOME_ARCHIVE_SCHEMA)
        conn.executescript(CALIBRATION_MEMORY_SCHEMA)
        conn.executescript(DEB_SHADOW_SCHEMA)
        conn.executescript(EMOS_SHADOW_SCHEMA)
        conn.executescript(SHADOW_ENGINE_EVALUATION_SCHEMA)
        conn.executescript(COMMAND_REVIEW_SCHEMA)
        for key, value in DEFAULT_RULES.items():
            conn.execute(
                "INSERT OR IGNORE INTO rule_configs (key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.execute(
            "INSERT OR IGNORE INTO system_state (key, value) VALUES (?, ?)",
            ("execution_mode", "OBSERVE_ONLY"),
        )
        init_probability_engine_configs(conn)
        conn.commit()
    finally:
        conn.close()
