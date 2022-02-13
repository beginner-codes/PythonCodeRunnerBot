from typing import Protocol
import logging


class Loggable(Protocol):
    log: logging.Logger
