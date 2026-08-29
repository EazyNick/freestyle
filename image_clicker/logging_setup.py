import logging
import sys
from pathlib import Path


class LoggerFactory:
    def __init__(self, name: str = "image_clicker") -> None:
        self.name = name

    def create(self, log_file: Path) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        logger.addHandler(self._console_handler(formatter))
        logger.addHandler(self._file_handler(log_file, formatter))
        return logger

    def _console_handler(self, formatter: logging.Formatter) -> logging.Handler:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        return handler

    def _file_handler(self, log_file: Path, formatter: logging.Formatter) -> logging.Handler:
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(formatter)
        return handler
