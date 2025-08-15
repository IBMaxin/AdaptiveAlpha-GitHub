stance helper
"""
Automated LLM Server Verification and Patching System
Continuously monitors, verifies, and auto-heals the LLM setup.
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from llm_logger import LLMLogger

class LLMVerifier:
    """Continuous verification and auto-healing system."""
    
    def __init__(self):
        self.logger = LLMLogger(log_dir="logs/verifier")
        self.config_path = Path(".continue/mcpServers/new-mcp-server.yaml")
        self.last_verified = {}
        self.patch_history = []
        
    def continuous_verify(self, interval: int = 300) -> None:
        """Run continuous verification loop.
        
        Args:
            interval: Seconds between checks
        """
        self.logger.log_system("verifier_started", level="info")
        
        while True:
            try:
                self._run_verification_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.logger.log_system("verifier_stopped", level="info")
                break
            except Exception as e:
                self.logger.log_system(
                    "verification_error",
                    level="error",
                    error=str(e)
                )
                time.sleep(60)  # Back off on error
                
    def _run_verification_cycle(self) -> None:
        """Execute a single verification cycle."""
        # Check core services
        services_status = self._verify_services()
        self._handle_service_issues(services_status)
        
        # Verify configuration
        config_status = self._verify_configuration()
        self._handle_config_issues(config_status)
        
        # Check system resources
        resource_status = self._verify_resources()
        self._handle_resource_issues(resource_status)
        
        # Test model responses
        model_status = self._verify_model_responses()
        self._handle_model_issues(model_status)
        
        # Update verification state
        self._update_verification_state({
            "services": services_status,
            "config": config_status,
            "resources": resource_status,
            "model": model_status
        })
        
    def _verify_services(self) -> Dict[str, bool]:
        """Verify core services are running."""
        results = {}
        
        # Check API endpoint
        try:
            api_base = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
            subprocess.run(
                ["curl", "-s", f"{api_base}/health"],
                check=True,
                capture_output=True
            )
            results["api_endpoint"] = True
        except subprocess.CalledProcessError:
            results["api_endpoint"] = False
            
        # Check Python environment
        try:
            import torch
            results["python_env"] = True
        except ImportError:
            results["python_env"] = False
            
        return results
        
    def _verify_configuration(self) -> Dict[str, bool]:
        """Verify configuration is valid and complete."""
        results = {}
        
        # Check config file exists
        results["config_exists"] = self.config_path.exists()
        
        if results["config_exists"]:
            # Parse and validate YAML
            try:
                import yaml
                with open(self.config_path) as f:
                    config = yaml.safe_load(f)
                results["config_valid"] = True
                
                # Check required fields
                required_fields = ["name", "version", "schema", "mcpServers"]
                results["config_complete"] = all(
                    field in config for field in required_fields
                )
                
                # Validate environment variables
                env_vars = config["mcpServers"][0]["env"]
                results["env_vars_set"] = all(
                    os.getenv(var.strip("${}")) for var in env_vars.values()
                    if isinstance(var, str) and var.startswith("$")
                )
                
            except Exception:
                results["config_valid"] = False
                results["config_complete"] = False
                results["env_vars_set"] = False
                
        return results
        
    def _verify_resources(self) -> Dict[str, float]:
        """Verify system resources are adequate."""
        results = {}
        
        # Check memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            results["memory_available"] = memory.available / (1024 * 1024 * 1024)  # GB
            results["memory_percent"] = memory.percent
            
            # Check CPU
            results["cpu_percent"] = psutil.cpu_percent(interval=1)
            
            # Check disk
            disk = psutil.disk_usage(".")
            results["disk_free"] = disk.free / (1024 * 1024 * 1024)  # GB
            results["disk_percent"] = disk.percent
            
        except Exception as e:
            self.logger.log_system(
                "resource_check_error",
                level="error",
                error=str(e)
            )
            
        return results
        
    def _verify_model_responses(self) -> Dict[str, bool]:
        """Verify model responses are working correctly."""
        results = {}
        
        # Test model with simple prompt
        try:
            import requests
            api_base = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
            response = requests.post(
                f"{api_base}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": os.getenv("MODEL_NAME", "codellama:13b"),
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            
            results["model_responsive"] = response.status_code == 200
            if results["model_responsive"]:
                response_data = response.json()
                results["model_output_valid"] = (
                    "choices" in response_data and
                    len(response_data["choices"]) > 0 and
                    "message" in response_data["choices"][0]
                )
            else:
                results["model_output_valid"] = False
                
        except Exception as e:
            self.logger.log_system(
                "model_test_error",
                level="error",
                error=str(e)
            )
            results["model_responsive"] = False
            results["model_output_valid"] = False
            
        return results
        
    def _handle_service_issues(self, status: Dict[str, bool]) -> None:
        """Handle any service issues detected."""
        if not status["api_endpoint"]:
            self._attempt_service_restart("api")
            
        if not status["python_env"]:
            self._attempt_env_repair()
            
    def _handle_config_issues(self, status: Dict[str, bool]) -> None:
        """Handle any configuration issues detected."""
        if not status["config_exists"]:
            self._restore_config_backup()
            
        elif not status["config_valid"]:
            self._attempt_config_repair()
            
        elif not status["env_vars_set"]:
            self._notify_missing_env_vars()
            
    def _handle_resource_issues(self, status: Dict[str, float]) -> None:
        """Handle any resource issues detected."""
        # Memory warnings
        if status.get("memory_percent", 0) > 90:
            self.logger.log_system(
                "high_memory_usage",
                level="warning",
                memory_percent=status["memory_percent"]
            )
            
        # CPU warnings
        if status.get("cpu_percent", 0) > 80:
            self.logger.log_system(
                "high_cpu_usage",
                level="warning",
                cpu_percent=status["cpu_percent"]
            )
            
        # Disk warnings
        if status.get("disk_free", float("inf")) < 5:  # Less than 5GB free
            self.logger.log_system(
                "low_disk_space",
                level="warning",
                disk_free_gb=status["disk_free"]
            )
            
    def _handle_model_issues(self, status: Dict[str, bool]) -> None:
        """Handle any model issues detected."""
        if not status["model_responsive"]:
            self._attempt_model_reload()
            
        elif not status["model_output_valid"]:
            self._attempt_model_repair()
            
    def _attempt_service_restart(self, service: str) -> None:
        """Attempt to restart a failed service."""
        self.logger.log_system(
            f"restarting_{service}",
            level="warning"
        )
        
        try:
            if service == "api":
                # Try restarting the API service
                subprocess.run(
                    ["./scripts/llm_health_check.sh"],
                    check=True,
                    capture_output=True
                )
        except Exception as e:
            self.logger.log_system(
                f"{service}_restart_failed",
                level="error",
                error=str(e)
            )
            
    def _attempt_env_repair(self) -> None:
        """Attempt to repair Python environment."""
        self.logger.log_system("repairing_python_env", level="warning")
        
        try:
            # Run environment setup script
            subprocess.run(
                ["./scripts/setup_env.sh"],
                check=True,
                capture_output=True
            )
        except Exception as e:
            self.logger.log_system(
                "env_repair_failed",
                level="error",
                error=str(e)
            )
            
    def _restore_config_backup(self) -> None:
        """Attempt to restore configuration from backup."""
        self.logger.log_system("restoring_config", level="warning")
        
        backup_dir = Path("backups")
        if not backup_dir.exists():
            return
            
        # Find most recent backup
        backups = sorted(
            backup_dir.glob("config-*.tar.gz"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if backups:
            try:
                subprocess.run(
                    ["tar", "-xzf", str(backups[0])],
                    check=True,
                    capture_output=True
                )
                self.logger.log_system(
                    "config_restored",
                    level="info",
                    backup_file=str(backups[0])
                )
            except Exception as e:
                self.logger.log_system(
                    "config_restore_failed",
                    level="error",
                    error=str(e)
                )
                
    def _attempt_config_repair(self) -> None:
        """Attempt to repair invalid configuration."""
        self.logger.log_system("repairing_config", level="warning")
        
        try:
            # Load template config
            template_path = Path("templates/mcp-server-template.yaml")
            if template_path.exists():
                import shutil
                shutil.copy(template_path, self.config_path)
                self.logger.log_system("config_repaired", level="info")
        except Exception as e:
            self.logger.log_system(
                "config_repair_failed",
                level="error",
                error=str(e)
            )
            
    def _notify_missing_env_vars(self) -> None:
        """Log warning about missing environment variables."""
        self.logger.log_system(
            "missing_env_vars",
            level="warning",
            message="Some required environment variables are not set"
        )
        
    def _attempt_model_reload(self) -> None:
        """Attempt to reload the model."""
        self.logger.log_system("reloading_model", level="warning")
        
        try:
            # Send model reload request
            import requests
            api_base = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
            requests.post(
                f"{api_base}/reload",
                headers={"Content-Type": "application/json"},
                json={"model": os.getenv("MODEL_NAME", "codellama:13b")},
                timeout=30
            )
            self.logger.log_system("model_reloaded", level="info")
        except Exception as e:
            self.logger.log_system(
                "model_reload_failed",
                level="error",
                error=str(e)
            )
            
    def _attempt_model_repair(self) -> None:
        """Attempt to repair model issues."""
        self.logger.log_system("repairing_model", level="warning")
        
        try:
            # Try switching to fallback model
            fallback_model = os.getenv("FALLBACK_MODEL", "gpt4all")
            os.environ["MODEL_NAME"] = fallback_model
            self.logger.log_system(
                "switched_to_fallback",
                level="info",
                fallback_model=fallback_model
            )
        except Exception as e:
            self.logger.log_system(
                "model_repair_failed",
                level="error",
                error=str(e)
            )
            
    def _update_verification_state(self, state: Dict) -> None:
        """Update the verification state history."""
        timestamp = datetime.utcnow().isoformat()
        self.last_verified = {
            "timestamp": timestamp,
            "state": state
        }
        
        # Log state update
        self.logger.log_system(
            "verification_state_updated",
            level="info",
            **state
        )
        
if __name__ == "__main__":
    verifier = LLMVerifier()
    verifier.continuous_verify()