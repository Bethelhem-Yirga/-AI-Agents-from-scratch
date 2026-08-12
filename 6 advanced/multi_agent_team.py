"""
Multi-Agent Team - Collaborative AI agents with orchestration
"""

from typing import List, Dict, Any, Optional, Callable
import json
import re
from src.agent import BaseAgent
from src.memory import ConversationBufferMemory
from src.planning import ReActPlanner, TaskDecomposer, ThoughtStep


class MockLLMClient:
    """Mock LLM client for testing when real API isn't available."""
    
    def complete(self, prompt: str) -> str:
        """Simulate LLM completion."""
        if "research" in prompt.lower():
            return "Research findings: AI agents are transforming industries by automating complex tasks."
        elif "analyze" in prompt.lower():
            return "Analysis: The key trends are automation, personalization, and efficiency gains."
        elif "summarize" in prompt.lower():
            return "Summary: AI agents are powerful tools for automation and decision support."
        else:
            return "I've processed your request and here are the findings."


class AgentTeam:
    """Orchestrates multiple specialized agents to work together."""
    
    def __init__(self, use_real_api: bool = False):
        """Initialize the agent team.
        
        Args:
            use_real_api: If True, use real API calls. If False, use mock responses.
        """
        self.use_real_api = use_real_api
        self.setup_agents()
        
    def setup_agents(self):
        """Set up the specialized agents and planner."""
        
        # Set up memory for each agent
        planner_memory = ConversationBufferMemory(max_history=5)
        researcher_memory = ConversationBufferMemory(max_history=5)
        analyst_memory = ConversationBufferMemory(max_history=5)
        reviewer_memory = ConversationBufferMemory(max_history=5)
        
        # Create LLM client (real or mock)
        if self.use_real_api:
            # Use real API with BaseAgent
            llm_client = BaseAgent(
                system_prompt="You are a helpful AI assistant.",
                memory=planner_memory,
                temperature=0.7
            )
        else:
            # Use mock client for testing
            llm_client = MockLLMClient()
        
        # Create the planner
        self.planner = ReActPlanner(
            llm_client=llm_client,
            max_steps=5
        )
        
        # Create task decomposer
        self.decomposer = TaskDecomposer(llm_client=llm_client)
        
        # Create specialized agents
        self.researcher = BaseAgent(
            system_prompt="You are a research specialist. Gather and synthesize information accurately.",
            memory=researcher_memory,
            temperature=0.5
        ) if self.use_real_api else MockLLMClient()
        
        self.analyst = BaseAgent(
            system_prompt="You are a data analyst. Analyze information and provide insights.",
            memory=analyst_memory,
            temperature=0.6
        ) if self.use_real_api else MockLLMClient()
        
        self.reviewer = BaseAgent(
            system_prompt="You are a quality reviewer. Critique work and suggest improvements.",
            memory=reviewer_memory,
            temperature=0.4
        ) if self.use_real_api else MockLLMClient()
        
        self.max_revisions = 3
    
    def handle_request(self, query: str) -> str:
        """Process a user request through the team."""
        print("\n" + "="*50)
        print(f"📝 Team received request: {query}")
        print("="*50)
        
        # Step 1: Decompose the task
        print("\n🔍 Step 1: Decomposing task...")
        subtasks = self.decomposer.decompose(query)
        for i, subtask in enumerate(subtasks, 1):
            print(f"  {i}. {subtask}")
        
        # Step 2: Assign subtasks to workers
        print("\n🤖 Step 2: Assigning tasks to specialists...")
        results = []
        for subtask in subtasks:
            if "research" in subtask.lower() or "gather" in subtask.lower():
                worker = self.researcher
                role = "Researcher"
            elif "analyze" in subtask.lower() or "insight" in subtask.lower():
                worker = self.analyst
                role = "Analyst"
            else:
                worker = self.researcher  # Default to researcher
                role = "Researcher"
            
            print(f"  → {role} working on: {subtask}")
            response = self._get_agent_response(worker, subtask)
            results.append({
                "subtask": subtask,
                "worker": role,
                "response": response
            })
            print(f"    ✓ {role} completed")
        
        # Step 3: Synthesize results
        print("\n🔄 Step 3: Synthesizing results...")
        synthesis_prompt = self._create_synthesis_prompt(query, results)
        draft_response = self._get_agent_response(
            self.analyst if self.use_real_api else MockLLMClient(),
            synthesis_prompt
        )
        print("  ✓ Draft synthesized")
        
        # Step 4: Review and iterate
        print("\n✅ Step 4: Reviewing and refining...")
        final_response = self._review_and_refine(query, draft_response, results)
        
        print("\n" + "="*50)
        print("✨ Final Response:")
        print("="*50)
        print(final_response)
        print("="*50 + "\n")
        
        return final_response
    
    def _get_agent_response(self, agent, prompt: str) -> str:
        """Get response from an agent."""
        try:
            if hasattr(agent, 'complete'):
                return agent.complete(prompt)
            elif hasattr(agent, 'chat'):
                return agent.chat(prompt)
            elif hasattr(agent, 'complete'):
                return agent.complete(prompt)
            else:
                return "Agent response not available"
        except Exception as e:
            return f"Error getting agent response: {str(e)}"
    
    def _create_synthesis_prompt(self, query: str, results: List[Dict]) -> str:
        """Create a prompt for synthesizing results."""
        synthesis = f"Based on the following research and analysis, create a comprehensive response to the original query: {query}\n\n"
        
        for result in results:
            synthesis += f"\n--- {result['worker']} on '{result['subtask']}' ---\n"
            synthesis += result['response'] + "\n"
        
        synthesis += "\nSynthesize these findings into a coherent, well-structured response."
        return synthesis
    
    def _review_and_refine(self, query: str, draft: str, results: List[Dict]) -> str:
        """Review and refine the response."""
        current_draft = draft
        
        for revision in range(self.max_revisions):
            # Review the draft
            review_prompt = f"""
Review the following response to the query: "{query}"

Draft Response:
{current_draft}

Provide specific feedback:
1. Factual accuracy issues
2. Missing important information
3. Clarity and structure improvements
4. Overall quality (1-10)

If the draft is excellent and doesn't need further revisions, say "APPROVED".
"""
            
            review = self._get_agent_response(self.reviewer, review_prompt)
            
            if "APPROVED" in review.upper():
                print(f"  ✓ Response approved after {revision + 1} revision(s)")
                break
            
            # Refine based on feedback
            refine_prompt = f"""
Original query: {query}

Previous draft:
{current_draft}

Reviewer feedback:
{review}

Improve the response based on the feedback. Address all specific criticisms while maintaining the original intent.
"""
            
            current_draft = self._get_agent_response(
                self.analyst if self.use_real_api else MockLLMClient(),
                refine_prompt
            )
            print(f"  ↻ Revision {revision + 1} completed")
        
        return current_draft


class MockAgent:
    """Mock agent for testing."""
    
    def chat(self, message: str) -> str:
        return f"Mock response to: {message[:50]}..."
    
    def complete(self, prompt: str) -> str:
        return f"Mock completion for: {prompt[:50]}..."


def main():
    """Main function to run the multi-agent team demo."""
    
    print("\n🤖 Multi-Agent Team Demo")
    print("="*50)
    print("This demo uses mock responses (no API calls).")
    print("To use real API, set use_real_api=True")
    print("="*50 + "\n")
    
    # Create the team with mock responses
    team = AgentTeam(use_real_api=False)
    
    # Example queries
    queries = [
        "Summarize two renewable energy trends and provide a cost comparison.",
        "Research AI safety concerns and suggest best practices.",
        "Plan a project for developing a sustainable agriculture system."
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"🎯 Example {i}: {query}")
        print('='*60)
        result = team.handle_request(query)
        
        # Pause between examples
        if i < len(queries):
            input("\nPress Enter for next example...")
    
    print("\n🎉 Demo complete!")


if __name__ == "__main__":
    main()