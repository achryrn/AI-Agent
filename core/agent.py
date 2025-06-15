from core.memory import Memory, ShortTermMemory
from core.model_interface import OllamaModel
from core.router import Router
import os

class Agent:
    def __init__(self):
        model_name = os.getenv("LLAMA3_MODEL_NAME", "artifish/llama3.2-uncensored:latest")
        self.model = OllamaModel(model_name)
        self.memory = Memory()
        self.short_term = ShortTermMemory()
        self.router = Router()
        self.tools_info = self._generate_tools_info()
        self.system_prompt = self._load_system_prompt()

        self.tools_enabled = False
        self.active_tool = None

    def _load_system_prompt(self) -> str:
        prompt_path = os.getenv("SYSTEM_PROMPT_PATH", "config/system_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip() + "\n\n"
        else:
            return (
                "You are a helpful and knowledgeable AI assistant with access to some special tools.\n"
                "You must respond conversationally and clearly.\n\n"
            )

    def _generate_tools_info(self) -> str:
        return (
            "Tools available:\n"
            "- placeholder_tool: A test tool that echoes input text back.\n"
            "- google_search: Searches Google for a given query and returns results (title, snippet, link).\n"
            "- research: Surf the internet using a real browser and return deep, detailed information from multiple pages and subpages.\n"
            "\nCommands:\n"
            "- 'use tool <tool_name>' to enable tool-only mode with that tool.\n"
            "- 'disable tools' to exit tool-only mode.\n"
            "- 'recall last [N]' to view last N memory entries.\n"
        )

    def handle_input(self, user_input: str) -> str:
        lowered = user_input.lower().strip()

        # Tool control
        if lowered.startswith("use tool "):
            tool_name = lowered[len("use tool "):].strip()
            if tool_name in self.router.tools:
                self.tools_enabled = True
                self.active_tool = tool_name
                return f"Tool mode enabled. Now using tool: {tool_name}"
            else:
                return f"Tool '{tool_name}' not found."

        if lowered == "disable tools":
            self.tools_enabled = False
            self.active_tool = None
            return "Tool mode disabled. Returning to normal response."

        # Recall short-term memory
        if lowered.startswith("recall last"):
            try:
                parts = lowered.split()
                n = int(parts[-1]) if len(parts) > 2 else 5
                entries = self.short_term.get_last(n)
                if not entries:
                    return "No memory entries found."
                return "\n".join([f"{e['role'].capitalize()}: {e['content']}" for e in entries])
            except Exception:
                return "Usage: recall last [N] (e.g., 'recall last 3')"

        # Active tool
        if self.tools_enabled and self.active_tool:
            tool_func = self.router.tools.get(self.active_tool)
            if tool_func:
                tool_result = tool_func(user_input, self.model)
                self.memory.add("user", user_input)
                self.memory.add("assistant", tool_result)
                self.short_term.add("user", user_input)
                self.short_term.add("assistant", tool_result)
                return f"[Using {self.active_tool}]\n{tool_result}"

        # Tool router
        tool_response = self.router.route(user_input, model=self.model)
        if tool_response is not None:
            return tool_response

        # Normal LLM prompt
        self.memory.add("user", user_input)
        self.short_term.add("user", user_input)

        prompt = (
            self.system_prompt
            + self.tools_info
            + self.memory.get_conversation()
            + "Assistant: "
        )
        response = self.model.generate(prompt)
        self.memory.add("assistant", response)
        self.short_term.add("assistant", response)

        return response
