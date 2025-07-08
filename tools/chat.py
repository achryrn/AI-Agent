# tools/chat.py

from tools.base_tool import Tool

class ChatTool(Tool):
    name = "chat"
    description = "Replies conversationally to the user."

    def run(self, input: dict) -> str:
        return input.get("response", "I'm here.")

    @property
    def example_usage(self) -> str:
        return 'Example: {"response": "Hello! How can I help you?"}'
