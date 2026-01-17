"""Logging helpers for the Flask app."""

from __future__ import annotations

import logging
import re
from logging import FileHandler, Formatter, StreamHandler

_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


class _AnsiStrippingFormatter(Formatter):
    """Formatter that removes ANSI escape codes from messages."""

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return _ANSI_ESCAPE_RE.sub("", formatted)


def configure_logging() -> None:
    """
    Configure logging to both console and file.

    Console logs are INFO+; file logs include DEBUG+ with ANSI codes removed.
    """

    log_format = "%(asctime)s %(levelname)s : %(message)s"
    date_format = "%m-%d %H:%M:%S"
    file_formatter = _AnsiStrippingFormatter(log_format, date_format)
    stream_formatter = Formatter(log_format, date_format)

    file_handler = FileHandler("debug.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])
