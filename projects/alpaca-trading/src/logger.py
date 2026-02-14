"""Structured JSON logging for the trading system."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class TradingLogger:
    """JSON Lines logger with daily file rotation."""
    
    def __init__(self, log_dir: str | Path | None = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_log_file(self) -> Path:
        """Get today's log file path."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{today}.jsonl"
    
    def _write_log(self, level: str, event: str, data: dict[str, Any] | None = None) -> None:
        """Write a log entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "event": event,
            "data": data or {}
        }
        
        log_file = self._get_log_file()
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def info(self, event: str, data: dict[str, Any] | None = None) -> None:
        """Log info level event."""
        self._write_log("INFO", event, data)
    
    def warning(self, event: str, data: dict[str, Any] | None = None) -> None:
        """Log warning level event."""
        self._write_log("WARNING", event, data)
    
    def error(self, event: str, data: dict[str, Any] | None = None) -> None:
        """Log error level event."""
        self._write_log("ERROR", event, data)
    
    def log_trade(self, trade_data: dict[str, Any]) -> None:
        """Log a trade execution."""
        self.info("trade_executed", trade_data)
    
    def log_signal(self, signal_data: dict[str, Any], action: str = "generated") -> None:
        """Log a trade signal."""
        self.info(f"signal_{action}", signal_data)
    
    def log_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Log an error with context."""
        import traceback
        tb_str = traceback.format_exc()
        data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_traceback": tb_str,
            "context": context or {}
        }
        self.error("exception", data)
    
    def log_daily_summary(self, summary: dict[str, Any]) -> None:
        """Log end of day summary."""
        self.info("daily_summary", summary)
    
    def log_startup(self, config: dict[str, Any] | None = None) -> None:
        """Log system startup."""
        self.info("system_startup", config or {})
    
    def log_shutdown(self, reason: str = "normal") -> None:
        """Log system shutdown."""
        self.info("system_shutdown", {"reason": reason})


# Convenience function for quick status file updates
def write_status(status: dict[str, Any], status_dir: str | Path | None = None) -> None:
    """Write current status to status.json for agent monitoring."""
    if status_dir is None:
        status_dir = Path(__file__).parent.parent / "logs"
    
    status_file = Path(status_dir) / "status.json"
    status["timestamp"] = datetime.now().isoformat()
    
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)


if __name__ == "__main__":
    # Quick test
    logger = TradingLogger()
    logger.log_startup({"version": "0.1.0"})
    logger.log_trade({"symbol": "AAPL", "side": "buy", "qty": 1.0})
    print(f"Log written to {logger._get_log_file()}")
