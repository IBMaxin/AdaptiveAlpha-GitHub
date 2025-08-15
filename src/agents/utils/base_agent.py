"""Module: base_agent.py — auto-generated docstring for flake8 friendliness."""

import logging
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    def __init__(self, name: str, config: dict = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")
        )
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    @abstractmethod
    def run(self):
        pass

    def log(self, msg, level=logging.INFO):
        self.logger.log(level, msg)
