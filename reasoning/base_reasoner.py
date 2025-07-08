# reasoning/base_reasoner.py

from abc import ABC, abstractmethod
from memory.base_memory import Memory
from tools.base_tool import Tool


class Reasoner(ABC):
    @abstractmethod
    def think(self, input: str, memory: Memory, tools: list[Tool]) -> dict:
        """
        Core reasoning function that decides what to do based on input, memory, and available tools.

        Must return a dict like:
        {
            "thoughts": "I need to calculate something.",
            "tool_name": "calculator",
            "tool_input": {"expression": "2 + 2"}
        }
        """
        pass
