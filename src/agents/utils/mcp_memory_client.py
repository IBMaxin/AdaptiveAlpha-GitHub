
"""
Memory MCP Client
-----------------
A modular, logged, and documented client for interacting with the Memory MCP server.
"""

import logging
from typing import Any, Optional
import requests

logger = logging.getLogger("mcp_memory_client")
logging.basicConfig(level=logging.INFO)


class MCPMemoryClient:
    """
    Client for interacting with the Memory MCP server over HTTP.
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        logger.info(f"MCPMemoryClient initialized with base_url={self.base_url}")

    def put(self, key: str, value: Any) -> bool:
        """Store a value in the memory server under the given key."""
        try:
            resp = requests.post(
                f"{self.base_url}/put", json={"key": key, "value": value}
            )
            resp.raise_for_status()
            logger.info(f"PUT {key}: {value}")
            return True
        except Exception as e:
            logger.error(f"PUT failed for {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the memory server by key."""
        try:
            resp = requests.get(f"{self.base_url}/get", params={"key": key})
            resp.raise_for_status()
            value = resp.json().get("value")
            logger.info(f"GET {key}: {value}")
            return value
        except Exception as e:
            logger.error(f"GET failed for {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a value from the memory server by key."""
        try:
            resp = requests.post(f"{self.base_url}/delete", json={"key": key})
            resp.raise_for_status()
            logger.info(f"DELETE {key}")
            return True
        except Exception as e:
            logger.error(f"DELETE failed for {key}: {e}")
            return False
