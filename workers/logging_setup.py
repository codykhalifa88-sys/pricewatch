import logging
from datetime import date
from pathlib import Path

from backend.config import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_dir / f"{name}_{date.today().isoformat()}.log")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
