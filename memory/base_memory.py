# memory/base_memory.py

from abc import ABC, abstractmethod
from typing import List


class Memory(ABC):
    @abstractmethod
    def save(self, role: str, content: str):
        """
        Store a message or context element.
        Role can be 'user', 'agent', etc.
        """
        pass

    @abstractmethod
    def recall(self, query: str = "") -> List[str]:
        """
        Retrieve past messages or facts as a list of strings.
        The query parameter can optionally be used for filtering.
        """
        pass
