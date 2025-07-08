# core/utils/tool_loader.py

import os
import importlib
from tools.base_tool import Tool
from core.tool_manager import ToolManager
from core.event_bus import EventBus


def load_tools_dynamically(tool_dir="tools", event_bus: EventBus = None) -> ToolManager:
    tool_manager = ToolManager()

    for filename in os.listdir(tool_dir):
        if (
            filename.endswith(".py")
            and not filename.startswith("_")
            and filename not in {"base_tool.py", "tool_manager.py"}
        ):
            module_name = filename[:-3]  # strip '.py'
            try:
                module = importlib.import_module(f"{tool_dir}.{module_name}")

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Tool)
                        and attr is not Tool
                    ):
                        tool_instance = attr()

                        # ✅ Metadata validation
                        assert hasattr(tool_instance, "name") and tool_instance.name
                        assert hasattr(tool_instance, "description") and tool_instance.description
                        assert hasattr(tool_instance, "example_usage") and tool_instance.example_usage
                        assert callable(getattr(tool_instance, "run", None))

                        tool_manager.register_tool(tool_instance)

                        if event_bus:
                            event_bus.emit("on_tool_loaded", {
                                "tool_name": tool_instance.name,
                                "description": tool_instance.description
                            })

            except Exception as e:
                error_msg = f"Failed to load tool: {module_name} - {str(e)}"
                print(f"[ToolLoader ERROR] {error_msg}")
                if event_bus:
                    event_bus.emit("on_tool_error", {
                        "module": module_name,
                        "error": str(e)
                    })

    return tool_manager
