class Memory:
    def __init__(self, max_turns=10):
        self.max_turns = max_turns
        self.history = []
        self.facts = {}  # key: fact name, value: fact content

    def add(self, role: str, text: str):
        self.history.append({"role": role, "text": text})
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2 :]
            
    def add_fact(self, key: str, value: str):
        self.facts[key] = value

    def get_fact(self, key: str):
        return self.facts.get(key, None)

    def get_all_facts_summary(self):
        if not self.facts:
            return ""
        summary = "Known facts:\n"
        for k, v in self.facts.items():
            summary += f"- {k.replace('_', ' ').title()}: {v}\n"
        summary += "\n"
        return summary
    
    def get_conversation(self) -> str:
        convo = ""
        for entry in self.history:
            prefix = "User: " if entry["role"] == "user" else "Assistant: "
            convo += prefix + entry["text"] + "\n"
        return convo

    def get_context_for_prompt(self) -> str:
        """Combine facts summary + recent conversation for prompt context."""
        return self.get_all_facts_summary() + self.get_conversation()

class ShortTermMemory:
    def __init__(self):
        self.history = []

    def add(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_last(self, n=1):
        return self.history[-n:] if n > 0 else []

    def get_all(self):
        return self.history.copy()

    def clear(self):
        self.history = []
        
