# core/agent_kernel.py (Enhanced Version)

from typing import Any
import asyncio
import inspect
from core.event_bus import EventBus
from interfaces.base_interface import Interface
from memory.base_memory import Memory
from reasoning.base_reasoner import Reasoner
from core.tool_manager import ToolManager
from core.tool_prompt import ToolPromptHandler
from memory.buffer_memory import MemoryEnhancedReasoner
import traceback

class AgentKernel:
    def __init__(
        self,
        interface: Interface,
        reasoner: Reasoner,
        memory: Memory,
        tools: ToolManager,
        event_bus: EventBus = None,
        debug_mode: bool = False
    ):
        self.interface = interface
        self.reasoner = reasoner
        self.memory = memory
        self.tools = tools
        self.event_bus = event_bus or EventBus()
        self.debug_mode = debug_mode # Store debug_mode
        
        # Initialize tool prompt handler
        self.tool_prompt_handler = ToolPromptHandler(reasoner, memory)
        self.tools = tools
        self.event_bus = event_bus or EventBus()
        
        # Initialize tool prompt handler
        self.tool_prompt_handler = ToolPromptHandler(reasoner, memory)
        
        # Initialize memory enhancer
        self.memory_enhancer = MemoryEnhancedReasoner()
        
        # Load any existing conversation context
        self._load_conversation_context()

    def _load_conversation_context(self):
        """Load and display previous conversation summary on startup"""
        if hasattr(self.memory, 'get_conversation_context'):
            context = self.memory.get_conversation_context(last_n=5)
            if context and len(context.strip()) > 0:
                print("🧠 Resuming conversation with previous context loaded...")
                # Optionally show a brief summary
                history_count = len(getattr(self.memory, '_conversation_history', []))
                if history_count > 0:
                    print(f"📚 Loaded {history_count} previous conversation entries")

    async def run(self):
        while True:
            try:
                user_input = await self.interface.input()
                self.event_bus.emit("on_input", {"input": user_input})
                
                # Enhanced memory save with metadata
                self.memory.save("user", user_input, metadata={
                    "input_length": len(user_input),
                    "tool_context": "conversation_start"
                })

                # 🧠 Enhanced reasoning with memory context injection
                enhanced_prompt = self._prepare_reasoning_prompt(user_input)
                
                # Pass event_bus to reasoner's think method
                reasoning_result = self.reasoner.think(
                    input=enhanced_prompt,
                    memory=self.memory,
                    tools=self.tools,
                    event_bus=self.event_bus # Pass event_bus
                )
                # Emitting "on_thought" is already done by debug_runner if DEBUG_MODE is on.
                # If not in DEBUG_MODE, it's still good to have for other potential listeners.
                if not self.debug_mode:
                    self.event_bus.emit("on_thought", reasoning_result)

                tool_name = reasoning_result.get("tool_name")
                tool_input = reasoning_result.get("tool_input", {})

                if self.debug_mode:
                    self.event_bus.emit("on_tool_selected", {"tool_name": tool_name, "tool_input": tool_input})

                # ✅ Case: pure chat response
                if tool_name == "chat" and "response" in tool_input:
                    output = tool_input["response"]
                    await self.interface.output(output)
                    
                    # Enhanced memory save with learning extraction
                    self._save_conversation_with_learning(user_input, output)
                    
                    if self.debug_mode:
                         self.event_bus.emit("on_tool_output", {"tool_name": "chat", "output": output})
                    else:
                        self.event_bus.emit("on_tool_used", {
                            "tool": "chat",
                            "input": tool_input,
                            "output": output
                        })
                    continue

                # ❌ Missing tool - Enhanced error handling with memory
                tool = self.tools.get_tool_by_name(tool_name)   
                if not tool:
                    fallback_response = tool_input.get("response")
                    if fallback_response:
                        output = f"[Fallback Chat] Tool '{tool_name}' not found. Chatting instead:\n{fallback_response}"
                        await self.interface.output(output)
                        
                        # Save fallback with context
                        self.memory.save("agent", output, metadata={
                            "type": "fallback",
                            "requested_tool": tool_name,
                            "reason": "tool_not_found"
                        })
                        
                        # Learn from the failed tool request
                        if hasattr(self.memory, 'save_context'):
                            self.memory.save_context(
                                f"failed_tool_{tool_name}", 
                                {"user_request": user_input, "fallback_used": True},
                                category="tool_usage"
                            )
                        
                        if self.debug_mode:
                            self.event_bus.emit("on_tool_output", {"tool_name": "chat_fallback", "output": output})
                        else:
                            self.event_bus.emit("on_tool_used", {
                                "tool": "chat_fallback",
                                "input": tool_input,
                                "output": output
                            })
                        continue
                    else:
                        error_msg = f"[ERROR] Tool '{tool_name}' not found or undefined."
                        await self.interface.output(error_msg)
                        self.memory.save("agent", error_msg, metadata={"type": "error", "error_type": "tool_not_found"})
                        if self.debug_mode:
                             self.event_bus.emit("on_tool_output", {"tool_name": "error_tool_not_found", "output": error_msg})
                        continue

                # 🔧 Smart field filling for missing required fields
                original_input = tool_input.copy()
                tool_input = self.tool_prompt_handler.fill_missing_fields(
                    tool_name, tool_input, user_input, self.tools
                )
                
                # Log if fields were auto-filled
                if tool_input != original_input:
                    self.event_bus.emit("on_fields_auto_filled", {
                        "tool": tool_name,
                        "original_input": original_input,
                        "filled_input": tool_input
                    })

                # ✅ Validate tool input (after auto-filling)
                valid, error_msg = self.tools.validate_input(tool_name, tool_input)
                if not valid:
                    error_output = f"[ERROR] Invalid tool input: {error_msg}"
                    await self.interface.output(error_output)
                    self.memory.save("agent", error_output, metadata={
                        "type": "error", 
                        "error_type": "validation_failed",
                        "tool": tool_name
                    })
                    continue

                # ✅ Run tool - Handle both sync and async tools
                if inspect.iscoroutinefunction(tool.run):
                    tool_output = await tool.run(tool_input)
                else:
                    tool_output = tool.run(tool_input)
                
                if self.debug_mode:
                    self.event_bus.emit("on_tool_output", {"tool_name": tool_name, "output": tool_output})
                else:
                    self.event_bus.emit("on_tool_used", {
                        "tool": tool_name,
                        "input": tool_input,
                        "output": tool_output
                    })

                # Enhanced memory save for tool results
                self.memory.save("agent", tool_output, metadata={
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "success": True
                })
                
                # Learn from successful tool usage
                if hasattr(self.memory, 'save_context'):
                    self.memory.save_context(
                        f"successful_tool_{tool_name}",
                        {
                            "user_request": user_input,
                            "tool_input": tool_input,
                            "output_length": len(str(tool_output))
                        },
                        category="tool_usage"
                    )

                await self.interface.output(tool_output)
                self.event_bus.emit("on_output", {"output": tool_output})

            except Exception as e:
                error_msg = f"[ERROR] Agent crashed: {str(e)}\n{traceback.format_exc()}"
                await self.interface.output(error_msg)
                
                # Save error to memory for debugging
                self.memory.save("system", error_msg, metadata={
                    "type": "system_error",
                    "exception_type": type(e).__name__
                })
                
                self.event_bus.emit("on_error", {"error": error_msg})

    def _prepare_reasoning_prompt(self, user_input: str) -> str:
        """Prepare enhanced prompt with memory context"""
        if hasattr(self.memory, 'get_conversation_context'):
            return self.memory_enhancer.inject_memory_context(
                user_input, 
                self.memory, 
                context_limit=8  # Adjust based on your needs
            )
        else:
            # Fallback for basic memory
            recent_context = self.memory.recall(limit=5)
            if recent_context:
                context_str = "\n".join(recent_context[-5:])  # Last 5 entries
                return f"Previous context:\n{context_str}\n\nCurrent request: {user_input}"
            return user_input

    def _save_conversation_with_learning(self, user_input: str, agent_output: str):
        """Save conversation and extract learnable information"""
        # Save the agent response with metadata
        self.memory.save("agent", agent_output, metadata={
            "type": "chat_response",
            "response_length": len(agent_output)
        })
        
        # Extract and save learnable information
        if hasattr(self.memory, 'save_context'):
            learnable_info = self.memory_enhancer.extract_learnable_info(user_input, agent_output)
            for info_type, info_value in learnable_info.items():
                self.memory.save_context(f"learned_{info_type}", info_value, category="learned_facts")

    def get_memory_summary(self) -> str:
        """Get a summary of current memory state"""
        if hasattr(self.memory, 'get_full_context'):
            context = self.memory.get_full_context()
            return f"Memory Summary:\n- Conversation entries: {context['total_entries']}\n- Context categories: {len(context.get('context_memory', {}))}\n- Session ID: {context['session_id']}"
        else:
            history = self.memory.recall()
            return f"Memory Summary:\n- Total entries: {len(history)}"

    # Enhanced utility method for creating tool prompt templates
    def create_prompt_template(self, tool_name: str):
        """Create a prompt template for a specific tool with memory context"""
        base_template = self.tool_prompt_handler.create_tool_prompt_template(tool_name, self.tools)
        
        # Add memory context to tool prompts if available
        if hasattr(self.memory, 'search_memory'):
            # Search for relevant previous tool usage
            relevant_usage = self.memory.search_memory(tool_name, in_context=True)
            if relevant_usage:
                memory_context = "\n".join([f"Previous {tool_name} usage: {item}" for item in relevant_usage[:3]])
                return f"{base_template}\n\nRelevant previous usage:\n{memory_context}"
        
        return base_template