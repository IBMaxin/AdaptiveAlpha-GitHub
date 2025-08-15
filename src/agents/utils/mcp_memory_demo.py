"""
Memory MCP Client Demo
----------------------
Demonstrates advanced, production-quality usage of the modular MCPMemoryClient.
- Batch operations
- Logging
- Error handling
- Clean code and docstrings
"""

import logging
from typing import Any, Dict

from agents.mcp_memory_client import MCPMemoryClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_memory_demo")


def batch_store_and_retrieve(client: MCPMemoryClient, items: Dict[str, Any]) -> None:
    """
    Store multiple items, retrieve them, and clean up.
    Args:
        client (MCPMemoryClient): The memory client instance.
        items (Dict[str, Any]): Key-value pairs to store.
    """
    for key, value in items.items():
        if client.put(key, value):
            logger.info(f"Stored {key}: {value}")
        else:
            logger.error(f"Failed to store {key}")

    for key in items:
        value = client.get(key)
        if value is not None:
            logger.info(f"Retrieved {key}: {value}")
        else:
            logger.warning(f"{key} not found in memory MCP")

    for key in items:
        if client.delete(key):
            logger.info(f"Deleted {key}")
        else:
            logger.error(f"Failed to delete {key}")


if __name__ == "__main__":
    client = MCPMemoryClient()
    test_data: Dict[str, Any] = {
        "agent1_state": {"step": 1, "result": "ok"},
        "agent2_state": {"step": 2, "result": "fail"},
        "learning_params": {"roi": 0.03, "stoploss": -0.12},
    }
    batch_store_and_retrieve(client, test_data)
    logger.info("Memory MCP demo complete.")
