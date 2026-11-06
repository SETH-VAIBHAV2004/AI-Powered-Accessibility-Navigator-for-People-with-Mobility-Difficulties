import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(app):
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    app.logger.propagate = False
