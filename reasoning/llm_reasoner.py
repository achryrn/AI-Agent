# reasoning/llm_reasoner.py

import httpx
import json
from core.config import AGENT_NAME
from reasoning.base_reasoner import Reasoner
from memory.base_memory import Memory
from core.tool_manager import ToolManager
from reasoning.prompt_templates import SYSTEM_PROMPT, CONTEXTUAL_PROMPT
from jsonschema import validate, ValidationError
from core.model_selector import ModelSelector

LLM_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["thoughts", "tool_name", "tool_input"],
    "properties": {
        "thoughts": {"type": "string"},
        "tool_name": {"type": ["string", "null"]},
        "tool_input": {"type": "object"}
    }
}

class LLMReasoner(Reasoner):
    def __init__(self, model=None, base_url="http://localhost:11434/api/generate", retries=3, **kwargs):
        if model is None:
            model_selector = ModelSelector()
            model = model_selector.get_selected_model()
        
        self.model = model
        self.base_url = base_url
        self.retries = retries
        self.debug_mode = kwargs.get('debug_mode', False)
        self.event_bus = None

    def think(self, input: str, memory: Memory, tools: ToolManager, interface=None, event_bus=None, **kwargs) -> dict:
        """
        Use LLM to dynamically understand intent and select appropriate tools
        """
        if event_bus:
            self.event_bus = event_bus
        
        try:
            # Get available tools dynamically
            available_tools = tools.get_all_tools()
            tool_descriptions = self._format_tool_descriptions(available_tools)
            
            # Get memory context
            memory_context = self._format_memory_context(memory)
            
            # Build dynamic prompt
            prompt = CONTEXTUAL_PROMPT.substitute(
                agent_name=AGENT_NAME,
                tool_list=", ".join([tool.name for tool in available_tools]),
                tool_descriptions=tool_descriptions,
                memory_context=memory_context,
                input=input,
                system_prompt=SYSTEM_PROMPT.substitute(
                    agent_name=AGENT_NAME,
                    tool_list=", ".join([tool.name for tool in available_tools])
                )
            )

            if self.debug_mode and self.event_bus:
                self.event_bus.emit("on_llm_prompt", {"prompt": prompt})

            transcript = []

            def stream_callback(line):
                if interface:
                    interface.print("...thinking", end="\r")
                    interface.print(line, end="")
                transcript.append(line)
                if self.event_bus:
                    self.event_bus.emit("on_llm_stream_line", {"line": line})

            response_str = self._try_call_llm(prompt, token_callback=stream_callback)

            memory.save("llm_transcript", "\n".join(transcript))

            if self.debug_mode and self.event_bus:
                self.event_bus.emit("on_llm_response", {"response": response_str})
            elif self.event_bus:
                self.event_bus.emit("on_llm_response", {
                    "input": input,
                    "prompt": prompt,
                    "raw_response": response_str,
                    "transcript": transcript
                })
            
            # Parse and validate the response
            try:
                parsed = json.loads(response_str.strip())
                validate(parsed, LLM_RESPONSE_SCHEMA)
                
                # Validate that the tool exists
                if not self._validate_reasoning_result(parsed, available_tools):
                    return self._fallback_response(input)
                
                if self.debug_mode and self.event_bus:
                    self.event_bus.emit("on_thought", parsed)
                return parsed
            except (json.JSONDecodeError, ValidationError) as e:
                fallback_prompt = (
                    f"You're an AI assistant. The user asked something, but your last response failed to format correctly.\n"
                    f"Just answer the user's question clearly and helpfully without explaining what went wrong.\n\n"
                    f"User's input:\n{input}\n\n"
                    f"Previous malformed response:\n{response_str.strip()}\n\n"
                    f"Respond directly to the user now:"
                )

                try:
                    fallback_response_str = self._try_call_llm(fallback_prompt)
                    if self.debug_mode and self.event_bus:
                        self.event_bus.emit("on_llm_response", {"response": fallback_response_str, "note": "Fallback due to parsing error"})
                    
                    fallback_parsed = {
                        "thoughts": f"Invalid LLM output, attempted rephrasing. Original error: {str(e)}",
                        "tool_name": "chat",
                        "tool_input": {
                            "response": fallback_response_str.strip()
                        }
                    }
                    if self.debug_mode and self.event_bus:
                        self.event_bus.emit("on_thought", fallback_parsed)
                    return fallback_parsed
                except Exception as inner_e:
                    final_fallback_parsed = {
                        "thoughts": f"Double LLM failure. Initial error: {str(e)}. Fallback error: {str(inner_e)}",
                        "tool_name": "chat",
                        "tool_input": {
                            "response": f"Raw LLM output from initial attempt: {response_str.strip()}"
                        }
                    }
                    if self.debug_mode and self.event_bus:
                        self.event_bus.emit("on_thought", final_fallback_parsed)
                    return final_fallback_parsed
                    
        except Exception as e:
            print(f"LLM Reasoning failed: {e}")
            error_fallback_parsed = self._fallback_response(input)
            error_fallback_parsed["thoughts"] = f"LLM Reasoning failed: {e}. Falling back to chat."
            if self.debug_mode and self.event_bus:
                self.event_bus.emit("on_thought", error_fallback_parsed)
            return error_fallback_parsed

    def _format_tool_descriptions(self, tools) -> str:
        """Format tool descriptions for the LLM"""
        descriptions = []
        for tool in tools:
            descriptions.append(f"- {tool.name}: {tool.description}")
            if hasattr(tool, 'example_usage'):
                descriptions.append(f"  Example: {tool.example_usage}")
        return "\n".join(descriptions)
    
    def _format_memory_context(self, memory: Memory) -> str:
        """Format recent memory for context"""
        try:
            recent_messages = memory.get_recent(limit=5)
            if not recent_messages:
                return "No previous conversation history."
            
            context = []
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:200]  # Limit length
                context.append(f"{role}: {content}")
            
            return "\n".join(context)
        except:
            return "No conversation history available."

    def _validate_reasoning_result(self, result: dict, available_tools) -> bool:
        """Validate that the LLM response is properly formatted"""
        if not isinstance(result, dict):
            return False
        
        required_keys = ["thoughts", "tool_name", "tool_input"]
        if not all(key in result for key in required_keys):
            return False
        
        # Check if requested tool exists
        tool_names = [tool.name for tool in available_tools]
        if result["tool_name"] not in tool_names:
            return False
        
        return True

    def _fallback_response(self, input: str) -> dict:
        """Fallback when LLM reasoning fails"""
        return {
            "thoughts": "LLM reasoning failed, falling back to chat response.",
            "tool_name": "chat",
            "tool_input": {"response": f"I'm having trouble processing that request. Could you rephrase it? You asked: {input}"}
        }

    def _call_llm_stream(self, prompt: str, token_callback=None) -> str:
        with httpx.stream("POST", self.base_url, json={
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }, timeout=None) as response:
            if response.status_code != 200:
                raise RuntimeError(f"LLM returned HTTP {response.status_code}")

            full_text = ""
            line_buffer = ""
            for chunk in response.iter_text():
                if chunk.strip():
                    try:
                        data = json.loads(chunk)
                        token = data.get("response", "")
                        full_text += token
                        line_buffer += token

                        while "\n" in line_buffer:
                            line, line_buffer = line_buffer.split("\n", 1)
                            if token_callback:
                                token_callback(line + "\n")
                    except Exception:
                        continue

            if line_buffer and token_callback:
                token_callback(line_buffer)

            return full_text

    def _try_call_llm(self, prompt: str, token_callback=None) -> str:
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                return self._call_llm_stream(prompt, token_callback)
            except Exception as e:
                print(f"[LLM Retry] Attempt {attempt} failed: {e}")
                last_error = e
        raise RuntimeError(f"LLM failed after {self.retries} retries: {str(last_error)}")

    def _select_contextual_memory(self, memory: Memory, query: str, limit=10) -> str:
        if hasattr(memory, "semantic_search"):
            results = memory.semantic_search(query, top_k=limit)
            return "\n".join(results)
        return "\n".join(memory.recall()[-limit:])

    def _build_prompt(self, input: str, memory: Memory, tools: ToolManager) -> str:
        memory_context = self._select_contextual_memory(memory, input)

        all_tools = tools.get_all_tools()
        tool_descriptions = "\n".join(
            [
                f"{tool.name} - {tool.description}\n{tool.example_usage}"
                for tool in all_tools
            ]
        )
        system_prompt = SYSTEM_PROMPT.substitute(
            agent_name=AGENT_NAME,
            tool_list=", ".join([tool.name for tool in all_tools])
        )

        return CONTEXTUAL_PROMPT.substitute(
            input=input,
            memory_context=memory_context,
            tool_descriptions=tool_descriptions,
            system_prompt=system_prompt
        )