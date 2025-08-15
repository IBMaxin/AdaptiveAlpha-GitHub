"""
Test for MCPMemoryClient
-----------------------
This test demonstrates optimal usage of the Memory MCP server client:
- Modular usage
- Logging
- Clean up
- Documentation
- Flake8/black formatting
"""
import logging

import pytest

from agents.mcp_memory_client import MCPMemoryClient

logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="module")
def mcp_client():
    # Assumes Memory MCP server is running at default URL
    return MCPMemoryClient()

def test_put_get_delete(mcp_client):
    """Test storing, retrieving, and deleting a value optimally."""
    key = "test_optimal_key"
    value = {"strategy": "SmaRsi_v2", "params": {"roi": 0.02, "stoploss": -0.1}}

    # Store value
    assert mcp_client.put(key, value) is True
    # Retrieve value
    retrieved = mcp_client.get(key)
    assert retrieved == value
    # Delete value
    assert mcp_client.delete(key) is True
    # Confirm deletion
    assert mcp_client.get(key) is None



    # Update data
    data["score"] = 1.23
    assert client.put(key, data), "Failed to update data"
    updated = client.get(key)
    assert updated["score"] == 1.23, "Update did not persist"
    print(f"Updated: {updated}")

    # Delete data
    assert client.delete(key), "Failed to delete data"
    assert client.get(key) is None, "Data was not deleted"
    print("Delete confirmed.")

if __name__ == "__main__":
    test_memory_client()
    print("MCPMemoryClient optimal usage test complete.")
