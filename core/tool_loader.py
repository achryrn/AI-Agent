import os
import importlib.util
import importlib
from typing import Dict, Callable

TOOLS_DIR = os.path.join(os.path.dirname(__file__), '..', 'tools')

def load_tools() -> Dict[str, Callable]:
    """
    Dynamically load all tools in tools/ directory.
    Supports both .py files and packages (folders with __init__.py).
    Each must define a run(command: str, model) -> str function.
    """
    tools = {}

    for item in os.listdir(TOOLS_DIR):
        item_path = os.path.join(TOOLS_DIR, item)

        # Load from .py file
        if item.endswith(".py") and not item.startswith("_"):
            tool_name = item[:-3]
            spec = importlib.util.spec_from_file_location(tool_name, item_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "run") and callable(module.run):
                    tools[tool_name] = module.run

        # Load from package (folder with __init__.py)
        elif os.path.isdir(item_path) and os.path.isfile(os.path.join(item_path, '__init__.py')):
            module_name = f"tools.{item}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "run") and callable(module.run):
                    tools[item] = module.run
            except Exception as e:
                print(f"Failed to load tool '{item}': {e}")

    return tools
