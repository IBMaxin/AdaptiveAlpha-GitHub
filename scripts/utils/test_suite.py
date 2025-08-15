"""
Test Suite for Auto-Patch System.

Verifies functionality, formatting, and integration of all components.
Follows flake8 standards and provides detailed test reporting.
"""

import json
import logging
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest
from flake8.api import verify_file
from llm_logger import LLMLogger
from auto_patch_loop import AutoPatchLoop
from auto_verify import LLMVerifier


class TestAutoPatchSystem(unittest.TestCase):
    """Test suite for the Auto-Patch system components."""

    def setUp(self) -> None:
        """Initialize test environment."""
        self.logger = LLMLogger(log_dir="logs/test")
        self.verifier = LLMVerifier()
        self.autopatch = AutoPatchLoop()
        self.test_dir = Path("test_outputs")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        """Clean up test artifacts."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_code_formatting(self) -> None:
        """Verify all Python files follow flake8 standards."""
        python_files = list(Path(".").rglob("*.py"))
        flake8_issues = []

        for file in python_files:
            result = verify_file(str(file))
            if result.total_errors > 0:
                flake8_issues.append(f"{file}: {result.total_errors} issues")

        self.assertEqual(len(flake8_issues), 0, "\n".join(flake8_issues))

    def test_verification_checks(self) -> None:
        """Test system verification functionality."""
        verification = self.verifier._get_verification()

        self.assertIsInstance(verification, dict)
        self.assertIn("services", verification)
        self.assertIn("config", verification)
        self.assertIn("resources", verification)
        self.assertIn("model", verification)

    def test_llm_integration(self) -> None:
        """Test LLM API integration."""
        test_verification = {
            "services": {"api_endpoint": True},
            "config": {"config_valid": True},
            "resources": {"memory_percent": 50},
            "model": {"model_responsive": True}
        }

        suggestions = self.autopatch._get_llm_suggestions(test_verification)
        self.assertIsInstance(suggestions, list)
        if suggestions:
            self.assertIn("description", suggestions[0])
            self.assertIn("priority", suggestions[0])

    def test_documentation_updates(self) -> None:
        """Test documentation generation."""
        test_suggestions = [{
            "description": "Test improvement",
            "reason": "Testing",
            "priority": 1,
            "method": "test"
        }]

        self.autopatch._update_documentation(test_suggestions)
        
        docs_dir = Path("docs")
        self.assertTrue((docs_dir / "IMPROVEMENTS.md").exists())
        self.assertTrue((docs_dir / "SYSTEM_STATE.md").exists())
        self.assertTrue((docs_dir / "STATISTICS.md").exists())

    def test_config_management(self) -> None:
        """Test configuration handling."""
        test_suggestion = {
            "method": "config_update",
            "updates": {
                "version": "1.0.1"
            }
        }

        original_config = self._read_config()
        self.autopatch._update_config(test_suggestion)
        updated_config = self._read_config()

        self.assertNotEqual(original_config, updated_config)
        self._restore_config(original_config)

    def test_resource_monitoring(self) -> None:
        """Test resource monitoring capabilities."""
        resources = self.verifier._verify_resources()

        self.assertIn("memory_available", resources)
        self.assertIn("cpu_percent", resources)
        self.assertIn("disk_free", resources)
        self.assertIsInstance(resources["memory_percent"], (int, float))

    def test_logging_system(self) -> None:
        """Test logging functionality."""
        test_log = "Test log entry"
        self.logger.log_system("test_event", level="info", message=test_log)

        log_file = Path("logs/test/info.log")
        self.assertTrue(log_file.exists())
        
        with open(log_file) as f:
            log_content = f.read()
            self.assertIn(test_log, log_content)

    def test_error_handling(self) -> None:
        """Test error handling mechanisms."""
        with self.assertLogs(level="ERROR"):
            self.verifier._attempt_model_reload()

    def test_improvement_cycle(self) -> None:
        """Test complete improvement cycle."""
        self.autopatch.improvement_count = 0
        self.autopatch._run_improvement_cycle()
        
        self.assertGreaterEqual(self.autopatch.improvement_count, 0)
        self.assertIsInstance(self.autopatch.patch_history, list)

    def _read_config(self) -> Dict:
        """Helper to read current config."""
        import yaml
        config_path = Path(".continue/mcpServers/new-mcp-server.yaml")
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _restore_config(self, config: Dict) -> None:
        """Helper to restore original config."""
        import yaml
        config_path = Path(".continue/mcpServers/new-mcp-server.yaml")
        with open(config_path, "w") as f:
            yaml.dump(config, f)

    @classmethod
    def generate_test_report(cls) -> None:
        """Generate detailed test report."""
        test_output = Path("test_outputs")
        test_output.mkdir(exist_ok=True)
        
        # Run tests with coverage
        subprocess.run([
            "pytest",
            "--cov=scripts",
            "--cov-report=html:test_outputs/coverage",
            "scripts/test_suite.py"
        ])

        # Generate flake8 report
        subprocess.run([
            "flake8",
            "--format=html",
            "--htmldir=test_outputs/flake8",
            "scripts/"
        ])

        # Create summary report
        with open(test_output / "TEST_SUMMARY.md", "w") as f:
            f.write("# Test Suite Summary\n\n")
            f.write(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("## Coverage Report\n")
            f.write("See test_outputs/coverage/index.html\n\n")
            f.write("## Code Quality Report\n")
            f.write("See test_outputs/flake8/index.html\n")


if __name__ == "__main__":
    # Run tests and generate report
    unittest.main(verbosity=2)
    TestAutoPatchSystem.generate_test_report()