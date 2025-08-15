"""
Continuous Auto-Patching Loop with LLM Assistance
Monitors, verifies, patches, and documents system improvements automatically.
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
from auto_verify import LLMVerifier

class AutoPatchLoop:
    """Continuous improvement system with LLM assistance."""
    
    def __init__(self):
        self.logger = LLMLogger(log_dir="logs/autopatch")
        self.verifier = LLMVerifier()
        self.docs_dir = Path("docs")
        self.patch_history = []
        self.improvement_count = 0
        
    def run_forever(self, interval: int = 600) -> None:
        """Run continuous improvement loop forever.
        
        Args:
            interval: Seconds between improvement cycles
        """
        self.logger.log_system("autopatch_started", level="info")
        
        while True:
            try:
                self._run_improvement_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.logger.log_system("autopatch_stopped", level="info")
                break
            except Exception as e:
                self.logger.log_system(
                    "improvement_error",
                    level="error",
                    error=str(e)
                )
                time.sleep(120)  # Back off on error
                
    def _run_improvement_cycle(self) -> None:
        """Execute a single improvement cycle."""
        # Verify current state
        verification = self._get_verification()
        
        # Check if improvements needed
        if self._needs_improvement(verification):
            # Get LLM suggestions
            suggestions = self._get_llm_suggestions(verification)
            
            # Apply improvements
            success = self._apply_improvements(suggestions)
            
            if success:
                # Update documentation
                self._update_documentation(suggestions)
                
                # Log improvement
                self.improvement_count += 1
                self._log_improvement(suggestions)
                
    def _get_verification(self) -> Dict:
        """Run verification and return results."""
        try:
            # Run verifier checks
            services = self.verifier._verify_services()
            config = self.verifier._verify_configuration()
            resources = self.verifier._verify_resources()
            model = self.verifier._verify_model_responses()
            
            return {
                "services": services,
                "config": config,
                "resources": resources,
                "model": model,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.log_system(
                "verification_failed",
                level="error",
                error=str(e)
            )
            return {}
            
    def _needs_improvement(self, verification: Dict) -> bool:
        """Check if system needs improvements."""
        if not verification:
            return False
            
        # Check for any failed verifications
        services_ok = all(verification.get("services", {}).values())
        config_ok = all(verification.get("config", {}).values())
        model_ok = all(verification.get("model", {}).values())
        
        # Check resource thresholds
        resources = verification.get("resources", {})
        resources_ok = (
            resources.get("memory_percent", 0) < 80 and
            resources.get("cpu_percent", 0) < 70 and
            resources.get("disk_free", float("inf")) > 10
        )
        
        return not (services_ok and config_ok and model_ok and resources_ok)
        
    def _get_llm_suggestions(self, verification: Dict) -> List[Dict]:
        """Get improvement suggestions from LLM."""
        try:
            import requests
            
            # Prepare system state description
            state_desc = json.dumps(verification, indent=2)
            
            # Prepare prompt for LLM
            prompt = f"""
            System State:
            {state_desc}
            
            Analyze the system state and suggest improvements.
            Format your response as a JSON list of improvement actions.
            Each action should have:
            - description: What needs to be done
            - reason: Why it's needed
            - priority: 1-5 (1 highest)
            - method: How to implement
            """
            
            # Call LLM API
            api_base = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
            response = requests.post(
                f"{api_base}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": os.getenv("MODEL_NAME", "codellama:13b"),
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                },
                timeout=30
            )
            
            suggestions = json.loads(response.json()["choices"][0]["message"]["content"])
            return sorted(suggestions, key=lambda x: x["priority"])
            
        except Exception as e:
            self.logger.log_system(
                "llm_suggestion_failed",
                level="error",
                error=str(e)
            )
            return []
            
    def _apply_improvements(self, suggestions: List[Dict]) -> bool:
        """Apply suggested improvements."""
        try:
            for suggestion in suggestions:
                self.logger.log_system(
                    "applying_improvement",
                    level="info",
                    suggestion=suggestion
                )
                
                # Apply based on method
                method = suggestion["method"]
                if method == "config_update":
                    self._update_config(suggestion)
                elif method == "service_restart":
                    self._restart_service(suggestion)
                elif method == "resource_optimization":
                    self._optimize_resources(suggestion)
                elif method == "model_adjustment":
                    self._adjust_model(suggestion)
                    
            return True
            
        except Exception as e:
            self.logger.log_system(
                "improvement_application_failed",
                level="error",
                error=str(e)
            )
            return False
            
    def _update_documentation(self, suggestions: List[Dict]) -> None:
        """Update documentation with improvements."""
        try:
            # Update improvement log
            improve_log = self.docs_dir / "IMPROVEMENTS.md"
            with open(improve_log, "a") as f:
                f.write(f"\n## Improvements {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                for suggestion in suggestions:
                    f.write(f"\n### {suggestion['description']}\n")
                    f.write(f"- Reason: {suggestion['reason']}\n")
                    f.write(f"- Priority: {suggestion['priority']}\n")
                    f.write(f"- Method: {suggestion['method']}\n")
                    
            # Update system state doc
            state_doc = self.docs_dir / "SYSTEM_STATE.md"
            verification = self._get_verification()
            with open(state_doc, "w") as f:
                f.write("# Current System State\n\n")
                f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                f.write("```json\n")
                f.write(json.dumps(verification, indent=2))
                f.write("\n```\n")
                
            # Update statistics
            stats_doc = self.docs_dir / "STATISTICS.md"
            with open(stats_doc, "w") as f:
                f.write("# System Statistics\n\n")
                f.write(f"Total Improvements: {self.improvement_count}\n")
                f.write(f"Last Improvement: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                
        except Exception as e:
            self.logger.log_system(
                "documentation_update_failed",
                level="error",
                error=str(e)
            )
            
    def _log_improvement(self, suggestions: List[Dict]) -> None:
        """Log improvement details."""
        self.patch_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "suggestions": suggestions,
            "improvement_number": self.improvement_count
        })
        
        self.logger.log_system(
            "improvement_complete",
            level="info",
            improvement_count=self.improvement_count,
            suggestions=suggestions
        )
        
    def _update_config(self, suggestion: Dict) -> None:
        """Update configuration based on suggestion."""
        import yaml
        config_path = Path(".continue/mcpServers/new-mcp-server.yaml")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Apply suggested changes
        if "updates" in suggestion:
            for key, value in suggestion["updates"].items():
                if key in config:
                    config[key] = value
                    
        with open(config_path, "w") as f:
            yaml.dump(config, f)
            
    def _restart_service(self, suggestion: Dict) -> None:
        """Restart specified service."""
        service = suggestion.get("service_name")
        if service:
            subprocess.run(
                ["./scripts/llm_health_check.sh"],
                check=True,
                capture_output=True
            )
            
    def _optimize_resources(self, suggestion: Dict) -> None:
        """Apply resource optimization."""
        import psutil
        
        # Clear system caches if needed
        if suggestion.get("clear_cache"):
            subprocess.run(["sync"])
            with open("/proc/sys/vm/drop_caches", "w") as f:
                f.write("3")
                
        # Adjust process priorities if needed
        if suggestion.get("adjust_priority"):
            current_process = psutil.Process()
            current_process.nice(10)
            
    def _adjust_model(self, suggestion: Dict) -> None:
        """Adjust model settings."""
        if "model_name" in suggestion:
            os.environ["MODEL_NAME"] = suggestion["model_name"]
            
        if "parameters" in suggestion:
            for key, value in suggestion["parameters"].items():
                os.environ[key] = str(value)
                
if __name__ == "__main__":
    autopatch = AutoPatchLoop()
    autopatch.run_forever()