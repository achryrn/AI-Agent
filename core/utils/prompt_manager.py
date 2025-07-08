#!/usr/bin/env python3
# prompt_manager.py - Utility for managing tool prompts

import sys
import asyncio
from core.agent_kernel import AgentKernel
from core.event_bus import EventBus
from interfaces.cli_interface import CLIInterface
from memory.buffer_memory import MemoryEnhancedReasoner
from reasoning.llm_reasoner import LLMReasoner
from core.utils.tool_loader import load_tools_dynamically
from core.model_selector import ModelSelector

async def create_all_prompts():
    """Create prompt templates for all loaded tools"""
    selector = ModelSelector()
    selector.set_selected_model("llama3")
    
    interface = CLIInterface()
    memory = MemoryEnhancedReasoner()
    reasoner = LLMReasoner()
    event_bus = EventBus()
    tool_manager = load_tools_dynamically(event_bus=event_bus)
    
    agent = AgentKernel(
        interface=interface,
        reasoner=reasoner,
        memory=memory,
        tools=tool_manager,
        event_bus=event_bus
    )
    
    print("Creating prompt templates for all tools...")
    
    for tool_name in tool_manager.list_tools().keys():
        try:
            template_path = agent.create_prompt_template(tool_name)
            print(f"✅ Created: {template_path}")
        except Exception as e:
            print(f"❌ Failed to create template for {tool_name}: {e}")

def main():
    if len(sys.argv) < 2:
        print("""
Usage: python prompt_manager.py <command>

Commands:
  create-all    - Create prompt templates for all tools
  create <tool> - Create prompt template for specific tool
        """)
        return
    
    command = sys.argv[1]
    
    if command == "create-all":
        asyncio.run(create_all_prompts())
    elif command == "create" and len(sys.argv) > 2:
        tool_name = sys.argv[2]
        # Implementation for single tool creation
        print(f"Creating prompt template for {tool_name}...")
    else:
        print("Invalid command. Use 'create-all' or 'create <tool_name>'")

if __name__ == "__main__":
    main()