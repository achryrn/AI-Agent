# core/tool_manager.py

import inspect
import importlib
import pkgutil
from tools.base_tool import Tool
from core.event_bus import EventBus
from jsonschema import validate, ValidationError

class ToolManager:
    def __init__(self, event_bus: EventBus = None):
        self._tools: dict[str, Tool] = {}
        self.event_bus = event_bus

    def register_tool(self, tool: Tool):
        """Register a tool with proper validation"""
        # Metadata validation
        if not tool.name or not tool.description or not hasattr(tool, "example_usage"):
            raise ValueError(f"[ToolManager] Invalid tool metadata: {tool}")

        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool

        if self.event_bus:
            self.event_bus.emit("on_tool_registered", {
                "tool": tool.name,
                "description": tool.description,
                "schema": getattr(tool, 'example_schema', tool.input_schema)
            })

    def get_tool(self, name: str) -> Tool | None:
        """Get tool by name - FIXED: Added this missing method"""
        return self._tools.get(name)

    def get_tool_by_name(self, name: str) -> Tool | None:
        """Alternative method name for backward compatibility"""
        return self._tools.get(name)

    def get_all_tools(self) -> list[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())

    @property
    def tools(self) -> dict[str, Tool]:
        """Public interface to access registered tools"""
        return self._tools.copy()

    def validate_input(self, tool_name: str, input_data: dict) -> tuple[bool, str]:
        """Validate input data against tool schema"""
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found."
        
        try:
            # Try to get schema from different possible attributes
            schema = None
            if hasattr(tool, 'example_schema'):
                schema = tool.example_schema
            elif hasattr(tool, 'input_schema'):
                schema = tool.input_schema
            else:
                return False, f"Tool '{tool_name}' has no schema defined."
            
            # Convert schema format if needed
            if isinstance(schema, dict) and 'properties' not in schema:
                # Convert simple schema to JSON Schema format
                properties = {}
                required = []
                
                for key, value in schema.items():
                    if isinstance(value, dict):
                        properties[key] = value
                        if value.get('required', False):
                            required.append(key)
                    else:
                        properties[key] = {"type": "string"}
                
                schema = {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            
            validate(instance=input_data, schema=schema)
            return True, ""
            
        except ValidationError as e:
            return False, e.message
        except Exception as e:
            return False, str(e)

    def list_tools(self) -> dict[str, str]:
        """Return a dictionary of tool names and their descriptions"""
        return {name: tool.description for name, tool in self._tools.items()}

    def tool_exists(self, tool_name: str) -> bool:
        """Check if a tool is registered"""
        return tool_name in self._tools

    def unregister_tool(self, tool_name: str) -> bool:
        """Remove a tool from the registry"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            if self.event_bus:
                self.event_bus.emit("on_tool_unregistered", {"tool": tool_name})
            return True
        return False

    def execute_tool(self, tool_name: str, input_data: dict) -> str:
        """Execute a tool with input validation"""
        # Validate input first
        is_valid, error_msg = self.validate_input(tool_name, input_data)
        if not is_valid:
            return f"Input validation failed: {error_msg}"
        
        # Get and execute tool
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found."
        
        try:
            return tool.run(input_data)
        except Exception as e:
            return f"Tool execution failed: {str(e)}"