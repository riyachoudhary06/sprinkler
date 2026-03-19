"""
utils/logger.py — Configure rotating file + console logging.
"""
import logging
import logging.handlers
import os


def setup_logger(log_dir: str = "/home/pi/logs", level: str = "INFO"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "agriwatch.log")

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("paho").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
