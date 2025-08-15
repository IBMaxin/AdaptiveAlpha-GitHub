# PRO DOCS

## LLM Assistance

LLM integration enables automated code suggestions, strategy generation, and agent orchestration. All LLM requests and responses are logged for auditability. See `services/llm_client.py` for usage and helper notes.

**Quick Example:**

````python
from services.llm_client import LLMClient, load_cfg
cfg = load_cfg()
llm = LLMClient(cfg)
print(llm.chat("system", "user"))
```text


## HF-Battle: Professional Codebase Documentation


## Executive Summary

HF-Battle is a modular, AI-driven research and trading automation platform built on Freqtrade. It features continuous learning, LLM-powered strategy generation and improvement, robust error healing, and full-cycle automation for quantitative trading research and deployment.

---

## Architecture Overview



### High-Level Flow

1. **Strategy Generation**: LLM generates a new, unique trading strategy.
2. **Backtesting**: The strategy is backtested on a realistic, rotating timerange.
3. **Evaluation & Logging**: Results are parsed, metrics are logged, and only decent strategies are retained.
4. **Improvement**: LLM suggests code improvements based on backtest logs.
5. **Safe Patching**: Improvements are safely applied with backup and rollback.
6. **Continuous Loop**: The process repeats, enabling self-improving research.


---


## Directory & Module Map

```text
.
├── agents/                # Modular agents for orchestration, patching, healing, and learning
│   ├── self_loop_agent.py         # Main orchestrator for the learning loop
│   ├── strategy_lab.py           # LLM-driven strategy generation
│   ├── backtest_agent.py         # Backtest runner
│   ├── improve_agent.py          # LLM-based code improver
│   ├── patch_utils.py            # Safe patch/rollback utilities
│   ├── ...
├── app/                   # App-level orchestration, reporting, risk
├── battle/                # Tournament runner and results
├── scripts/               # Shell and Python scripts for automation
├── services/              # FastAPI healing server, LLM client, dashboard
├── strategies/            # All strategies (generated, hand-written, verified)
├── user_data/             # Results, logs, configs, verified strategies
├── config/                # Agent, LLM, and backtest configuration
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation (may be extracted from docs.zip)
├── PROJECT_DOCUMENTATION.md # User-level documentation
├── ...
```text

````

---

## Key Components & Responsibilities

### Agents

- **SelfLoopAgent** (`agents/self_loop_agent.py`):
  - Orchestrates the full research loop.
  - Ensures each cycle uses a unique strategy and timerange.
  - Logs only strategies that meet a minimum metric.
  - Copies verified strategies to `user_data/verified_strategies/`.
- **StrategyLab** (`agents/strategy_lab.py`):
  - Uses LLM to generate new strategies from prompts.
- **BacktestAgent** (`agents/backtest_agent.py`):
  - Runs Freqtrade backtests, captures logs and metrics.
- **ImproveAgent** (`agents/improve_agent.py`):
  - Uses LLM to suggest code improvements based on backtest logs.
- **PatchUtils** (`agents/patch_utils.py`):
  - Provides safe patching, backup, and rollback for code changes.
- **WatchdogAgent, DependencyMedic, ErrorMedic**: Health monitoring and auto-healing.

### Services

- **HealingServer** (`services/healing_server.py`): FastAPI server for health and healing endpoints.
- **LLMClient** (`services/llm_client.py`): Handles LLM API calls.
- **Dashboard** (`services/dashboard.html`): Web UI for monitoring.

### Scripts

- **run_backtest.sh**: Runs Freqtrade backtests with env vars.
- **run_healing_agents.sh**: Launches healing agents.
- **kraken_ohlcv_fetcher.py**: Fetches OHLCV data.

### Data & Results

- **learning_log.csv**: Logs all successful learning cycles and metrics.
- **verified_strategies/**: Only decent, tested strategies are saved here.
- **backtest_results/**: Raw backtest logs.

---

## Configuration

- **config/agents.yaml**: LLM and agent config (endpoints, prompts, thresholds).
- **config/battle.yaml**: Tournament config.
- **user_data/config.json|yaml**: User-specific settings.

---

## Automation & Continuous Learning

- Run the main loop:

  ```bash
  python -m agents.self_loop_agent 'Australian strategy full cycle loop' '' 100
  ```

- All results are auto-logged and only decent strategies are retained.
- Healing and watchdog agents can be run in parallel for self-repair.

---

## AI/LLM Integration

- Prompts are customizable in `strategy_lab.py` and `self_loop_agent.py`.
- LLM endpoint is set in `config/agents.yaml`.
- LLM is used for both strategy generation and improvement.

---

## Error Handling & Healing

- All patching is atomic and reversible (see `patch_utils.py`).
- HealingServer and WatchdogAgent monitor for errors and can auto-repair or alert.
- Logs are kept for all errors and healing actions.

---

## Extending the System

- Add new agents to `agents/` and register in orchestrator/config.
- Add new strategies to `strategies/` or let the LLM generate them.
- Tune learning loop logic, prompts, or thresholds in `self_loop_agent.py`.
- Add new data fetchers or health checks as needed.

---

## Best Practices & Pro Tips

- Use `learning_log.csv` for performance analytics and trend visualization.
- Only strategies with positive metrics are kept—tune this in `self_loop_agent.py`.
- Use `patch_utils.py` for all code changes to ensure safety.
- Monitor logs in `user_data/` and `services/` for troubleshooting.
- Use process managers (e.g., `systemd`, `supervisord`, `tmux`) for 24/7 operation.

---

## Common Commands

- Run the full loop:  
  `python -m agents.self_loop_agent 'Australian strategy full cycle loop' '' 100`
- View learning log:  
  `cat user_data/learning_log.csv`
- See verified strategies:  
  `ls user_data/verified_strategies/`
- Start healing server:  
  `uvicorn services.healing_server:app --reload --port 8000`
- Run a backtest:  
  `bash scripts/run_backtest.sh`

---

## Further Reading

- See `PROJECT_DOCUMENTATION.md` for user-level docs.
- See code comments and docstrings for API-level details.
- For LLM prompt engineering, see `strategy_lab.py` and `self_loop_agent.py`.

---

_This documentation is auto-generated and can be extended as your project evolves._
