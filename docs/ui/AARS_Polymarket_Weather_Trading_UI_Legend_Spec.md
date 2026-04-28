# AARS Polymarket Weather Trading Console
# UI Legend Spec

版本：v1.0  
日期：2026-04-25

## State Table

| State | Type | Primary State Allowed | Secondary State Allowed | Affects Gate | Triggers Operator Action | Color |
|---|---|---|---|---|---|---|
| LIVE | Freshness | No | Yes | Indirect | No | Green |
| STALE | Freshness | Yes | Yes | Indirect | Yes | Blue / Amber |
| ALERT | Market Signal | Yes | Yes | No | Yes | Red |
| ANOM | Anomaly Signal | Yes | Yes | No | Yes | Amber |
| BLOCKED | Gate State | Yes | Yes | Yes | Yes | Red |
| NORMAL | Display State | Yes | No | No | No | Green / Neutral |
| ALLOW | Gate State | No | Yes | Yes | No | Green |
| B | Data Quality | No | Yes | Indirect | Yes | Magenta |
| OPS | System State | Not for market-card primary state | Yes | No | Yes | Red / Amber |
| FOCUS | View State | No | Yes | No | No | Blue |
| WATCH | View Group | No | Yes | No | No | Amber / Neutral |

## Primary State Policy

```text
BLOCKED > ALERT > ANOM > STALE > NORMAL
```

Primary state is for HMI display prioritization only and does not redefine gate semantics.

## Color Rules

- Red: `BLOCKED`, `ALERT red`, critical `OPS`, top risk numbers.
- Amber: `ANOM`, warning, medium risk.
- Green: `LIVE`, `ALLOW`, `NORMAL`, healthy.
- Blue: selected, focus, neutral info.
- Magenta: field-level data quality issue `B`.

## Data Quality Marker

`B` means bad field-level quality. It does not replace the primary state; it is a secondary field marker.

