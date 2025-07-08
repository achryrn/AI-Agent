# interfaces/base_interface.py

from abc import ABC, abstractmethod


class Interface(ABC):
    @abstractmethod
    async def input(self) -> str:
        """Get user input"""
        pass

    @abstractmethod
    async def output(self, message: str):
        """Send output to user"""
        pass
