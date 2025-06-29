# core/tool_prompt.py

import json
import os
from typing import Dict, Any, Optional
from core.tool_manager import ToolManager
from memory.base_memory import Memory
from reasoning.base_reasoner import Reasoner


class ToolPromptHandler:
    """
    Handles smart prompting for tools with required fields.
    Automatically fills missing required fields using LLM reasoning.
    """
    
    def __init__(self, reasoner: Reasoner, memory: Memory):
        self.reasoner = reasoner
        self.memory = memory
        self.prompt_cache = {}
        self._load_tool_prompts()
    
    def _load_tool_prompts(self):
        """Load tool-specific prompts from prompts/ directory"""
        prompts_dir = "prompts"
        if not os.path.exists(prompts_dir):
            os.makedirs(prompts_dir)
            return
        
        for filename in os.listdir(prompts_dir):
            if filename.endswith("_prompt.json"):
                tool_name = filename.replace("_prompt.json", "")
                try:
                    with open(os.path.join(prompts_dir, filename), 'r') as f:
                        self.prompt_cache[tool_name] = json.load(f)
                except Exception as e:
                    print(f"[ToolPromptHandler] Failed to load {filename}: {e}")
    
    def get_tool_prompt(self, tool_name: str) -> Dict[str, Any]:
        """Get prompt configuration for a specific tool"""
        return self.prompt_cache.get(tool_name, {})
    
    def fill_missing_fields(self, tool_name: str, tool_input: Dict[str, Any], 
                          user_input: str, tool_manager: ToolManager) -> Dict[str, Any]:
        """
        Automatically fill missing required fields using LLM reasoning
        """
        tool = tool_manager.get_tool_by_name(tool_name)
        if not tool:
            return tool_input
        
        # Get tool schema
        schema = getattr(tool, 'example_schema', {})
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})
        
        # Check which required fields are missing
        missing_fields = [field for field in required_fields if field not in tool_input or not tool_input[field]]
        
        if not missing_fields:
            return tool_input  # All required fields present
        
        # Get tool-specific prompt configuration
        tool_prompt_config = self.get_tool_prompt(tool_name)
        
        # Fill missing fields using LLM
        filled_input = tool_input.copy()
        for field in missing_fields:
            filled_value = self._fill_single_field(
                tool_name, field, properties.get(field, {}), 
                user_input, tool_prompt_config, filled_input
            )
            if filled_value is not None:
                filled_input[field] = filled_value
        
        return filled_input
    
    def _fill_single_field(self, tool_name: str, field_name: str, field_schema: Dict,
                          user_input: str, tool_config: Dict, current_input: Dict) -> Any:
        """Fill a single missing field using LLM reasoning"""
        
        # Get field-specific prompt from config
        field_prompts = tool_config.get('field_prompts', {})
        field_prompt = field_prompts.get(field_name, '')
        
        # Build context-aware prompt
        field_type = field_schema.get('type', 'string')
        field_description = field_schema.get('description', f'{field_name} field')
        
        # Create smart prompt
        prompt = self._build_field_prompt(
            tool_name, field_name, field_type, field_description,
            user_input, current_input, field_prompt
        )
        
        try:
            # Use reasoner to get the field value
            reasoning_result = self.reasoner.think(
                input=prompt,
                memory=self.memory,
                tools=None  # Don't use tools for field filling
            )
            
            # Extract the field value from reasoning result
            if reasoning_result.get("tool_name") == "chat":
                response = reasoning_result.get("tool_input", {}).get("response", "")
                return self._parse_field_value(response, field_type)
            
        except Exception as e:
            print(f"[ToolPromptHandler] Failed to fill field {field_name}: {e}")
        
        return None
    
    def _build_field_prompt(self, tool_name: str, field_name: str, field_type: str,
                           field_description: str, user_input: str, current_input: Dict,
                           custom_prompt: str = "") -> str:
        """Build an intelligent prompt for filling a specific field"""
        
        base_prompt = f"""
You are helping to fill missing required fields for the '{tool_name}' tool.

User's original request: "{user_input}"

Missing field: {field_name}
Field type: {field_type}
Field description: {field_description}

Current tool input: {json.dumps(current_input, indent=2)}

{custom_prompt}

Based on the user's request, what should the value be for the '{field_name}' field?
Respond ONLY with the field value, no explanations or extra text.
"""
        
        # Add type-specific instructions
        if field_type == "boolean":
            base_prompt += "\nRespond with only: true or false"
        elif field_type == "integer":
            base_prompt += "\nRespond with only a number (integer)"
        elif field_type == "number":
            base_prompt += "\nRespond with only a number"
        elif field_type == "array":
            base_prompt += "\nRespond with a JSON array format: [item1, item2, ...]"
        elif field_type == "object":
            base_prompt += "\nRespond with a JSON object format: {\"key\": \"value\"}"
        else:
            base_prompt += "\nRespond with only the text/string value"
        
        return base_prompt.strip()
    
    def _parse_field_value(self, response: str, field_type: str) -> Any:
        """Parse LLM response into the correct field type"""
        response = response.strip()
        
        try:
            if field_type == "boolean":
                return response.lower() in ["true", "yes", "1", "on"]
            elif field_type == "integer":
                return int(response)
            elif field_type == "number":
                return float(response)
            elif field_type in ["array", "object"]:
                return json.loads(response)
            else:
                return response
                
        except (ValueError, json.JSONDecodeError):
            # Fallback to string
            return response
    
    def create_tool_prompt_template(self, tool_name: str, tool_manager: ToolManager):
        """Create a prompt template file for a specific tool"""
        tool = tool_manager.get_tool_by_name(tool_name)
        if not tool:
            print(f"[ToolPromptHandler] Tool '{tool_name}' not found")
            return
        
        schema = getattr(tool, 'example_schema', {})
        properties = schema.get('properties', {})
        
        # Create template
        template = {
            "tool_name": tool_name,
            "description": tool.description,
            "field_prompts": {}
        }
        
        # Add field-specific prompts
        for field_name, field_info in properties.items():
            template["field_prompts"][field_name] = f"Smart prompt for {field_name} field. Customize this based on your tool's needs."
        
        # Save template
        prompts_dir = "prompts"
        os.makedirs(prompts_dir, exist_ok=True)
        
        template_path = os.path.join(prompts_dir, f"{tool_name}_prompt.json")
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"[ToolPromptHandler] Created template: {template_path}")
        return template_path