codebase """
Patch Verification and Application System.
Handles code reviews, patch application, and verification of changes.
"""

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from llm_logger import LLMLogger
from auto_verify import LLMVerifier
from ollama_api import OllamaAPI

@dataclass
class PatchResult:
    """Result of a patch application."""
    success: bool
    changes: List[str]
    errors: List[str]
    timestamp: str
    verification: Dict

class PatchVerifier:
    """Verifies and applies system patches with validation."""
    
    def __init__(self):
        self.logger = LLMLogger(log_dir="logs/patches")
        self.verifier = LLMVerifier()
        self.llm = OllamaAPI()
        self.patch_history: List[PatchResult] = []
        
    def verify_and_apply(self, patch_file: str) -> PatchResult:
        """Verify and apply a patch with full validation.
        
        Args:
            patch_file: Path to the patch file
        """
        timestamp = datetime.utcnow().isoformat()
        changes = []
        errors = []
        
        try:
            # 1. Initial state verification
            initial_state = self.verifier._get_verification()
            self.logger.log_system(
                "initial_verification",
                level="info",
                state=initial_state
            )
            
            # 2. Parse and validate patch
            patch_content = self._read_patch(patch_file)
            if not self._validate_patch(patch_content):
                raise ValueError("Invalid patch format")
                
            # 3. Apply patch
            success = self._apply_patch(patch_content)
            if success:
                changes.append(f"Applied patch: {patch_file}")
            else:
                errors.append(f"Failed to apply patch: {patch_file}")
                
            # 4. Verify after patch
            final_state = self.verifier._get_verification()
            
            # 5. Check for improvements
            if not self._verify_improvement(initial_state, final_state):
                self._rollback_changes()
                errors.append("Patch did not improve system state")
                success = False
                
            # 6. Update documentation
            if success:
                self._update_documentation(patch_file, changes)
                
            return PatchResult(
                success=success,
                changes=changes,
                errors=errors,
                timestamp=timestamp,
                verification=final_state
            )
            
        except Exception as e:
            self.logger.log_system(
                "patch_error",
                level="error",
                error=str(e)
            )
            return PatchResult(
                success=False,
                changes=changes,
                errors=[str(e)],
                timestamp=timestamp,
                verification=self.verifier._get_verification()
            )
            
    def _read_patch(self, patch_file: str) -> Dict:
        """Read and parse patch file."""
        try:
            with open(patch_file) as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to read patch file: {e}")
            
    def _validate_patch(self, patch: Dict) -> bool:
        """Validate patch format and content."""
        required_fields = ["description", "changes", "verification"]
        return all(field in patch for field in required_fields)
        
    def _apply_patch(self, patch: Dict) -> bool:
        """Apply the patch changes."""
        try:
            for change in patch["changes"]:
                if change["type"] == "file":
                    self._apply_file_change(change)
                elif change["type"] == "config":
                    self._apply_config_change(change)
                elif change["type"] == "env":
                    self._apply_env_change(change)
            return True
        except Exception as e:
            self.logger.log_system(
                "apply_failed",
                level="error",
                error=str(e)
            )
            return False
            
    def _verify_improvement(
        self,
        initial_state: Dict,
        final_state: Dict
    ) -> bool:
        """Verify system improved after patch."""
        # Check configuration
        if not all(final_state["config"].values()):
            return False
            
        # Check resources
        if (final_state["resources"].get("memory_percent", 100) >
            initial_state["resources"].get("memory_percent", 0)):
            return False
            
        # Check model
        if not all(final_state["model"].values()):
            return False
            
        return True
        
    def _rollback_changes(self) -> None:
        """Rollback applied changes."""
        self.logger.log_system("rolling_back", level="warning")
        try:
            # Execute rollback commands
            subprocess.run(
                ["git", "reset", "--hard"],
                check=True,
                capture_output=True
            )
            self.logger.log_system("rollback_complete", level="info")
        except Exception as e:
            self.logger.log_system(
                "rollback_failed",
                level="error",
                error=str(e)
            )
            
    def _update_documentation(self, patch_file: str, changes: List[str]) -> None:
        """Update documentation with patch details."""
        docs_dir = Path("docs")
        patches_doc = docs_dir / "PATCHES.md"
        
        with open(patches_doc, "a") as f:
            f.write(f"\n## Patch Applied: {datetime.now()}\n")
            f.write(f"Source: {patch_file}\n")
            f.write("\nChanges:\n")
            for change in changes:
                f.write(f"- {change}\n")
                
    def _apply_file_change(self, change: Dict) -> None:
        """Apply changes to a file."""
        file_path = Path(change["path"])
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if change["operation"] == "modify":
            with open(file_path, "r") as f:
                content = f.read()
            new_content = self._apply_modifications(
                content,
                change["modifications"]
            )
            with open(file_path, "w") as f:
                f.write(new_content)
                
        elif change["operation"] == "create":
            with open(file_path, "w") as f:
                f.write(change["content"])
                
    def _apply_config_change(self, change: Dict) -> None:
        """Apply changes to configuration."""
        import yaml
        config_path = Path(".continue/mcpServers/new-mcp-server.yaml")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Apply changes
        for key, value in change["updates"].items():
            if isinstance(value, dict):
                config.setdefault(key, {}).update(value)
            else:
                config[key] = value
                
        with open(config_path, "w") as f:
            yaml.dump(config, f)
            
    def _apply_env_change(self, change: Dict) -> None:
        """Apply environment variable changes."""
        env_file = Path(".env")
        
        # Read existing env vars
        env_vars = {}
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value
                        
        # Apply updates
        env_vars.update(change["variables"])
        
        # Write back
        with open(env_file, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
                
    def _apply_modifications(self, content: str, mods: List[Dict]) -> str:
        """Apply text modifications to content."""
        for mod in mods:
            if mod["type"] == "replace":
                content = content.replace(
                    mod["search"],
                    mod["replace"]
                )
            elif mod["type"] == "insert":
                content = content[:mod["position"]] + mod["text"] + content[mod["position"]:]
                
        return content
        
if __name__ == "__main__":
    # Example usage
    verifier = PatchVerifier()
    
    # Test patch application
    test_patch = {
        "description": "Update model configuration",
        "changes": [
            {
                "type": "config",
                "updates": {
                    "MODEL_NAME": "codellama:20b",
                    "MEMORY_LIMIT": "16384"
                }
            }
        ],
        "verification": ["config", "model"]
    }
    
    with open("test_patch.json", "w") as f:
        json.dump(test_patch, f, indent=2)
        
    result = verifier.verify_and_apply("test_patch.json")
    print(f"Patch applied: {result.success}")
    print(f"Changes: {result.changes}")
    print(f"Errors: {result.errors}")
    print(f"Verification: {result.verification}")