
"""
Memory MCP Client
-----------------
A modular, logged, and documented client for interacting with memory storage.
Falls back to file-based storage when MCP server is unavailable.
"""

import json
import logging
import os
from typing import Any, Optional
from pathlib import Path

logger = logging.getLogger("mcp_memory_client")
logging.basicConfig(level=logging.INFO)


class MCPMemoryClient:
    """
    Client for interacting with memory storage.
    Uses file-based storage as primary method since MCP memory server
    is designed for different integration patterns.
    """

    def __init__(self, storage_path: str = "user_data/agent_memory.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"MCPMemoryClient initialized with storage_path={self.storage_path}")
        
        # Initialize storage file if it doesn't exist
        if not self.storage_path.exists():
            self._save_data({})

    def _load_data(self) -> dict:
        """Load data from storage file."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load data: {e}")
            return {}

    def _save_data(self, data: dict) -> bool:
        """Save data to storage file."""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False

    def put(self, key: str, value: Any) -> bool:
        """Store a value in memory under the given key."""
        try:
            data = self._load_data()
            data[key] = value
            success = self._save_data(data)
            if success:
                logger.info(f"PUT {key}: {value}")
            return success
        except Exception as e:
            logger.error(f"PUT failed for {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory by key."""
        try:
            data = self._load_data()
            value = data.get(key)
            logger.info(f"GET {key}: {value}")
            return value
        except Exception as e:
            logger.error(f"GET failed for {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a value from memory by key."""
        try:
            data = self._load_data()
            if key in data:
                del data[key]
                success = self._save_data(data)
                if success:
                    logger.info(f"DELETE {key}")
                return success
            else:
                logger.info(f"DELETE {key}: key not found")
                return True  # Consider non-existent key as successful deletion
        except Exception as e:
            logger.error(f"DELETE failed for {key}: {e}")
            return False

    def append(self, key: str, value: Any) -> bool:
        """Append a value to a list stored under the given key."""
        try:
            data = self._load_data()
            if key not in data:
                data[key] = []
            elif not isinstance(data[key], list):
                data[key] = [data[key]]  # Convert to list if not already
            
            data[key].append(value)
            success = self._save_data(data)
            if success:
                logger.info(f"APPEND {key}: {value}")
            return success
        except Exception as e:
            logger.error(f"APPEND failed for {key}: {e}")
            return False

    def get_all_keys(self) -> list:
        """Get all keys in memory."""
        try:
            data = self._load_data()
            keys = list(data.keys())
            logger.info(f"GET_ALL_KEYS: {keys}")
            return keys
        except Exception as e:
            logger.error(f"GET_ALL_KEYS failed: {e}")
            return []
