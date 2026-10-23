import logging
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler

from app.config import BASE_PATH, BACKUP_COUNT, LOG_MAX_BYTES

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get()
        return True


LOG_DIR = BASE_PATH / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] "
        "request_id=%(request_id)s %(message)s"
    )
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

for handler in logger.handlers:
    if not any(isinstance(item, RequestIdFilter) for item in handler.filters):
        handler.addFilter(RequestIdFilter())

logger.propagate = False
