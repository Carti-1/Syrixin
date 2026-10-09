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
