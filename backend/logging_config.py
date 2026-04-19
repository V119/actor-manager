import logging
from logging.handlers import WatchedFileHandler
from pathlib import Path

from backend.config import get_config, get_trace_id


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        return True


def setup_logging_config() -> None:
    level = str(get_config("logging.level", "INFO")).upper()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(threadName)s] [%(filename)s:%(lineno)d] [%(name)s] [%(trace_id)s]: %(message)s"
    )
    trace_filter = TraceIdFilter()
    handlers: list[logging.Handler] = []

    if bool(get_config("logging.file.also_stdout", True)):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(trace_filter)
        handlers.append(stream_handler)

    file_enabled = bool(get_config("logging.file.enabled", False))
    file_path = str(get_config("logging.file.path", "") or "").strip()
    if file_enabled and file_path:
        log_file = Path(file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = WatchedFileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)
        handlers.append(file_handler)

    if not handlers:
        fallback_handler = logging.StreamHandler()
        fallback_handler.setFormatter(formatter)
        fallback_handler.addFilter(trace_filter)
        handlers.append(fallback_handler)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.filters.clear()
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(level)
    root_logger.addFilter(trace_filter)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(level)
        logger.addFilter(trace_filter)
        logger.propagate = True
