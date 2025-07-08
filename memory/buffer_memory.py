# memory/buffer_memory.py

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from memory.base_memory import Memory
from core.config import MEMORY_LIMIT

class EnhancedBufferMemory(Memory):
    def __init__(self, limit: int = MEMORY_LIMIT, persist_file: str = "memory/conversation_history.json"):
        self.limit = limit
        self.persist_file = persist_file
        self._conversation_history = []
        self._context_memory = {}  # For storing facts, preferences, etc.
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load previous conversations if they exist
        self._load_persistent_memory()

    def save(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Enhanced save with metadata and context tracking"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        
        self._conversation_history.append(entry)
        
        # Apply memory limit (but keep recent conversations)
        if len(self._conversation_history) > self.limit:
            # Remove oldest entries but preserve session boundaries
            self._conversation_history = self._conversation_history[-self.limit:]
        
        # Auto-persist after each save
        self._persist_memory()

    def save_context(self, key: str, value: Any, category: str = "general"):
        """Save contextual information (facts, preferences, learned info)"""
        if category not in self._context_memory:
            self._context_memory[category] = {}
        
        self._context_memory[category][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id
        }
        self._persist_memory()

    def recall(self, query: str = "", include_context: bool = True, limit: Optional[int] = None) -> List[str]:
        """Enhanced recall with context inclusion and filtering"""
        results = []
        
        # Add conversation history
        history_entries = self._conversation_history
        if limit:
            history_entries = history_entries[-limit:]
            
        for entry in history_entries:
            if not query or query.lower() in entry["content"].lower():
                formatted_entry = f"[{entry['timestamp']}] {entry['role']}: {entry['content']}"
                if entry.get("metadata"):
                    formatted_entry += f" (metadata: {entry['metadata']})"
                results.append(formatted_entry)
        
        # Add context memory if requested
        if include_context and self._context_memory:
            results.append("\n--- CONTEXT MEMORY ---")
            for category, items in self._context_memory.items():
                results.append(f"[{category.upper()}]")
                for key, data in items.items():
                    results.append(f"  {key}: {data['value']}")
        
        return results

    def get_conversation_context(self, last_n: int = 10) -> str:
        """Get formatted conversation context for the reasoner"""
        recent_entries = self._conversation_history[-last_n:] if self._conversation_history else []
        
        context_parts = []
        
        # Add recent conversation
        if recent_entries:
            context_parts.append("RECENT CONVERSATION:")
            for entry in recent_entries:
                context_parts.append(f"{entry['role']}: {entry['content']}")
        
        # Add relevant context memory
        if self._context_memory:
            context_parts.append("\nRELEVANT CONTEXT:")
            for category, items in self._context_memory.items():
                if items:  # Only add non-empty categories
                    context_parts.append(f"{category.upper()}:")
                    for key, data in items.items():
                        context_parts.append(f"  - {key}: {data['value']}")
        
        return "\n".join(context_parts)

    def get_full_context(self) -> Dict[str, Any]:
        """Get complete memory state for advanced reasoning"""
        return {
            "conversation_history": self._conversation_history,
            "context_memory": self._context_memory,
            "session_id": self._session_id,
            "total_entries": len(self._conversation_history)
        }

    def search_memory(self, query: str, in_content: bool = True, in_context: bool = True) -> List[Dict[str, Any]]:
        """Search through memory with more advanced filtering"""
        results = []
        query_lower = query.lower()
        
        # Search conversation history
        if in_content:
            for entry in self._conversation_history:
                if query_lower in entry["content"].lower():
                    results.append({
                        "type": "conversation",
                        "entry": entry,
                        "match_in": "content"
                    })
        
        # Search context memory
        if in_context:
            for category, items in self._context_memory.items():
                for key, data in items.items():
                    if (query_lower in key.lower() or 
                        query_lower in str(data["value"]).lower()):
                        results.append({
                            "type": "context",
                            "category": category,
                            "key": key,
                            "data": data,
                            "match_in": "context"
                        })
        
        return results

    def clear_session(self):
        """Clear current session but keep persistent context"""
        self._conversation_history = []
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _persist_memory(self):
        """Save memory to file for persistence across runs"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.persist_file), exist_ok=True)
            
            memory_data = {
                "conversation_history": self._conversation_history,
                "context_memory": self._context_memory,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not persist memory: {e}")

    def _load_persistent_memory(self):
        """Load memory from file if it exists"""
        try:
            if os.path.exists(self.persist_file):
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                self._conversation_history = memory_data.get("conversation_history", [])
                self._context_memory = memory_data.get("context_memory", {})
                
                print(f"Loaded {len(self._conversation_history)} conversation entries from persistent memory")
        except Exception as e:
            print(f"Warning: Could not load persistent memory: {e}")
            # Start fresh if loading fails
            self._conversation_history = []
            self._context_memory = {}


# memory/memory_enhanced_reasoner.py

class MemoryEnhancedReasoner:
    """Mixin class to enhance any reasoner with memory awareness"""
    
    def inject_memory_context(self, prompt: str, memory, context_limit: int = 10) -> str:
        """Inject memory context into reasoning prompts"""
        
        # Get conversation context
        conversation_context = memory.get_conversation_context(last_n=context_limit)
        
        if conversation_context:
            enhanced_prompt = f"""CONVERSATION CONTEXT:
{conversation_context}

CURRENT REQUEST:
{prompt}

Please consider the above context when responding. Reference previous conversations when relevant."""
            return enhanced_prompt
        
        return prompt

    def extract_learnable_info(self, user_input: str, agent_response: str) -> Dict[str, Any]:
        """Extract information that should be remembered for future conversations"""
        learnable_info = {}
        
        # Simple keyword-based extraction (can be enhanced with NLP)
        user_lower = user_input.lower()
        
        # Extract preferences
        if "i like" in user_lower or "i prefer" in user_lower:
            learnable_info["preference"] = user_input
        
        # Extract facts about user
        if "i am" in user_lower or "my name is" in user_lower:
            learnable_info["user_fact"] = user_input
        
        # Extract important decisions or conclusions
        if "remember" in user_lower or "note that" in user_lower:
            learnable_info["important_note"] = user_input
        
        return learnable_info