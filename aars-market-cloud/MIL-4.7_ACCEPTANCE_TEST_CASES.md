# MIL-4.7 Verification & Acceptance Pack

| ID | Test | Machine criterion | Executor |
|---|---|---|---|
| TC-01 | Trial continuity | >=72h | Acceptance runner |
| TC-02 | Market data continuity | freshness/gap review | Market health + human |
| TC-03 | Forecast cadence | PASS >=95%; WARN 80-95%; FAIL <80% | Acceptance runner |
| TC-04 | Asset/horizon identity | forecast bound to symbol+horizon | Acceptance runner |
| TC-06 | Probability validity | each in [0,1], sum=1 | Acceptance runner |
| TC-07 | Forecast ID uniqueness | zero duplicate IDs | SQLite check |
| TC-08/09 | Mature outcome settlement | PASS >=98%; WARN 95-98%; FAIL <95% | Acceptance runner |
| TC-10 | Scorecard | artifact exists | Acceptance runner |
| TC-11 | LLM failure isolation | controlled failure must not stop Quant/API | Human-controlled injection |
| TC-12 | Execution boundary | PAPER_ONLY, authority NONE | Machine + human review |

At nominal 4h cadence, 3 assets and 2 horizons, 72h produces about 108 forecasts. The runner computes the expected count from actual observed hours rather than hard-coding 108.

TC-02 and TC-11 intentionally remain REVIEW until their independent evidence exists. The system must not fabricate a PASS.

Final verdict remains HUMAN_SIGNOFF_REQUIRED.
