# runner.py (Enhanced Version)

import asyncio
import os
from core.agent_kernel import AgentKernel
from core.event_bus import EventBus
from interfaces.cli_interface import CLIInterface
from memory.buffer_memory import EnhancedBufferMemory  # Updated import
from reasoning.llm_reasoner import LLMReasoner
from core.utils.tool_loader import load_tools_dynamically
from core.model_selector import ModelSelector

async def main():
    selector = ModelSelector()
    selector.set_selected_model("llama3") 
    
    # Enhanced interface with exit command support
    interface = CLIInterface(allow_empty=False, exit_commands=['exit', 'quit', 'q'])
    
    # 🧠 Enhanced Memory System with persistence
    memory_file = "memory/agent_conversations.json"
    memory = EnhancedBufferMemory(
        limit=1000,  # Increased limit for more context
        persist_file=memory_file
    )
    
    reasoner = LLMReasoner()
    event_bus = EventBus()

    tool_manager = load_tools_dynamically(event_bus=event_bus)

    # 📊 Memory Event Listeners for debugging/monitoring
    def on_memory_save(data):
        if os.getenv("DEBUG_MEMORY"):
            print(f"🧠 Memory saved: {data.get('role', 'unknown')} - {len(data.get('content', ''))} chars")
    
    def on_context_learned(data):
        if os.getenv("DEBUG_MEMORY"):
            print(f"📚 Context learned: {data}")
    
    event_bus.subscribe("on_memory_save", on_memory_save)
    event_bus.subscribe("on_context_learned", on_context_learned)

    agent = AgentKernel(
        interface=interface,
        reasoner=reasoner,
        memory=memory,
        tools=tool_manager,
        event_bus=event_bus
    )

    # 🎯 Show memory status on startup
    print("🤖 AI Agent starting...")
    print(agent.get_memory_summary())
    print("💬 Type 'exit', 'quit', or 'q' to stop\n")

    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
        
        # Save final memory state
        if hasattr(memory, '_persist_memory'):
            memory._persist_memory()
            print("💾 Memory saved successfully")

def add_memory_commands():
    """Optional: Add CLI commands for memory management"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--clear-memory":
            memory_file = "memory/agent_conversations.json"
            if os.path.exists(memory_file):
                os.remove(memory_file)
                print("🗑️ Memory cleared successfully")
            else:
                print("ℹ️ No memory file found to clear")
            return True
            
        elif command == "--show-memory":
            memory = EnhancedBufferMemory(persist_file="memory/agent_conversations.json")
            context = memory.get_full_context()
            print(f"📊 Memory Status:")
            print(f"   Conversation entries: {context['total_entries']}")
            print(f"   Context categories: {len(context.get('context_memory', {}))}")
            print(f"   Session ID: {context['session_id']}")
            
            if context['total_entries'] > 0:
                print(f"\n📝 Recent conversations:")
                recent = memory.recall(limit=5)
                for entry in recent[-5:]:
                    print(f"   {entry}")
            return True
            
        elif command == "--export-memory":
            memory = EnhancedBufferMemory(persist_file="memory/agent_conversations.json")
            export_file = "memory/memory_export.txt"
            
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write("AI Agent Memory Export\n")
                f.write("=" * 50 + "\n\n")
                
                context = memory.get_full_context()
                f.write(f"Total Entries: {context['total_entries']}\n")
                f.write(f"Session ID: {context['session_id']}\n\n")
                
                f.write("Conversation History:\n")
                f.write("-" * 30 + "\n")
                
                for entry in context['conversation_history']:
                    f.write(f"[{entry['timestamp']}] {entry['role']}: {entry['content']}\n")
                
                if context.get('context_memory'):
                    f.write(f"\nContext Memory:\n")
                    f.write("-" * 30 + "\n")
                    for category, items in context['context_memory'].items():
                        f.write(f"\n{category.upper()}:\n")
                        for key, data in items.items():
                            f.write(f"  {key}: {data['value']}\n")
            
            print(f"📤 Memory exported to {export_file}")
            return True
    
    return False

if __name__ == "__main__":
    # Handle memory management commands
    if add_memory_commands():
        exit(0)
    
    # Normal agent execution
    asyncio.run(main())