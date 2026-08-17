"""
Planning and ReAct implementation for AI agents
"""

from typing import List, Dict, Any, Optional, Tuple
import json


class ThoughtStep:
    """A single step in the reasoning process."""
    
    def __init__(self, thought: str = "", action: str = "", action_input: dict = None, 
                 observation: str = "", final_answer: str = ""):
        self.thought = thought
        self.action = action
        self.action_input = action_input or {}
        self.observation = observation
        self.final_answer = final_answer


class TaskDecomposer:
    """Breaks down a high-level task into smaller subtasks."""
    
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps
    
    def decompose(self, goal: str, agent) -> List[str]:
        """Decompose a goal into subtasks."""
        prompt = f"""Break down this goal into {self.max_steps} or fewer subtasks.
Goal: {goal}

Return only the subtasks, one per line, numbered.
Example:
1. Research flights
2. Find accommodation
"""
        try:
            response = agent.chat(prompt)
            subtasks = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and line[0].isdigit() and '.' in line:
                    parts = line.split('.', 1)
                    if len(parts) > 1:
                        subtasks.append(parts[1].strip())
            return subtasks[:self.max_steps]
        except:
            return [goal]


