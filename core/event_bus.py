# core/event_bus.py

from collections import defaultdict
from typing import Callable, Dict, List


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable):
        self._subscribers[event_name].append(callback)

    def emit(self, event_name: str, data: dict):
        for callback in self._subscribers[event_name]:
            callback(data)
