# tools/base_tool.py

from abc import ABC, abstractmethod
import json


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, input: dict) -> str:
        pass

    @property
    @abstractmethod
    def example_usage(self) -> str:
        """Returns example usage in JSON format string."""
        pass

    @property
    def example_schema(self) -> dict:
        """Auto-generate schema from example."""
        try:
            example = json.loads(self.example_usage.replace("Example:", "").strip())
            def infer_type(value):
                if isinstance(value, bool): return "boolean"
                if isinstance(value, int): return "integer"
                if isinstance(value, float): return "number"
                if isinstance(value, dict): return "object"
                if isinstance(value, list): return "array"
                return "string"

            return {
                "type": "object",
                "required": list(example.keys()),
                "properties": {
                    k: {"type": infer_type(v)} for k, v in example.items()
                }
            }
        except Exception:
            return {"type": "object"}
