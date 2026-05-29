"""
Logging setup.
==============
Provides a single get_logger() helper so every module logs consistently to
both the console and a rotating file in logs/crew_demo.log.

CrewAI itself emits verbose output when verbose=True on agents/crew; this
logger is for OUR application code so you can trace exactly what is happening.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "crew_demo.log")

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-18s | %(message)s"
_configured = False


def _configure_root() -> None:
    global _configured
    if _configured:
        return

    formatter = logging.Formatter(_FORMAT, datefmt="%H:%M:%S")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger that writes to console + file."""
    _configure_root()
    return logging.getLogger(name)
