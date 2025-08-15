### Scripts

- **run_backtest.sh**: Runs Freqtrade backtests with env vars.
- **run_healing_agents.sh**: Launches healing agents.
- **kraken_ohlcv_fetcher.py**: Fetches OHLCV data.

### Features

...

# HF-Battle (Freqtrade + LLM Agents)

## LLM Assistance Integration

This project supports robust LLM (Large Language Model) assistance for code generation, strategy improvement, and agent orchestration. All LLM requests and responses are logged for traceability. See `services/llm_client.py` for usage examples and integration details.

**Quick LLM Usage Example:**

```python
from services.llm_client import LLMClient, load_cfg
cfg = load_cfg()
llm = LLMClient(cfg)
response = llm.chat("You are a helpful trading assistant.", "Write a Freqtrade strategy that buys when RSI < 30.")
print(response)
```

An opinionated, reproducible research sandbox for **Freqtrade** strategies powered by **local LLM orchestration**. Targets WSL2 (Ubuntu) + Windows, but runs on Linux/macOS too.

---

# HF-Battle: Modular AI-Driven Trading Research & Automation

## Features

- Modular agents for strategy generation, backtesting, improvement, and healing
- LLM-powered code generation and improvement (OpenAI-compatible)
- Full-cycle automation and logging
- Robust error handling and self-healing
- CI/CD, code quality, and reproducibility

---

## Quickstart

```bash
# Clone and enter project
git clone git@github.com:IBMaxin/CodingP1.1.git
cd CodingP1.1

# Pin Python version
echo "3.11.9" > .python-version

# Create and activate venv
python3.11 -m venv .venv-ft2025
source .venv-ft2025/bin/activate
pip install -r requirements.txt

# Or use the auto-activation in ./project.sh (recommended)
./project.sh start

# Copy and edit configs
cp .env.example .env
cp config/agents.example.yaml config/agents.yaml
cp user_data/config.example.json user_data/config.json
nano .env
nano config/agents.yaml
nano user_data/config.json

# Run the main loop
python -m agents.self_loop_agent 'Full cycle loop' '' 100
```

---

## LLM Integration & Usage

> **LLM Helper:** All LLM requests and responses are logged for traceability. See `services/llm_client.py` for advanced usage and helper comments.

**Basic Example:**

```python
from services.llm_client import LLMClient, load_cfg
cfg = load_cfg()
llm = LLMClient(cfg)
print(llm.chat("You are a helpful trading assistant.", "Write a Freqtrade strategy that buys when RSI < 30."))
```

- LLM config: `config/agents.yaml`
- Prompts: `agents/strategy_lab.py`, `agents/self_loop_agent.py`

---

## Architecture & Directory Map

```
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
├── docs/                  # Documentation
├── ...
```

---

## Memory MCP Integration

### Overview

The project supports integration with a modular, in-memory Model Context Protocol (MCP) server for agent state sharing, rapid prototyping, and stateless workflows. The Memory MCP server is ideal for development and testing, allowing agents to store and retrieve context or results without persistent storage.

### Usage

- Start the Memory MCP server:

  ```bash
  ./scripts/start_memory_mcp.sh
  ```

- Use the modular Python client in your agents:

  ```python
  from agents.mcp_memory_client import MCPMemoryClient
  client = MCPMemoryClient()  # Defaults to http://localhost:8080
  client.put("key", {"foo": "bar"})
  value = client.get("key")
  client.delete("key")
  ```

### Logging & Documentation

- All interactions are logged using Python's logging module for traceability.
- The client is fully documented with docstrings and type hints.
- See `agents/mcp_memory_client.py` for details and example usage.

### Testing

- Run the test suite to verify integration:

  ```bash
  pytest tests/test_mcp_memory_client.py
  ```

- The test covers storing, retrieving, and deleting agent state in the Memory MCP server.

### Notes

- The Memory MCP server is for temporary, in-memory use only. Data is lost when the server stops.
- For persistent workflows, use a filesystem or database-backed MCP server.

### Agents

- **SelfLoopAgent**: Orchestrates the full research loop, ensures unique strategies, logs metrics, copies verified strategies.
- **StrategyLab**: Uses LLM to generate new strategies from prompts.
- **BacktestAgent**: Runs Freqtrade backtests, captures logs and metrics.
- **ImproveAgent**: Uses LLM to suggest code improvements based on backtest logs.
- **PatchUtils**: Provides safe patching, backup, and rollback for code changes.
- **WatchdogAgent, DependencyMedic, ErrorMedic**: Health monitoring and auto-healing.

### Services

- **HealingServer**: FastAPI server for health and healing endpoints.
- **LLMClient**: Handles LLM API calls (see `services/llm_client.py`).
- **Dashboard**: Web UI for monitoring.

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
  python -m agents.self_loop_agent 'Full cycle loop' '' 100
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
  `python -m agents.self_loop_agent 'Full cycle loop' '' 100`
- View learning log:  
  `cat user_data/learning_log.csv`
- See verified strategies:  
  `ls user_data/verified_strategies/`
- Start healing server:  
  `uvicorn services.healing_server:app --reload --port 8000`
- Run a backtest:  
  `bash scripts/run_backtest.sh`

---

## Troubleshooting

- See logs in `user_data/` and `services/`.
- Check `.env` and config files for correct endpoints and keys.
- Ensure `.venv-ft2025` exists and is activated.
- Use `make lint`, `make type`, `make test` for code quality.

---

## Contributing & Further Reading

- See code comments and docstrings for API details.
- For LLM prompt engineering, see `strategy_lab.py` and `self_loop_agent.py`.
- For user-level docs, see `docs/README.md` (if split).
- PRs welcome—CI must pass.

---

_This documentation is auto-generated and can be extended as your project evolves._

- Linting: `flake8`, `ruff`
