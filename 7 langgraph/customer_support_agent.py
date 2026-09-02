"""Enhanced LangGraph Tutorial: Customer Support Ticket Routing System
Converted to use OpenRouter (Free alternative to OpenAI)

This tutorial demonstrates LangGraph's core strengths:
- Orchestration: Multiple specialized nodes working together
- Persistence: State tracking across conversation turns
- Branching: Conditional routing based on ticket properties

Example application: An intelligent customer support system that:
1. Analyzes incoming support requests
2. Routes tickets to appropriate handlers
3. Escalates urgent issues automatically
4. Maintains ticket state throughout the conversation
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import requests
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Annotated, List, Literal, Optional, Sequence, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, add_messages

# ✅ ADD THIS: Load .env from parent directory
script_dir = Path(__file__).parent
project_root = script_dir.parent  # Go up one level
env_path = project_root / '.env'

if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️ .env file not found at: {env_path}")
    print("📝 Make sure your .env file is in the project root folder")
    print("📝 Creating sample .env...")
    with open(project_root / '.env', 'w') as f:
        f.write("# API Keys\n")
        f.write("OPENROUTER_API_KEY=your-openrouter-key-here\n")
    print("✅ Created sample .env. Please add your OpenRouter API key.")

# ============================================================================
# OPENROUTER LLM WRAPPER
# ============================================================================

class OpenRouterLLM:
    """OpenRouter LLM wrapper compatible with LangChain."""
    
    def __init__(self, model: str = "google/gemma-4-26b-a4b-it:free", temperature: float = 0.2):
        load_dotenv(override=True)
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        """Send messages to OpenRouter and get response."""
        
        # Convert LangChain messages to dict format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            else:
                formatted_messages.append({"role": "user", "content": msg.content})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Customer Support Agent"
        }
        
        data = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return AIMessage(content=content)
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                return AIMessage(content=f"Error: {error_msg}")
        except Exception as e:
            return AIMessage(content=f"Error: {str(e)}")
    
    def bind_tools(self, tools: List) -> "OpenRouterLLM":
        """Bind tools to the LLM (for tool calling support)."""
        self._tools = tools
        return self
    
    def invoke_with_tools(self, messages: List[BaseMessage]) -> AIMessage:
        """Send messages with tool support."""
        # For now, just use regular invoke
        # In production, you'd implement proper tool calling
        return self.invoke(messages)


# ============================================================================
# DOMAIN MODELS
# ============================================================================

class TicketCategory(str, Enum):
    """Support ticket categories."""
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    GENERAL = "general"


class TicketPriority(str, Enum):
    """Support ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketState(TypedDict):
    """Current state of a support ticket."""
    ticket_id: str
    category: Optional[str]
    priority: Optional[str]
    summary: Optional[str]
    assigned_to: Optional[str]
    resolution: Optional[str]
    created_at: str


# ============================================================================
# LANGGRAPH STATE
# ============================================================================

class SupportAgentState(TypedDict):
    """LangGraph state that tracks messages AND ticket metadata."""
    messages: Annotated[List[BaseMessage], add_messages]
    ticket: TicketState  # Persistent ticket state


# ============================================================================
# TOOLS
# ============================================================================

@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for solutions to common problems."""
    kb = {
        "password": """To reset your password:
1. Go to login page
2. Click 'Forgot Password'
3. Check your email for reset link
4. Create a new strong password""",
        
        "billing": """For billing inquiries:
- Check your invoice in Account Settings
- Payment methods can be updated under Billing
- Contact billing@company.com for disputes
- Refunds are processed within 5-7 business days""",
        
        "slow": """Performance troubleshooting:
1. Clear browser cache
2. Check internet connection
3. Try incognito mode
4. Update your browser to latest version
5. Disable unnecessary browser extensions""",
        
        "cancel": """To cancel your subscription:
1. Go to Account Settings
2. Select Subscription
3. Click 'Cancel Subscription'
4. Follow the confirmation steps
5. You'll receive a confirmation email""",
        
        "email": """To change your email address:
1. Go to Account Settings
2. Click on Profile
3. Select 'Change Email'
4. Enter new email address
5. Verify the new email""",
        
        "login": """Having trouble logging in?
1. Check your username and password
2. Try resetting your password
3. Clear browser cookies
4. Try a different browser
5. Contact support if issues persist"""
    }

    query_lower = query.lower()
    for key, solution in kb.items():
        if key in query_lower:
            return solution

    return "No exact match found. Please describe your issue in more detail."


@tool
def check_account_status(user_id: str) -> str:
    """Check the status of a user account (simulated)."""
    accounts = {
        "user123": {"status": "active", "plan": "premium", "expires": "2025-12-31"},
        "user456": {"status": "suspended", "plan": "basic", "reason": "payment_failed"},
        "user789": {"status": "active", "plan": "basic", "expires": "2025-06-30"},
        "userABC": {"status": "pending", "plan": "trial", "expires": "2024-03-15"},
    }

    account = accounts.get(user_id, {"status": "not_found"})
    return json.dumps(account, indent=2)


@tool
def create_escalation(ticket_id: str, reason: str) -> str:
    """Escalate a ticket to human support team."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""✓ Ticket {ticket_id} escalated at {timestamp}
Reason: {reason}
A specialist will contact you within 2 hours.

Escalation ID: ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"""


# ============================================================================
# AGENT NODES
# ============================================================================

def analyze_ticket_node(state: SupportAgentState) -> SupportAgentState:
    """First node: Analyze the user's request and classify the ticket."""
    llm = OpenRouterLLM(model="google/gemma-4-26b-a4b-it:free", temperature=0)

    # Get the latest user message
    last_message = state["messages"][-1]
    user_request = last_message.content if isinstance(last_message.content, str) else ""

    # Use LLM to classify the ticket
    analysis_prompt = f"""Analyze this support request and extract:
1. Category: technical, billing, account, or general
2. Priority: low, medium, high, or urgent
3. Brief summary (one line)

User request: {user_request}

Respond in JSON format:
{{"category": "...", "priority": "...", "summary": "..."}}
"""

    response = llm.invoke([HumanMessage(content=analysis_prompt)])

    try:
        # Try to parse JSON from response
        content = response.content
        # Find JSON in the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = content[start_idx:end_idx]
            analysis = json.loads(json_str)
            category = analysis.get("category", "general")
            priority = analysis.get("priority", "medium")
            summary = analysis.get("summary", user_request[:100])
        else:
            category = "general"
            priority = "medium"
            summary = user_request[:100]
    except:
        category = "general"
        priority = "medium"
        summary = user_request[:100]

    # Update ticket state
    updated_ticket = state["ticket"].copy()
    updated_ticket["category"] = category
    updated_ticket["priority"] = priority
    updated_ticket["summary"] = summary

    return {"ticket": updated_ticket}


def route_ticket_node(state: SupportAgentState) -> SupportAgentState:
    """Second node: Route ticket to appropriate handler based on category."""
    ticket = state["ticket"]
    category = ticket.get("category", "general")

    handlers = {
        "technical": "Tech Support Team",
        "billing": "Billing Department",
        "account": "Account Services",
        "general": "General Support",
    }

    assigned_to = handlers.get(category, "General Support")

    updated_ticket = ticket.copy()
    updated_ticket["assigned_to"] = assigned_to

    # Add a system message about routing
    routing_msg = AIMessage(
        content=f"[System: Ticket routed to {assigned_to}]"
    )

    return {"ticket": updated_ticket, "messages": [routing_msg]}


def handle_support_node(state: SupportAgentState) -> SupportAgentState:
    """Third node: Actually handle the support request."""
    llm = OpenRouterLLM(model="google/gemma-4-26b-a4b-it:free", temperature=0.3)

    ticket = state["ticket"]
    messages = state["messages"]

    # Create support context
    support_prompt = f"""You are a helpful customer support agent.

Ticket Info:
- Category: {ticket.get('category', 'Unknown')}
- Priority: {ticket.get('priority', 'Unknown')}
- Summary: {ticket.get('summary', 'No summary')}

You have access to these tools when needed:
- search_knowledge_base: Search for solutions to common problems
- check_account_status: Check user account details (needs user_id)

Provide helpful, concise support. Use the knowledge base when appropriate.

If the user mentions a specific user_id like 'user123', use check_account_status.

If the user is experiencing a technical issue or needs account help, search the knowledge base.

Be friendly and professional. Always offer to help further."""

    # Build conversation with context
    conversation = [SystemMessage(content=support_prompt)] + messages[-4:]

    response = llm.invoke(conversation)

    # Check if we should use tools (simple keyword matching)
    response_content = response.content.lower()
    messages_content = " ".join([m.content for m in messages[-2:] if hasattr(m, 'content')])

    # Use knowledge base if relevant keywords appear
    kb_keywords = ["password", "billing", "slow", "cancel", "email", "login", "reset", "forgot", "payment"]
    account_keywords = ["account", "user", "subscription", "plan"]

    tool_results = []

    if any(keyword in messages_content for keyword in kb_keywords):
        # Search knowledge base
        for keyword in kb_keywords:
            if keyword in messages_content:
                result = search_knowledge_base.invoke({"query": keyword})
                tool_results.append(f"Knowledge Base: {result}")
                break

    if any(keyword in messages_content for keyword in account_keywords):
        # Check account - look for user_id in message
        user_id_match = None
        words = messages_content.split()
        for word in words:
            if word.startswith('user'):
                user_id_match = word
                break
        if user_id_match:
            result = check_account_status.invoke({"user_id": user_id_match})
            tool_results.append(f"Account Status: {result}")

    if tool_results:
        # Create final response incorporating tool results
        final_prompt = f"""Based on these tool results, provide a clear and helpful answer to the user:

{chr(10).join(tool_results)}

Original request: {messages[-1].content if messages else "No message"}

Be friendly, concise, and helpful."""
        final_response = llm.invoke([HumanMessage(content=final_prompt)])
        return {"messages": [final_response]}

    return {"messages": [response]}


def check_escalation_node(state: SupportAgentState) -> SupportAgentState:
    """Final node: Check if escalation is needed."""
    ticket = state["ticket"]
    priority = ticket.get("priority", "medium")

    # Auto-escalate urgent tickets
    if priority == "urgent":
        escalation_msg = AIMessage(
            content=create_escalation.invoke({
                "ticket_id": ticket["ticket_id"],
                "reason": f"Urgent {ticket.get('category', 'support')} issue"
            })
        )
        updated_ticket = ticket.copy()
        updated_ticket["resolution"] = "escalated"
        return {"messages": [escalation_msg], "ticket": updated_ticket}

    # Mark as handled for non-urgent
    updated_ticket = ticket.copy()
    updated_ticket["resolution"] = "handled"
    return {"ticket": updated_ticket}


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def should_escalate(state: SupportAgentState) -> Literal["escalate", "complete"]:
    """Conditional edge: Decide if ticket needs escalation."""
    priority = state["ticket"].get("priority", "medium")

    # Keywords that trigger escalation
    last_message = state["messages"][-1].content if state["messages"] else ""
    if isinstance(last_message, list):
        last_message = str(last_message)
    escalation_keywords = ["speak to manager", "lawsuit", "legal", "unacceptable", "emergency", "urgent"]

    if priority == "urgent" or any(kw in last_message.lower() for kw in escalation_keywords):
        return "escalate"

    return "complete"


# ============================================================================
# MAIN AGENT
# ============================================================================

@dataclass
class CustomerSupportAgent:
    """LangGraph-powered customer support agent using OpenRouter."""
    
    model: str = "google/gemma-4-26b-a4b-it:free"
    temperature: float = 0.3
    graph: StateGraph = field(init=False)

    def __post_init__(self):
        load_dotenv(override=True)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the support ticket workflow graph."""
        builder = StateGraph(SupportAgentState)

        # Add nodes for each stage
        builder.add_node("analyze", analyze_ticket_node)
        builder.add_node("route", route_ticket_node)
        builder.add_node("handle", handle_support_node)
        builder.add_node("check_escalation", check_escalation_node)

        # Define the workflow
        builder.add_edge(START, "analyze")
        builder.add_edge("analyze", "route")
        builder.add_edge("route", "handle")
        builder.add_edge("handle", "check_escalation")

        # Conditional ending - escalate or complete
        builder.add_conditional_edges(
            "check_escalation",
            should_escalate,
            {
                "escalate": END,
                "complete": END,
            }
        )

        return builder.compile()

    def handle_request(self, user_request: str, ticket_id: Optional[str] = None) -> dict:
        """Process a support request through the workflow."""
        if ticket_id is None:
            ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        initial_state = {
            "messages": [HumanMessage(content=user_request)],
            "ticket": {
                "ticket_id": ticket_id,
                "category": None,
                "priority": None,
                "summary": None,
                "assigned_to": None,
                "resolution": None,
                "created_at": datetime.now().isoformat(),
            }
        }

        # Run through the graph
        result = self.graph.invoke(initial_state)

        # Extract response
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        response = ai_messages[-1].content if ai_messages else "I'm here to help!"

        return {
            "response": response,
            "ticket": result["ticket"],
        }

    def print_ticket_info(self, ticket: TicketState):
        """Pretty print ticket information."""
        print("\n" + "="*60)
        print(f"Ticket ID: {ticket['ticket_id']}")
        print(f"Category: {ticket.get('category', 'N/A')}")
        print(f"Priority: {ticket.get('priority', 'N/A')}")
        print(f"Assigned To: {ticket.get('assigned_to', 'N/A')}")
        print(f"Summary: {ticket.get('summary', 'N/A')}")
        print(f"Status: {ticket.get('resolution', 'in_progress')}")
        print("="*60 + "\n")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def run_examples():
    """Run example scenarios to demonstrate the agent's capabilities."""
    agent = CustomerSupportAgent()

    examples = [
        {
            "name": "Low Priority - General Question",
            "request": "How do I change my email address?",
        },
        {
            "name": "Medium Priority - Technical Issue",
            "request": "The app is running really slow on my phone. What can I do?",
        },
        {
            "name": "High Priority - Billing Issue",
            "request": "I was charged twice this month! This is unacceptable.",
        },
        {
            "name": "Urgent - Account Access",
            "request": "URGENT: I can't access my account and I have an important presentation in 1 hour!",
        },
    ]

    print("\n*** CUSTOMER SUPPORT AGENT - EXAMPLE SCENARIOS ***")
    print("="*70)

    for i, example in enumerate(examples, 1):
        print(f"\n[Example {i}]: {example['name']}")
        print("-"*70)
        print(f"User: {example['request']}")
        print()

        result = agent.handle_request(example['request'])

        print(f"Agent: {result['response']}")
        agent.print_ticket_info(result['ticket'])

        if i < len(examples):
            print("\n" + "-"*70)


def run_interactive():
    """Run interactive chat mode."""
    agent = CustomerSupportAgent()

    print("\n*** CUSTOMER SUPPORT AGENT - INTERACTIVE MODE ***")
    print("="*70)
    print("Type your support request, or 'quit' to exit.")
    print()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            print("Thank you for contacting support. Goodbye!")
            break

        result = agent.handle_request(user_input)

        print(f"\nAgent: {result['response']}")
        agent.print_ticket_info(result['ticket'])


def main():
    # Check for API key
    load_dotenv()
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ ERROR: OPENROUTER_API_KEY not found in .env file")
        print("Please add your key to .env:")
        print("OPENROUTER_API_KEY=your-key-here")
        return

    parser = argparse.ArgumentParser(
        description="LangGraph Customer Support Agent Tutorial (OpenRouter)"
    )
    parser.add_argument(
        "--mode",
        choices=["examples", "interactive"],
        default="examples",
        help="Run examples or interactive mode"
    )

    args = parser.parse_args()

    if args.mode == "examples":
        run_examples()
    else:
        run_interactive()


if __name__ == "__main__":
    main()