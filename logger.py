```python
"""
Structured logger – JSONL, daily rotation
"""
from __future__ import annotations
import json
import logging
import logging.handlers
import datetime as dt
import pathlib
import uuid

# Define log directory
LOG_DIR = pathlib.Path(__file__).with_suffix("").parent / "log"
LOG_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        base = {
            "ts": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
        }
        if record.args:
            base["data"] = record.args
        return json.dumps(base, ensure_ascii=False)

# Set up the logger
_handler = logging.handlers.TimedRotatingFileHandler(
    LOG_DIR / "run.jsonl", when="midnight", backupCount=14, encoding="utf-8"
)
_handler.setFormatter(JSONFormatter())
LOGGER = logging.getLogger("vendo_sync")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(_handler)

# Convenience functions -----------------------------------------------------

def event_to_dict(ev: dict) -> dict:
    """Convert event dictionary to a simplified format."""
    return {
        "id": ev.get("id"),
        "summary": ev.get("summary"),
        "start": ev["start"],
        "end": ev["end"],
        "color": ev.get("colorId"),
    }

def log_run_snapshot(label: str, payload: dict) -> None:
    """Log a snapshot of the run with a label and payload."""
    LOGGER.info(label, payload)

def new_run_id() -> str:
    """Generate a new unique run ID."""
    return uuid.uuid4().hex[:8]
```