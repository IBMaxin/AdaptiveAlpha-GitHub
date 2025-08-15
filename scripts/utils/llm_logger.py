"""
LLM Server Logging Module
Handles structured logging for the LLM server with rotating files and monitoring.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class LLMLogger:
    """Structured logger for LLM server operations."""
    
    def __init__(
        self,
        log_dir: str = "logs",
        max_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """Initialize the logger with rotation and structured format.
        
        Args:
            log_dir: Directory to store log files
            max_size: Maximum size of each log file
            backup_count: Number of backup files to keep
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup handlers
        self._setup_handlers(max_size, backup_count)
        
        # Track metrics
        self.request_count = 0
        self.error_count = 0
        self.total_tokens = 0
        
    def _setup_handlers(self, max_size: int, backup_count: int) -> None:
        """Configure logging handlers for different log levels."""
        # Main logger
        self.logger = logging.getLogger("llm_server")
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        handlers = {
            "error": self._create_handler("error.log", logging.ERROR, max_size, backup_count),
            "info": self._create_handler("info.log", logging.INFO, max_size, backup_count),
            "debug": self._create_handler("debug.log", logging.DEBUG, max_size, backup_count)
        }
        
        # Add handlers to logger
        for handler in handlers.values():
            self.logger.addHandler(handler)
            
    def _create_handler(
        self,
        filename: str,
        level: int,
        max_size: int,
        backup_count: int
    ) -> logging.Handler:
        """Create a rotating file handler with JSON formatting."""
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=max_size,
            backupCount=backup_count
        )
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '{"timestamp":"%(asctime)s", "level":"%(levelname)s", '
            '"event":"%(message)s", "data":%(data)s}'
        )
        handler.setFormatter(formatter)
        return handler
        
    def log_request(
        self,
        model: str,
        tokens: int,
        duration_ms: int,
        error: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Log an LLM request with metrics."""
        data = {
            "model": model,
            "tokens": tokens,
            "duration_ms": duration_ms,
            **kwargs
        }
        
        if error:
            self.error_count += 1
            data["error"] = error
            self.logger.error("request_error", extra={"data": json.dumps(data)})
        else:
            self.request_count += 1
            self.total_tokens += tokens
            self.logger.info("request_complete", extra={"data": json.dumps(data)})
            
    def log_system(
        self,
        event: str,
        level: str = "info",
        **kwargs: Any
    ) -> None:
        """Log system events and metrics."""
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        getattr(self.logger, level)(event, extra={"data": json.dumps(data)})
        
    def get_metrics(self) -> Dict[str, Any]:
        """Return current logging metrics."""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "total_tokens": self.total_tokens,
            "error_rate": self.error_count / max(self.request_count, 1),
            "avg_tokens": self.total_tokens / max(self.request_count, 1)
        }
        
    def rotate_logs(self) -> None:
        """Force rotation of all log files."""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()
                
    def cleanup_old_logs(self, days: int = 30) -> None:
        """Remove log files older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for file in self.log_dir.glob("*.log.*"):
            if file.stat().st_mtime < cutoff:
                file.unlink()

# Example usage
if __name__ == "__main__":
    logger = LLMLogger()
    
    # Log successful request
    logger.log_request(
        model="codellama:13b",
        tokens=512,
        duration_ms=1234,
        prompt_tokens=128,
        completion_tokens=384
    )
    
    # Log error request
    logger.log_request(
        model="codellama:13b",
        tokens=0,
        duration_ms=500,
        error="Model not loaded",
        prompt="test prompt"
    )
    
    # Log system event
    logger.log_system(
        "model_loaded",
        level="info",
        model="codellama:13b",
        load_time_ms=5000
    )
    
    # Print metrics
    print("Metrics:", logger.get_metrics())