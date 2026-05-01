
# **Round_PWB-01_Acceptance_Test**

## **1. 文件目的**

本文件用于固定：

```text
Round PWB-01 — Execution Core v0
```

的验收边界。

本轮验收只判断 Execution Core v0 是否形成最小闭环：

```text
mock market scan
→ strategy signal
→ opportunity candidate
→ risk gate
→ simulation
→ SQLite persistence
→ audit log
→ minimal API / UI 可读取
```

本文件不是性能测试文件，不验证真实交易收益，不验证天气预测准确率，不验证实盘执行能力。

---

# **2. 验收原则**

## **2.1 必须满足**

```text
1. 所有测试使用 mock market source。
2. 所有测试使用临时 SQLite 数据库。
3. 所有交易动作默认不触发 live execution。
4. 所有 command / scan / simulation 都必须写入 audit log。
5. 系统初始 mode 必须是 OBSERVE_ONLY。
6. LIVE_EXECUTE 不得作为默认可选操作出现。
```

---

## **2.2 不纳入验收**

```text
1. 不验证真实 Polymarket API。
2. 不验证真实天气 API。
3. 不验证 DEB / EMOS / LGBM。
4. 不验证 Telegram bot。
5. 不验证订阅 / 支付 / 商业化功能。
6. 不验证复杂前端图表。
7. 不验证 portfolio-level 风险管理。
8. 不验证真实资金交易。
```

---

# **3. 测试环境**

## **3.1 Required test setup**

```text
Python 3.11+
SQLite
pytest
FastAPI test client, if API layer exists
No external network dependency
```

---

## **3.2 Test database**

测试必须使用临时数据库，例如：

```text
/tmp/pwb01_test.sqlite
```

或 pytest fixture 临时路径。

要求：

```text
1. 每个测试前可清空数据库。
2. init_db() 可重复运行。
3. 测试结束后不依赖持久状态。
```

---

## **3.3 Test fixtures**

必须至少包含 5 个 mock markets：

```text
mock_weather_strong_yes
mock_weather_weak_edge
mock_binary_arb
mock_low_liquidity
mock_high_spread
```

建议 fixture：

```json
[
  {
    "marketId": "mock_weather_strong_yes",
    "question": "Will Tokyo high temperature exceed 30C on test date?",
    "yesPrice": 0.52,
    "noPrice": 0.49,
    "liquidity": 1000,
    "spread": 0.03,
    "source": "mock"
  },
  {
    "marketId": "mock_weather_weak_edge",
    "question": "Will Osaka high temperature exceed 28C on test date?",
    "yesPrice": 0.50,
    "noPrice": 0.51,
    "liquidity": 1000,
    "spread": 0.03,
    "source": "mock"
  },
  {
    "marketId": "mock_binary_arb",
    "question": "Binary arbitrage test market",
    "yesPrice": 0.45,
    "noPrice": 0.50,
    "liquidity": 1200,
    "spread": 0.02,
    "source": "mock"
  },
  {
    "marketId": "mock_low_liquidity",
    "question": "Low liquidity test market",
    "yesPrice": 0.40,
    "noPrice": 0.61,
    "liquidity": 20,
    "spread": 0.03,
    "source": "mock"
  },
  {
    "marketId": "mock_high_spread",
    "question": "High spread test market",
    "yesPrice": 0.40,
    "noPrice": 0.63,
    "liquidity": 1000,
    "spread": 0.15,
    "source": "mock"
  }
]
```

---

# **4. 默认规则**

测试必须使用以下默认规则，除非单个测试显式覆盖：

```text
min_edge_percent = 10
min_liquidity = 100
max_spread = 0.08
max_position_percent = 2
max_daily_loss_percent = 5
circuit_breaker_loss_percent = 10
execution_mode = OBSERVE_ONLY
```

---

# **5. Acceptance Test 01 — Init DB works**

## **Purpose**

确认数据库初始化可重复执行。

## **Given**

```text
A fresh temporary SQLite database path
```

## **When**

```text
init_db() is called twice
```

## **Then**

```text
1. No exception is raised.
2. All required tables exist.
3. system_state exists.
4. rule_configs exists.
5. default execution_mode = OBSERVE_ONLY.
```

## **Required tables**

```text
market_snapshots
strategy_signals
opportunity_candidates
execution_decisions
simulation_results
audit_logs
rule_configs
system_state
```

## **Pass condition**

```text
All required tables exist and default state is initialized.
```

---

# **6. Acceptance Test 02 — Mock market source returns fixtures**

## **Purpose**

确认测试不依赖外部 API。

## **Given**

```text
MockMarketSource
```

## **When**

```text
fetch_markets() is called
```

## **Then**

```text
1. At least 5 markets are returned.
2. Every market has source = mock.
3. Every market has yes_price.
4. Every market has no_price.
5. Every market has liquidity.
6. Every market has spread.
```

## **Pass condition**

```text
Mock market source returns deterministic local fixtures.
```

---

# **7. Acceptance Test 03 — Placeholder probability provider is deterministic**

## **Purpose**

确认 placeholder probability 不引入随机性。

## **Given**

```text
PlaceholderProbabilityProvider
```

## **When**

```text
estimate(mock_weather_strong_yes) is called multiple times
```

## **Then**

```text
1. Same market returns same probability.
2. Probability is between 0 and 1.
3. Unknown market returns 0.5.
```

## **Pass condition**

```text
Probability provider is stable and bounded.
```

---

# **8. Acceptance Test 04 — Weather edge strategy creates signal for strong edge**

## **Purpose**

确认 weather edge strategy v0 能生成信号。

## **Given**

```text
mock_weather_strong_yes
placeholder model probability = 0.72
yes_price = 0.52
min_edge_percent = 10
```

## **When**

```text
WeatherEdgeStrategy.evaluate(market) is called
```

## **Then**

```text
1. StrategySignal is created.
2. side = YES.
3. model_probability = 0.72.
4. market_probability = 0.52.
5. edge_percent = 20.
6. strategy_id = weather_edge_v0.
7. confidence = LOW.
8. reason mentions placeholder probability.
```

## **Pass condition**

```text
Strong weather edge creates a valid StrategySignal.
```

---

# **9. Acceptance Test 05 — Weather edge strategy ignores weak edge**

## **Purpose**

确认低 edge 不会生成机会。

## **Given**

```text
mock_weather_weak_edge
placeholder model probability = 0.51
yes_price = 0.50
min_edge_percent = 10
```

## **When**

```text
WeatherEdgeStrategy.evaluate(market) is called
```

## **Then**

```text
signal = None
```

## **Pass condition**

```text
Weak edge market does not create StrategySignal.
```

---

# **10. Acceptance Test 06 — Binary arbitrage strategy creates signal**

## **Purpose**

确认 binary arbitrage v0 能识别明显套利候选。

## **Given**

```text
mock_binary_arb
yes_price = 0.45
no_price = 0.50
fee_buffer = 0.02
min_profit = 0.01
```

## **When**

```text
BinaryArbStrategy.evaluate(market) is called
```

## **Then**

```text
1. StrategySignal is created.
2. strategy_id = binary_arb_v0.
3. reason mentions paired-arb candidate.
4. edge_percent or profit_gap is positive.
```

## **Pass condition**

```text
YES + NO < 0.97 creates binary arbitrage signal.
```

---

# **11. Acceptance Test 07 — Risk gate passes strong candidate**

## **Purpose**

确认强机会能通过风险门控。

## **Given**

```text
OpportunityCandidate:
edge_percent = 20
liquidity = 1000
spread = 0.03
circuit_breaker = inactive
```

## **When**

```text
RiskManager.evaluate(candidate) is called
```

## **Then**

```text
1. status = PASS.
2. minEdgePassed = true.
3. minLiquidityPassed = true.
4. maxSpreadPassed = true.
5. circuitBreakerInactive = true.
6. reasons is empty or contains only non-blocking notes.
```

## **Pass condition**

```text
Strong candidate passes risk gate.
```

---

# **12. Acceptance Test 08 — Risk gate blocks weak edge**

## **Purpose**

确认低 edge 被阻断。

## **Given**

```text
OpportunityCandidate:
edge_percent = 3
liquidity = 1000
spread = 0.03
```

## **When**

```text
RiskManager.evaluate(candidate) is called
```

## **Then**

```text
1. status = BLOCK.
2. minEdgePassed = false.
3. reasons includes edge below threshold.
```

## **Pass condition**

```text
Weak edge candidate is blocked.
```

---

# **13. Acceptance Test 09 — Risk gate blocks low liquidity**

## **Purpose**

确认低流动性被阻断。

## **Given**

```text
OpportunityCandidate:
edge_percent = 20
liquidity = 20
spread = 0.03
```

## **When**

```text
RiskManager.evaluate(candidate) is called
```

## **Then**

```text
1. status = BLOCK.
2. minLiquidityPassed = false.
3. reasons includes liquidity below threshold.
```

## **Pass condition**

```text
Low liquidity candidate is blocked.
```

---

# **14. Acceptance Test 10 — Risk gate blocks high spread**

## **Purpose**

确认高 spread 被阻断。

## **Given**

```text
OpportunityCandidate:
edge_percent = 20
liquidity = 1000
spread = 0.15
```

## **When**

```text
RiskManager.evaluate(candidate) is called
```

## **Then**

```text
1. status = BLOCK.
2. maxSpreadPassed = false.
3. reasons includes spread above threshold.
```

## **Pass condition**

```text
High spread candidate is blocked.
```

---

# **15. Acceptance Test 11 — Strategy runner creates candidates**

## **Purpose**

确认扫描闭环有效。

## **Given**

```text
MockMarketSource
WeatherEdgeStrategy
BinaryArbStrategy
RiskManager
Repository
Temporary SQLite database
```

## **When**

```text
StrategyRunner.run_once() is called
```

## **Then**

```text
1. market_snapshots table has records.
2. strategy_signals table has records.
3. opportunity_candidates table has records.
4. at least one candidate has risk_status = PASS.
5. at least one candidate has risk_status = BLOCK.
6. audit_logs contains CANDIDATE_CREATED.
```

## **Pass condition**

```text
Strategy runner creates persisted candidates and audit logs.
```

---

# **16. Acceptance Test 12 — Candidate action status is resolved**

## **Purpose**

确认 risk gate 与 action status 对齐。

## **Given**

```text
StrategyRunner.run_once()
```

## **When**

```text
Candidates are listed from repository
```

## **Then**

```text
1. PASS candidate action_status is WATCH or SIMULATE.
2. WARN candidate action_status is WATCH.
3. BLOCK candidate action_status is BLOCKED.
```

## **Pass condition**

```text
risk_status and action_status are consistent.
```

---

# **17. Acceptance Test 13 — Simulation creates result for PASS candidate**

## **Purpose**

确认模拟执行可用。

## **Given**

```text
A PASS OpportunityCandidate
position_size = 10
```

## **When**

```text
Simulator.simulate(candidate_id, position_size=10) is called
```

## **Then**

```text
1. SimulationResult is created.
2. simulation_results table has one record.
3. execution_decisions table has one related decision or equivalent decision record.
4. audit_logs contains SIMULATION_CREATED.
5. execution_status = SIMULATED or result_status = CREATED / COMPLETED.
```

## **Pass condition**

```text
PASS candidate can be simulated and persisted.
```

---

# **18. Acceptance Test 14 — BLOCK candidate cannot be simulated by default**

## **Purpose**

确认阻断候选不会默认进入模拟或执行。

## **Given**

```text
A BLOCK OpportunityCandidate
allow_blocked_simulation = false
```

## **When**

```text
Simulator.simulate(candidate_id) is called
```

## **Then**

```text
1. SimulationResult is not created.
2. Error or structured rejection is returned.
3. audit_logs contains SIMULATION_REJECTED or equivalent.
```

## **Pass condition**

```text
Blocked candidate cannot be simulated by default.
```

---

# **19. Acceptance Test 15 — Simulation never calls live execution**

## **Purpose**

确认本轮不会触发真实交易。

## **Given**

```text
A PASS OpportunityCandidate
```

## **When**

```text
Simulator.simulate(candidate_id) is called
```

## **Then**

```text
1. No live executor is called.
2. No live trade record is created.
3. execution mode remains OBSERVE_ONLY or SIMULATION.
4. audit log does not contain LIVE_EXECUTED.
```

## **Pass condition**

```text
Simulation is isolated from live execution.
```

---

# **20. Acceptance Test 16 — Command parser recognizes supported commands**

## **Purpose**

确认命令解析稳定。

## **Given**

```text
CommandParser
```

## **When / Then**

```text
/run scan → RUN_SCAN
/list opportunities → LIST_OPPORTUNITIES
/simulate abc → SIMULATE with candidate_id=abc
/block abc → BLOCK with candidate_id=abc
/set mode observe_only → SET_MODE OBSERVE_ONLY
/set mode simulation → SET_MODE SIMULATION
/show rules → SHOW_RULES
/show history → SHOW_HISTORY
/simulate → INVALID
/auto trade → UNKNOWN or UNSUPPORTED
```

## **Pass condition**

```text
Supported commands resolve correctly; unsafe commands are rejected.
```

---

# **21. Acceptance Test 17 — Command API runs scan**

## **Purpose**

确认 Command API 可以触发扫描。

## **Given**

```text
POST /api/command
body: { "command": "/run scan" }
```

## **When**

```text
Request is sent
```

## **Then**

```text
1. Response status is 200.
2. Response includes candidates_count.
3. audit_logs contains COMMAND_EXECUTED.
4. opportunity_candidates table has records.
```

## **Pass condition**

```text
/run scan works through Command API.
```

---

# **22. Acceptance Test 18 — Command API simulates candidate**

## **Purpose**

确认 Command API 可以触发模拟。

## **Given**

```text
Existing PASS candidate
POST /api/command
body: { "command": "/simulate <candidate_id>" }
```

## **When**

```text
Request is sent
```

## **Then**

```text
1. Response status is 200.
2. Response includes simulation_id.
3. simulation_results table has record.
4. audit_logs contains COMMAND_EXECUTED.
5. audit_logs contains SIMULATION_CREATED.
```

## **Pass condition**

```text
/simulate works through Command API.
```

---

# **23. Acceptance Test 19 — Unsupported live command is rejected**

## **Purpose**

确认本轮不能通过命令启用实盘。

## **Given**

```text
POST /api/command
body: { "command": "/set mode live_execute" }
```

or

```text
POST /api/command
body: { "command": "/auto trade" }
```

## **When**

```text
Request is sent
```

## **Then**

```text
1. Response indicates unsupported or rejected.
2. system mode does not become LIVE_EXECUTE.
3. audit_logs contains COMMAND_REJECTED or equivalent.
4. No live execution record is created.
```

## **Pass condition**

```text
Live / auto-trade commands are rejected.
```

---

# **24. Acceptance Test 20 — Opportunity API scan works**

## **Purpose**

确认 Opportunity API 可用。

## **Given**

```text
POST /api/opportunities/scan
```

## **When**

```text
Request is sent
```

## **Then**

```text
1. Response status is 200.
2. Response includes candidate list or candidates_count.
3. GET /api/opportunities returns candidates.
```

## **Pass condition**

```text
Opportunity API can scan and list candidates.
```

---

# **25. Acceptance Test 21 — Opportunity block works**

## **Purpose**

确认候选可被手动阻断。

## **Given**

```text
Existing candidate
POST /api/opportunities/{candidate_id}/block
```

## **When**

```text
Request is sent
```

## **Then**

```text
1. Candidate action_status = BLOCKED.
2. audit_logs contains CANDIDATE_BLOCKED.
3. GET /api/opportunities/{candidate_id} reflects BLOCKED status.
```

## **Pass condition**

```text
Candidate can be manually blocked.
```

---

# **26. Acceptance Test 22 — History API returns persisted records**

## **Purpose**

确认历史记录可回放。

## **Given**

```text
After scan and simulation
```

## **When**

```text
GET /api/history/signals
GET /api/history/candidates
GET /api/history/simulations
GET /api/history/audit
```

## **Then**

```text
1. signals endpoint returns records.
2. candidates endpoint returns records.
3. simulations endpoint returns records.
4. audit endpoint returns records.
5. audit payload_json is parseable JSON.
```

## **Pass condition**

```text
History API supports basic replay.
```

---

# **27. Acceptance Test 23 — Settings API returns defaults**

## **Purpose**

确认默认规则可读取。

## **Given**

```text
Fresh system
```

## **When**

```text
GET /api/settings/rules
GET /api/settings/mode
```

## **Then**

```text
1. rules include min_edge_percent = 10.
2. rules include min_liquidity = 100.
3. rules include max_spread = 0.08.
4. mode = OBSERVE_ONLY.
```

## **Pass condition**

```text
Default settings are initialized and readable.
```

---

# **28. Acceptance Test 24 — Settings API updates safe rules**

## **Purpose**

确认可安全修改规则。

## **Given**

```text
POST /api/settings/rules
body: { "min_edge_percent": 12 }
```

## **When**

```text
Request is sent
```

## **Then**

```text
1. Response status is 200.
2. GET /api/settings/rules returns min_edge_percent = 12.
3. audit_logs contains RULE_UPDATED.
```

## **Pass condition**

```text
Safe risk rule can be updated and audited.
```

---

# **29. Acceptance Test 25 — Settings API rejects LIVE_EXECUTE mode**

## **Purpose**

确认实盘模式不在本轮开启。

## **Given**

```text
POST /api/settings/mode
body: { "mode": "LIVE_EXECUTE" }
```

## **When**

```text
Request is sent
```

## **Then**

```text
1. Request is rejected.
2. mode remains OBSERVE_ONLY or previous safe mode.
3. audit_logs contains MODE_CHANGE_REJECTED or equivalent.
```

## **Pass condition**

```text
LIVE_EXECUTE cannot be enabled in PWB-01.
```

---

# **30. Acceptance Test 26 — Minimal Opportunity Board reads candidates**

## **Purpose**

确认前端可以读取候选列表。

## **Given**

```text
API is running
Candidates exist
Opportunity Board page is opened
```

## **When**

```text
Page loads
```

## **Then**

```text
1. Page calls GET /api/opportunities.
2. Candidate rows are displayed.
3. risk_status is visible.
4. action_status is visible.
5. Scan button exists.
6. Block button exists for non-blocked candidates.
```

## **Pass condition**

```text
Opportunity Board displays persisted candidates.
```

---

# **31. Acceptance Test 27 — Minimal Command Page runs command**

## **Purpose**

确认前端 Command 页面可执行基础命令。

## **Given**

```text
Command page is opened
```

## **When**

```text
User enters /run scan
```

## **Then**

```text
1. Page calls POST /api/command.
2. Result panel shows candidates_count.
3. Command history updates.
4. No page crash.
```

## **Pass condition**

```text
Command page can run /run scan.
```

---

# **32. Acceptance Test 28 — Minimal History Page displays records**

## **Purpose**

确认前端 History 页面可回放记录。

## **Given**

```text
Signals, candidates, simulations, and audit logs exist
```

## **When**

```text
History page opens
```

## **Then**

```text
1. Signals tab displays records.
2. Candidates tab displays records.
3. Simulations tab displays records.
4. Audit Logs tab displays records.
```

## **Pass condition**

```text
History page displays persisted records.
```

---

# **33. Acceptance Test 29 — Minimal Settings Page displays safe mode**

## **Purpose**

确认前端不会误导用户启用实盘。

## **Given**

```text
Settings page is opened
```

## **When**

```text
Execution Mode section is displayed
```

## **Then**

```text
1. Current mode is visible.
2. OBSERVE_ONLY is available.
3. SIMULATION is available.
4. PAPER_TRADE may be visible but disabled or clearly marked if not implemented.
5. LIVE_EXECUTE is not available as default option.
```

## **Pass condition**

```text
Settings page only exposes safe execution modes.
```

---

# **34. Acceptance Test 30 — Baseline freeze readiness**

## **Purpose**

确认 PWB-01 可以冻结。

## **Given**

```text
Acceptance Tests 01–29 have passed
```

## **When**

```text
Freeze review is performed
```

## **Then**

```text
1. PWB-01 status note can be completed.
2. Accepted path inventory can be completed.
3. Baseline freeze note can be completed.
4. PWB-02 entry is clearly marked as future work.
5. No live trading is enabled.
6. Weather Intelligence remains deferred to PWB-02.
```

## **Pass condition**

```text
PWB-01 is ready to freeze without continuing scope expansion.
```

---

# **35. Minimal pytest file outline**

建议 Codex 生成：

```text
tests/test_pwb01_acceptance.py
```

基础结构：

```python
import pytest

from backend.storage.db import init_db
from backend.sources.mock_market_source import MockMarketSource
from backend.probability.placeholder_probability_provider import PlaceholderProbabilityProvider
from backend.strategies.weather_edge_strategy import WeatherEdgeStrategy
from backend.strategies.binary_arb_strategy import BinaryArbStrategy
from backend.execution.risk_manager import RiskManager
from backend.execution.strategy_runner import StrategyRunner
from backend.execution.simulator import Simulator


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "pwb01_test.sqlite"
    init_db(str(db_path))
    return str(db_path)


def test_init_db_works(test_db):
    # assert required tables and default mode
    pass


def test_mock_market_source_returns_fixtures():
    # assert at least 5 mock markets
    pass


def test_placeholder_probability_provider_is_deterministic():
    # assert deterministic probability
    pass


def test_weather_edge_strategy_creates_signal_for_strong_edge():
    # assert signal for mock_weather_strong_yes
    pass


def test_weather_edge_strategy_ignores_weak_edge():
    # assert None for weak edge
    pass


def test_binary_arbitrage_strategy_creates_signal():
    # assert binary arb signal
    pass


def test_risk_gate_passes_strong_candidate():
    # assert PASS
    pass


def test_risk_gate_blocks_weak_edge():
    # assert BLOCK
    pass


def test_risk_gate_blocks_low_liquidity():
    # assert BLOCK
    pass


def test_risk_gate_blocks_high_spread():
    # assert BLOCK
    pass


def test_strategy_runner_creates_candidates(test_db):
    # assert full scan loop
    pass


def test_simulation_creates_result_for_pass_candidate(test_db):
    # assert simulation result
    pass


def test_block_candidate_cannot_be_simulated_by_default(test_db):
    # assert simulation rejection
    pass


def test_simulation_never_calls_live_execution(test_db):
    # assert no live execution
    pass


def test_command_parser_recognizes_supported_commands():
    # assert parser intents
    pass
```

---

# **36. Codex Acceptance Prompt**

可直接交给 Codex：

```text
Implement Round PWB-01 acceptance tests only.

Create or update:
- tests/test_pwb01_acceptance.py

Use the existing PWB-01 backend modules:
- models
- storage/db.py
- storage/repositories.py
- sources/mock_market_source.py
- probability/placeholder_probability_provider.py
- strategies/weather_edge_strategy.py
- strategies/binary_arb_strategy.py
- execution/risk_manager.py
- execution/strategy_runner.py
- execution/simulator.py
- api/command_parser.py

Scope:
- Test the PWB-01 execution core only.
- Use temporary SQLite database.
- Use mock market source only.
- Do not call real Polymarket.
- Do not call real weather APIs.
- Do not enable LIVE_EXECUTE.
- Do not start PWB-02.

Required tests:
1. init db works
2. mock market source returns fixtures
3. placeholder probability provider is deterministic
4. weather edge strategy creates signal for strong edge
5. weather edge strategy ignores weak edge
6. binary arbitrage strategy creates signal
7. risk gate passes strong candidate
8. risk gate blocks weak edge
9. risk gate blocks low liquidity
10. risk gate blocks high spread
11. strategy runner creates candidates
12. candidate action status is resolved
13. simulation creates result for PASS candidate
14. BLOCK candidate cannot be simulated by default
15. simulation never calls live execution
16. command parser recognizes supported commands

Do not add new features to make tests pass.
Only fix minimal bugs directly related to PWB-01 acceptance.
```

---

# **37. Obsidian 放置位置**

```text
03_Projects/Polymarket_Bot/Implementation/
  Round_PWB-01_Acceptance_Test.md
```

---

# **38. Repo 放置位置**

```text
docs/implementation/
  round-pwb-01-acceptance-test.md
```

---

# **39. 下一步**

继续进入：

```text
Execution_Core_v0.md
```

用于把实现侧架构单独固化，方便 Codex 按模块落代码。