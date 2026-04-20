# weather-signal-engine

Signal generation engine for rule-aware weather market monitoring.

## Purpose

This repository turns:
- rulebook outputs,
- station mappings,
- weather forecasts,
- optional market snapshots

into structured signal events.

It does not send Telegram messages directly.
It does not execute trades directly.

It produces:
- signal scores
- confidence estimates
- action hints
- serialized payloads for downstream consumers

## Inputs

Primary upstream inputs:
- `rulebook.json`
- `station_map.json`
- Open-Meteo forecast data
- optional market metadata / market price snapshots

## Outputs

Primary downstream outputs:
- `SignalEvent`
- confidence
- action hint
- alert payload JSON

## First MVP Scope

Only support:
- one city
- one market family
- daily high temperature
- one simple edge type:
  model band vs market expectation

## Suggested Flow

```text
rulebook
→ forecast ingest
→ feature extraction
→ score
→ signal event
→ alert payload
```
