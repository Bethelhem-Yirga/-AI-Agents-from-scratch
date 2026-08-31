"""
Memory implementations for AI agents
"""

from typing import List, Dict, Any
from collections import deque

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


class ConversationBufferMemory:
    """Simple conversation memory that stores chat history."""
    
    def __init__(self, max_history: int = 10, max_messages: int = None):
        """Initialize the conversation buffer.
        
        Args:
            max_history: Maximum number of conversation turns to keep
            max_messages: Alias for max_history (for compatibility with different tutorials)
        """
        # Support both parameter names
        if max_messages is not None:
            self.max_history = max_messages
        else:
            self.max_history = max_history
            
        self.history: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history.
        
        Args:
            role: The role of the message sender ('user' or 'assistant')
            content: The message content
        """
        self.history.append({"role": role, "content": content})
        
        # Trim history to max size (each turn has user + assistant)
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history."""
        return self.history
    
    def get_context(self) -> List[Dict[str, str]]:
        """Get the current context (alias for get_history)."""
        return self.get_history()
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self.history = []
    
    def add_user_message(self, content: str) -> None:
        """Convenience method to add a user message."""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """Convenience method to add an assistant message."""
        self.add_message("assistant", content)
    
    def get_last_n_messages(self, n: int) -> List[Dict[str, str]]:
        """Get the last N messages from history."""
        return self.history[-n:] if self.history else []
    
    def __len__(self) -> int:
        """Return the number of messages in history."""
        return len(self.history)