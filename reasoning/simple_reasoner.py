# reasoning/simple_reasoner.py

from reasoning.base_reasoner import Reasoner
from memory.base_memory import Memory
from core.tool_manager import ToolManager  # ← Central registry


class SimpleReasoner(Reasoner):
    def think(self, input: str, memory: Memory, tools: ToolManager) -> dict:
        """
        Rule-based reasoning for MVP agent.
        If input contains math-related tokens, use the calculator.
        Otherwise, fallback to chat.
        """
        input_lower = input.lower()
        math_keywords = ["+", "-", "*", "/", "plus", "minus", "times", "divided"]
        is_math_query = any(op in input_lower for op in math_keywords)

        if is_math_query and tools.get_tool_by_name("calculator"):
            return {
                "thoughts": "This looks like a math problem. Using calculator.",
                "tool_name": "calculator",
                "tool_input": {"expression": input}
            }

        # Fallback to chat tool
        return {
            "thoughts": "This doesn't look like a math problem. Falling back to chat.",
            "tool_name": "chat",
            "tool_input": {"response": f"Echo: {input}"}
        }
