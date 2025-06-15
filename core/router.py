from core.tool_loader import load_tools

class Router:
    def __init__(self, model=None):
        self.tools = load_tools()
        self.model = model

    def route(self, user_input: str, model=None):
        model_to_use = model or self.model

        # Match tool name as prefix (case-insensitive)
        user_input_lower = user_input.lower()

        for tool_name in self.tools.keys():
            if user_input_lower.startswith(tool_name.lower()):
                command = user_input[len(tool_name):].strip()
                try:
                    # Pass model if available
                    if model_to_use:
                        return self.tools[tool_name](command, model_to_use)
                    else:
                        return self.tools[tool_name](command)
                except TypeError:
                    # fallback if tool.run only accepts one argument
                    return self.tools[tool_name](command)

        # No tool matched
        return None
