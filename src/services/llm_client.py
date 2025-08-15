"""
services.llm_client: LLMClient and load_cfg implementation

Loads LLM config from config/agents.yaml and provides a robust OpenAI-compatible LLM client.
All requests and responses are logged to user_data/llm_client.log.
Flake8 and Black compliant.

USAGE EXAMPLES:
----------------
from services.llm_client import LLMClient, load_cfg

# Load config (auto-expands env vars in config/agents.yaml)
cfg = load_cfg()

# Create LLM client
llm = LLMClient(cfg)

# Send a chat prompt
system = "You are a helpful trading assistant."
user = "Write a Freqtrade strategy that buys when RSI < 30."
response = llm.chat(system, user)
print(response)

# All requests and responses are logged to user_data/llm_client.log

HELPER NOTES:
-------------
- Supports any OpenAI-compatible API (LM Studio, OpenRouter, OpenAI, etc).
- Requires config/agents.yaml with an 'llm' section (see repo docs for template).
- Expands env vars in config (e.g., ${OPENAI_API_KEY}).
- Raises ValueError if config is missing required fields.
- Raises and logs exceptions for HTTP or API errors.
- All logs are timestamped and include system/user prompts and responses.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import yaml

CONFIG_PATH = Path("config/agents.yaml")
LOG_PATH = Path("user_data/llm_client.log")


def load_cfg() -> dict[str, Any]:
    """Load LLM config from config/agents.yaml, with env var expansion."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    llm_cfg = config.get("llm", {})
    # Expand env vars in config values
    for k, v in llm_cfg.items():
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_key = v[2:-1]
            llm_cfg[k] = os.environ.get(env_key, v)
    return llm_cfg


class LLMClient:
    """OpenAI-compatible LLM client (supports LM Studio, OpenRouter, OpenAI, etc)."""

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.base_url = cfg.get("base_url")
        self.model = cfg.get("model")
        self.api_key = cfg.get("api_key")
        self.temperature = cfg.get("temperature", 0.7)
        self.top_p = cfg.get("top_p", 0.95)
        self.max_tokens = cfg.get("max_tokens", 1024)
        if not self.base_url or not self.model or not self.api_key:
            raise ValueError("LLM config missing base_url, model, or api_key")

    def chat(self, system: str, user: str) -> str:
        """Send a chat completion request and return the LLM's response (as string)."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }
        ts = datetime.now().isoformat()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            # OpenAI-compatible: choices[0].message.content
            content = data["choices"][0]["message"]["content"]
            self._log(ts, system, user, content)
            return content
        except Exception as e:
            self._log(ts, system, user, f"[ERROR] {e}")
            raise

    def _log(self, ts: str, system: str, user: str, response: str) -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(
                f"\n---\nTIMESTAMP: {ts}\nSYSTEM:\n{system}\nUSER:\n{user}\nRESPONSE:\n{response}\n"
            )
