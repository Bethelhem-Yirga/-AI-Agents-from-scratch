"""
Planning utilities for AI agents - ReAct pattern and task decomposition
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import json
import re


@dataclass
class ThoughtStep:
    """Represents a single thought step in the ReAct process."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None
    is_final: bool = False
    final_answer: Optional[str] = None


class TaskDecomposer:
    """Break down complex tasks into subtasks."""
    
    def __init__(self, llm_client=None):
        """Initialize the task decomposer.
        
        Args:
            llm_client: An optional LLM client for intelligent decomposition.
                       If None, uses rule-based decomposition.
        """
        self.llm_client = llm_client
    
    def decompose(self, task: str) -> List[str]:
        """Decompose a task into subtasks.
        
        Args:
            task: The main task to decompose
            
        Returns:
            List of subtask descriptions
        """
        # If we have an LLM, use it for intelligent decomposition
        if self.llm_client:
            return self._decompose_with_llm(task)
        else:
            return self._decompose_with_rules(task)
    
    def _decompose_with_rules(self, task: str) -> List[str]:
        """Simple rule-based decomposition."""
        # Common patterns
        if "summarize" in task.lower() or "summary" in task.lower():
            return [
                "Read and understand the source material",
                "Identify key points and main arguments",
                "Organize findings into a coherent summary",
                "Review and polish the summary"
            ]
        elif "research" in task.lower() or "analyze" in task.lower():
            return [
                "Define research questions and scope",
                "Gather relevant information and data",
                "Analyze the collected information",
                "Synthesize findings into insights",
                "Prepare final report"
            ]
        elif "plan" in task.lower() or "strategy" in task.lower():
            return [
                "Define goals and objectives",
                "Identify resources and constraints",
                "Develop action items and timeline",
                "Create monitoring and evaluation plan"
            ]
        else:
            # Generic decomposition
            return [
                f"Understand the task: {task}",
                "Gather necessary information",
                "Analyze and process the information",
                "Generate solution or response",
                "Review and refine the output"
            ]
    
    def _decompose_with_llm(self, task: str) -> List[str]:
        """Use LLM for intelligent task decomposition."""
        prompt = f"""Break down the following task into 3-5 specific subtasks that can be executed independently:

Task: {task}

List the subtasks as a JSON array of strings. Each subtask should be clear and actionable."""
        
        try:
            response = self.llm_client.complete(prompt)
            # Try to extract JSON array
            match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            if match:
                subtasks = json.loads(f'[{match.group(1)}]')
                return subtasks if isinstance(subtasks, list) else [task]
        except Exception:
            pass
        
        # Fallback to rule-based
        return self._decompose_with_rules(task)


class ReActPlanner:
    """Planner that uses the ReAct (Reasoning + Acting) pattern."""
    
    def __init__(self, llm_client, tools: Optional[Dict[str, Callable]] = None,
                 max_steps: int = 5):
        """Initialize the ReAct planner.
        
        Args:
            llm_client: An LLM client with a complete() method
            tools: Dictionary of tool name -> function mappings
            max_steps: Maximum number of reasoning steps
        """
        self.llm_client = llm_client
        self.tools = tools or {}
        self.max_steps = max_steps
        self.thought_steps: List[ThoughtStep] = []
    
    def plan(self, query: str) -> str:
        """Execute the ReAct planning loop.
        
        Args:
            query: The user's query or task
            
        Returns:
            The final answer or response
        """
        self.thought_steps = []
        current_query = query
        
        for step in range(self.max_steps):
            # Generate thought
            thought = self._generate_thought(current_query, step)
            self.thought_steps.append(thought)
            
            # If final answer, return it
            if thought.is_final and thought.final_answer:
                return thought.final_answer
            
            # Execute action if needed
            if thought.action and thought.action in self.tools:
                try:
                    result = self.tools[thought.action](thought.action_input)
                    observation = f"Tool '{thought.action}' returned: {result}"
                    current_query = f"{current_query}\nObservation: {observation}"
                except Exception as e:
                    observation = f"Error executing tool '{thought.action}': {str(e)}"
            
            # If no action, treat thought as the answer
            if not thought.action and not thought.is_final:
                # If thought contains a plausible answer, use it
                if len(thought.thought) > 50:  # Arbitrary threshold
                    return thought.thought
        
        # If we've exhausted steps, return the last thought
        return self.thought_steps[-1].thought if self.thought_steps else "Unable to complete the task."
    
    def _generate_thought(self, query: str, step: int) -> ThoughtStep:
        """Generate a thought using the LLM."""
        tools_desc = "\n".join([f"- {name}: {getattr(func, '__doc__', 'No description')}" 
                                for name, func in self.tools.items()])
        
        prompt = f"""You are a reasoning agent using the ReAct (Reasoning + Acting) pattern.

Current query: {query}
Step number: {step + 1}/{self.max_steps}

Available tools:
{tools_desc if tools_desc else 'No tools available'}

Analyze the situation and respond in the following format:

THOUGHT: Your reasoning about the current situation and what to do next.
ACTION: (Optional) The tool to use (if any). Choose from the available tools.
ACTION_INPUT: (Optional) The input to the tool.
FINAL: (Optional) Use this if you have a final answer. Include the complete final answer.

Remember:
- Think step by step
- If you have enough information, provide a FINAL answer
- Use tools only when necessary
- Be specific in your reasoning

Your response:"""
        
        try:
            response = self.llm_client.complete(prompt)
            
            # Parse the response
            thought = ThoughtStep(thought="")
            
            # Extract thought
            thought_match = re.search(r'THOUGHT:\s*(.*?)(?=ACTION:|FINAL:|$)', response, re.DOTALL)
            if thought_match:
                thought.thought = thought_match.group(1).strip()
            
            # Extract action
            action_match = re.search(r'ACTION:\s*(.*?)(?=ACTION_INPUT:|FINAL:|$)', response, re.DOTALL)
            if action_match:
                thought.action = action_match.group(1).strip()
            
            # Extract action input
            input_match = re.search(r'ACTION_INPUT:\s*(.*?)(?=ACTION:|FINAL:|$)', response, re.DOTALL)
            if input_match:
                thought.action_input = input_match.group(1).strip()
            
            # Check if final
            final_match = re.search(r'FINAL:\s*(.*?)$', response, re.DOTALL)
            if final_match:
                thought.is_final = True
                thought.final_answer = final_match.group(1).strip()
            
            return thought
            
        except Exception as e:
            return ThoughtStep(
                thought=f"Error generating thought: {str(e)}",
                is_final=True,
                final_answer="I encountered an error in my reasoning."
            )
    
    def get_thought_trace(self) -> List[Dict[str, Any]]:
        """Get the complete thought trace for debugging."""
        return [
            {
                "step": i,
                "thought": step.thought,
                "action": step.action,
                "action_input": step.action_input,
                "observation": step.observation,
                "is_final": step.is_final,
                "final_answer": step.final_answer
            }
            for i, step in enumerate(self.thought_steps)
        ]


# Additional helper functions
def create_planning_agent(llm_client, tools: Optional[Dict[str, Callable]] = None):
    """Convenience function to create a planning agent."""
    return ReActPlanner(llm_client, tools)


if __name__ == "__main__":
    # Simple test
    class MockLLM:
        def complete(self, prompt):
            return """THOUGHT: I need to analyze the task and provide a plan.
ACTION: None
FINAL: I will help you plan your project step by step."""
    
    planner = ReActPlanner(MockLLM())
    result = planner.plan("Help me plan a software project")
    print("Result:", result)
    print("Thought trace:", planner.get_thought_trace())