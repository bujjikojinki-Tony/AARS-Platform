起完之后，建议按这个顺序做检查，最快能定位是哪一层没通。

**1. 规则层**
```bash
cd /Users/maolei/AARS-Platform/weather-rules-research
python scripts/run_weather_realtime.py
```
看输出里有没有：
- `forecast_realtime_snapshot.json`
- `official_label_summary.json`
- `station_settlement_summary.json`

**2. Polymarket ingest**
```bash
cd /Users/maolei/AARS-Platform/polymarket-weather-ingest
PYTHONPATH=src python scripts/run_polymarket_realtime.py
```
看输出里有没有：
- `market_realtime_snapshot.json`
- `market_realtime_simple.json`
- `market_realtime_simple_<family>.json`

**3. 比较引擎**
```bash
cd /Users/maolei/AARS-Platform/weather-comparison-engine
PYTHONPATH=src python -m weather_comparison_engine.main build-monitoring-status
PYTHONPATH=src python -m weather_comparison_engine.main build-gate-stack-api
PYTHONPATH=src python -m weather_comparison_engine.main build-gate-stack-automation-summary
```
看输出里有没有：
- `monitoring_status.json`
- `gate_stack_api.json`
- `gate_stack_automation_summary.json`

**4. Telegram**
```bash
cd /Users/maolei/AARS-Platform/weather-telegram-console
PYTHONPATH=src weather-telegram-console
```
然后在 Telegram 里测：
- `/start`
- `/status`
- `/market`
- `/signal`
- `/opsqueue`

**5. Dashboard**
```bash
cd /Users/maolei/AARS-Platform/weather-dashboard
streamlit run src/weather_dashboard/app.py --server.port 8514 --server.address 127.0.0.1
```
打开后先看：
- `Top Parameter Surface`
- `Command`
- `Pipeline`
- `Validation`

**6. Execution gateway**
```bash
cd /Users/maolei/AARS-Platform/weather-execution-gateway
PYTHONPATH=src python -m weather_execution_gateway.main check-production-readiness
```
重点看：
- `production_readiness_report.json`
- `blocked / warning / passed`

如果你要，我下一条可以直接给你补一份“**最小可运行组合**”，也就是只启动 3 个进程先把界面跑起来。