import logging
from pathlib import Path

# Log file path resolved dynamically
LOG_FILE = Path(__file__).resolve().parent / "syrixin.log"


logger = logging.getLogger(__name__)

FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

logging.basicConfig(
    format=FORMAT,
    filename=LOG_FILE,
    level=logging.INFO,
    encoding="utf-8",
)


def log_info(message: str) -> None:
    logger.info(message)


def log_warning(message: str) -> None:
    logger.warning(message)


def log_error(message: str) -> None:
    logger.error(message)


def clear_log_file() -> None:
    """Clear Syrixin's event log while keeping its file handler usable."""
    for handler in logging.getLogger().handlers:
        if not isinstance(handler, logging.FileHandler):
            continue
        if Path(handler.baseFilename).resolve() != LOG_FILE.resolve():
            continue

        handler.acquire()
        try:
            handler.flush()
            if handler.stream is not None:
                handler.stream.seek(0)
                handler.stream.truncate()
                handler.stream.flush()
            else:
                LOG_FILE.write_text("", encoding="utf-8")
        finally:
            handler.release()
        return

    # This fallback is useful when logging was configured by another caller.
    LOG_FILE.write_text("", encoding="utf-8")
