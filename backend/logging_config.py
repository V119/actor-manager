import logging

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
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(trace_filter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.setLevel(level)
    root_logger.addFilter(trace_filter)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(level)
        logger.addFilter(trace_filter)
        logger.propagate = True
