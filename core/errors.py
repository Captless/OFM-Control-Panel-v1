"""Shared WaveSpeed error class."""
import logging

logger = logging.getLogger(__name__)


class WaveSpeedError(Exception):
    def __init__(self, message, code=None, status=0):
        self.code = code
        self.message = str(message)
        self.status = status
        super().__init__(f"[{status} {code}] {message}" if code else str(message))
        logger.warning("WaveSpeedError: %s", self)
