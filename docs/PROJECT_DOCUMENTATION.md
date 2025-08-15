# PROJECT DOCUMENTATION

## LLM Assistance

This project leverages LLMs for code generation, agent improvement, and automation. All LLM interactions are logged. See `services/llm_client.py` for robust usage and helper comments.

**Example:**

```python
from services.llm_client import LLMClient, load_cfg
cfg = load_cfg()
llm = LLMClient(cfg)
print(llm.chat("system prompt", "user prompt"))
```

## HF-Battle Project Documentation

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

1. **Configure your LLM and agents:**

Edit `config/agents.yaml` and other config files as needed.

1. **Run the main agent loop:**

```bash
PYTHONPATH=. python3 agents/self_loop_agent.py "SmaRsi_v2" config/agents.yaml 5
```

1. **Chat with the LLM directly:**

```bash
python3 services/llm_client.py
```

1. **Run tests:**

```bash
PYTHONPATH=. pytest
```

This project is a robust, modular, and extensible research/trading automation platform. It supports continuous, LLM-driven improvement, safe patching, result review, and self-healing, with all results and learning cycles logged for transparency and further analysis.

---

## Directory Structure

```text
.
├── agents/
├── app/
├── battle/
├── scripts/
├── services/
├── strategies/
├── user_data/
├── config/
├── tests/
├── docs/
├── Makefile, package.json, pyproject.toml, tsconfig.json, etc.
```

---

## Core Components

### Agents (`agents/`)

- **base_agent.py**: Abstract base for all agents.
- **dependency_medic_agent.py**: Handles dependency checks and fixes.
- **error_medic_agent.py**: Detects and attempts to heal errors in the system.
- **orchestrator_agent.py**: Coordinates multiple agents for complex workflows.
- **patch_utils.py**: Safe patching, backup, and rollback utilities.
- **strategy_lab.py**: LLM-driven strategy generation.
- **watchdog_agent.py**: Monitors system health and triggers healing.
- **self_loop_agent.py**: Orchestrates the full research/trading loop: generate, backtest, improve, repeat. Handles continuous learning and logging.

### App (`app/`)

- **orchestrator.py**: High-level orchestration logic for the app.
- **report.py**: Reporting utilities and result formatting.
- **risk.py**: Risk management logic.

### Battle (`battle/`)

- **run_tournament.py**: Runs tournaments between strategies for benchmarking.
- **results/**: Stores tournament results.

### Scripts (`scripts/`)

- **run_backtest.sh**: Bash script to run Freqtrade backtests with environment variables.
- **run_healing_agents.sh**: Launches healing agents.
- **ensure_data.sh, guard.sh, health.sh, etc.**: Data, health, and utility scripts.
- **kraken_ohlcv_fetcher.py**: Fetches OHLCV data from Kraken.

### Services (`services/`)

- **healing_server.py**: FastAPI server for healing endpoints.
- **llm_client.py**: Client for interacting with LLM Studio or other LLM endpoints.
- **dashboard.html**: Web dashboard for monitoring.

### Strategies (`strategies/`)

- **BreakoutATR_v1.py, MeanRev_v1.py, SmaRsi_v1.py, etc.**: Example and generated trading strategies.
- **\*\*pycache\*\*/**: Compiled Python files.

### User Data (`user_data/`)

- **config.json, config.yaml**: User-specific configuration.
- **backtest_results/**: Stores logs/results of backtests.
- **verified_strategies/**: Stores only decent, verified, and tested strategies (auto-managed).
- **learning_log.csv**: CSV log of all learning cycles and their metrics.
- **paper_trades.sqlite, hyperopt.lock, etc.**: Data and lock files.

### Config (`config/` and `configs/`)

- **agent_config.yaml, agents.yaml**: Agent and LLM configuration.
- **battle.yaml, config.backtest.json, etc.**: Backtest and battle configuration.

### Tests (`tests/`)

- **test_kraken_ohlcv_fetcher.py**: Example test file.
- **\*\*pycache\*\*/**: Compiled test files.

---

## Automation & Learning Loop

- **SelfLoopAgent** (in `agents/self_loop_agent.py`) is the core orchestrator for continuous learning:
  - Generates a unique strategy each cycle using LLMs.
  - Runs a backtest on a new timerange.
  - Logs only strategies that meet a minimum performance threshold.
  - Saves verified strategies and logs metrics to `user_data/learning_log.csv`.
  - Applies LLM-suggested improvements and patches.
  - Supports full automation for hands-off research and improvement.

---

## Configuration Files

- **.env**: Environment variables for scripts and agents.
- **config.json, config.yaml**: Main configuration for Freqtrade and agents.
- **agents.yaml**: LLM and agent-specific settings.
- **battle.yaml**: Tournament/battle configuration.

---

## Logging & Results

- **Log files**: Each agent and script logs to its own file (e.g., `agent_server.log`, `healing_server.log`).
- **Backtest results**: Saved in `user_data/backtest_results/`.
- **Learning log**: All successful learning cycles are appended to `user_data/learning_log.csv`.
- **Verified strategies**: Only decent, tested strategies are copied to `user_data/verified_strategies/`.

---

## Development & Utilities

- **Makefile**: Common build and run commands.
- **package.json, tsconfig.json**: For TypeScript/Node.js utilities.
- **pyproject.toml**: Python project configuration.
- **docs/**: Documentation (may be extracted from `docs.zip`).

---

## Extending & Customizing

- **Add new agents**: Place in `agents/` and register in orchestrator or config.
- **Add new strategies**: Place in `strategies/` or let the LLM generate them.
- **Tune learning loop**: Adjust thresholds, prompts, or logic in `self_loop_agent.py`.
- **Integrate new data sources**: Add fetchers to `scripts/` or `services/`.
- **Customize healing**: Extend `healing_server.py` and related agents.

---

## AI Helper Hints

- Tune LLM prompts in `strategy_lab.py` and `self_loop_agent.py` for better strategy generation.
- Use `patch_utils.py` for safe code changes.
- Visualize `learning_log.csv` for performance trends.
- Use `watchdog_agent.py` and `healing_server.py` for self-healing and monitoring.
- Add new metrics to the learning log as needed.

---

## Common Commands & Snippets

- Run the full self-learning loop:

  ```bash
  python -m agents.self_loop_agent 'Australian strategy full cycle loop' '' 10
  ```

- View the learning log:

  ```bash
  cat user_data/learning_log.csv
  ```

- See only verified strategies:

  ```bash
  ls user_data/verified_strategies/
  ```

- Run the healing server:

  ```bash
  uvicorn services.healing_server:app --reload --port 8000
  ```

- Install required Python package:

  ```bash
  pip install python-multipart
  ```

- Run a backtest manually:

  ```bash
  bash scripts/run_backtest.sh
  ```

- Generate a new strategy with LLM:

  ```python
  from agents.strategy_lab import main as generate_strategy
  generate_strategy("Create a unique RSI+MACD strategy for 1h timeframe.")
  ```

- Apply a patch safely:

  ```python
  from agents.patch_utils import apply_patch, backup_file, rollback_file
  backup_file('strategies/MyStrategy.py')
  success = apply_patch('strategies/MyStrategy.py', patch_text)
  if not success:
      rollback_file('strategies/MyStrategy.py')
  ```

- Check what’s using a port:

  ```bash
  lsof -i :8000
  ```

- Run the watchdog agent:

  ```bash
  python -m agents.watchdog_agent
  ```

---

## Quick Start

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

1. **Configure your LLM and agents:**

Edit `config/agents.yaml` and other config files as needed.

1. **Run the main agent loop:**

```bash
PYTHONPATH=. python3 agents/self_loop_agent.py "SmaRsi_v2" config/agents.yaml 5
```

1. **Chat with the LLM directly:**

```bash
python3 services/llm_client.py
```

1. **Run tests:**

```bash
PYTHONPATH=. pytest
```

## Best Practices

- Keep `.env` and secrets out of version control.
- Use the provided scripts for safe automation and patching.
- Regularly clean up bytecode and cache files.
- Review logs and verified strategies in `user_data/`.

## Contributing

- Follow PEP8 and type hinting guidelines.
- Write tests for new features and bugfixes.
- Document new modules and scripts in this file.

---

For advanced usage, see `PRO_DOCS.md` and the `docs/` folder.
