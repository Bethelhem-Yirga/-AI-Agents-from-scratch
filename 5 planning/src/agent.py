"""
Base Agent - Core AI agent implementation
"""

from typing import List, Optional
import requests
import json
import os
from dotenv import load_dotenv


class BaseAgent:
    """Base AI agent with memory and tool capabilities."""
    
    def __init__(self, system_prompt: str, memory=None, temperature: float = 0.7, model: str = "gpt-4o-mini"):
        load_dotenv()
        
        self.system_prompt = system_prompt
        self.memory = memory
        self.temperature = temperature
        self.model = model
        
        # For OpenRouter support
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def chat(self, message: str) -> str:
        """Send a message to the agent and get a response."""
        if self.memory:
            context = self.memory.get_context()
        else:
            context = []
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + context + [
            {"role": "user", "content": message}
        ]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model if not self.model.startswith("google/") else "google/gemini-2.0-flash-exp:free",
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
