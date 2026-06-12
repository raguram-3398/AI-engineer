from __future__ import annotations
from datetime import UTC, datetime

import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord,) -> str:
        log_data = {
            "timestamp": datetime.now(UTC,).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        return json.dumps(log_data)
    
def get_logger(name: str,) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger

def log_request(logger: logging.Logger, request_id: str, event: str, **kwargs: str | float | int | bool | None,) -> None:
    logger.info(event, extra={"extra_fields": {"request_id": request_id, **kwargs,}})