"""
Memory implementations for AI agents
"""

from typing import List, Dict, Any


class TokenWindowMemory:
    """Memory with token limit (simplified version)."""
    
    def __init__(self, model: str = "gpt-4o-mini", max_tokens: int = 1500):
        self.model = model
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to memory."""
        self.messages.append({"role": role, "content": content})
        # Simple trimming (in reality, you'd count tokens)
        if len(self.messages) > 20:  # Approximate limit
            self.messages = self.messages[-10:]
    
    def get_context(self) -> List[Dict[str, Any]]:
        """Get the current context."""
        return self.messages
    
    def clear(self) -> None:
        """Clear memory."""
        self.messages = []
