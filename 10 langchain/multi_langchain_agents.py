"""
Tutorial 09 (bonus): Multi-agent coordination with vanilla LangChain (Fixed).

This script orchestrates three LangChain agents—Researcher, Coder, and Reviewer—
using the new LangChain 1.0+ syntax.
"""

from __future__ import annotations

import ast
import operator
import os
from typing import Any, Iterable
from pathlib import Path

from dotenv import load_dotenv

# ============================================================================
# ✅ Fixed imports for LangChain 1.0+
# ============================================================================

import langchain.agents
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# ============================================================================
# Load .env from project root
# ============================================================================

script_dir = Path(__file__).parent
project_root = script_dir.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print("⚠️ .env file not found!")

# ============================================================================
# ✅ Configure OpenRouter
# ============================================================================

api_key = os.getenv("OPENROUTER_API_KEY", "")

if not api_key:
    print("❌ ERROR: OPENROUTER_API_KEY not found in .env")
    print("Please add: OPENROUTER_API_KEY=your-key-here")
    raise RuntimeError("OPENROUTER_API_KEY is required.")

print(f"✅ API Key found: {api_key[:10]}...")

# Set environment variables for LangChain
os.environ["OPENAI_API_KEY"] = api_key
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

# ✅ Use a model that works with OpenRouter
OPENROUTER_MODEL = "openai/gpt-4o-mini"

print(f"✅ Using OpenRouter with model: {OPENROUTER_MODEL}")

# ============================================================================
# Safe Calculator
# ============================================================================

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}


def safe_calculator(expression: str) -> str:
    """Evaluate a math expression safely using AST parsing."""
    if not expression.strip():
        raise ValueError("Empty expression.")

    node = ast.parse(expression, mode="eval").body

    def _eval(subnode: ast.AST) -> float:
        if isinstance(subnode, ast.Num):  # type: ignore[attr-defined]
            return float(subnode.n)
        if isinstance(subnode, ast.Constant) and isinstance(subnode.value, (int, float)):
            return float(subnode.value)
        if isinstance(subnode, ast.BinOp) and type(subnode.op) in ALLOWED_OPERATORS:
            left = _eval(subnode.left)
            right = _eval(subnode.right)
            return ALLOWED_OPERATORS[type(subnode.op)](left, right)
        if isinstance(subnode, ast.UnaryOp) and isinstance(subnode.op, (ast.UAdd, ast.USub)):
            return +_eval(subnode.operand) if isinstance(subnode.op, ast.UAdd) else -_eval(subnode.operand)
        raise ValueError("Unsupported expression.")

    return str(_eval(node))


def build_tools() -> list[Tool]:
    """Return shared tools for every agent."""
    return [
        Tool(
            name="Calculator",
            func=safe_calculator,
            description="Useful for arithmetic. Input should be a math expression like '1200/3 + 45'.",
        )
    ]


def create_agent(system_prompt: str, llm: ChatOpenAI, tools: list[Tool]) -> langchain.agents.AgentExecutor:
    """Create a tool-calling agent with a custom system prompt."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = langchain.agents.create_tool_calling_agent(llm, tools, prompt)
    return langchain.agents.AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=4,
        handle_parsing_errors=True,
    )


def format_steps(result: dict[str, Any]) -> Iterable[str]:
    """Yield formatted intermediate steps for logging."""
    for action, observation in result.get("intermediate_steps", []):
        yield f"Tool: {action.tool}\nInput: {action.tool_input}\nObservation: {observation}\n---"


def run_pipeline(question: str) -> None:
    """Coordinate the three agents on the provided question."""
    # ✅ Create LLM with OpenRouter
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=0.25,
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    tools = build_tools()

    # Create three specialized agents
    researcher = create_agent(
        "You are ResearchAgent. Read the business question, outline 3-4 bullet steps, "
        "and highlight which columns/statistics from time_series.csv you need.",
        llm,
        tools,
    )
    coder = create_agent(
        "You are CoderAgent. Write Python (pandas + matplotlib) pseudocode or code snippets "
        "that implement the given analysis plan. Emphasize data loading, cleaning, and anomaly checks. "
        "Do NOT actually run code; just produce steps.",
        llm,
        tools,
    )
    reviewer = create_agent(
        "You are ReviewerAgent. Evaluate the plan and code snippet for completeness, safety, "
        "and whether it answers the question. Respond with PASS/FAIL and reasons.",
        llm,
        tools,
    )

    context: dict[str, Any] = {}

    # Step 1: Researcher plan
    print("\n" + "="*80)
    print("🔍 RESEARCHER AGENT - Planning Analysis")
    print("="*80)
    
    research_result = researcher.invoke(
        {
            "input": (
                f"Question: {question}\n"
                "Describe a short plan (bullets) and note which columns from time_series.csv you expect."
            )
        }
    )
    context["plan"] = research_result["output"]

    # Step 2: Coder produces pseudocode leveraging plan
    print("\n" + "="*80)
    print("💻 CODER AGENT - Writing Analysis Code")
    print("="*80)
    
    coder_result = coder.invoke(
        {
            "input": (
                f"Follow this plan:\n{context['plan']}\n\n"
                "Write Python pseudocode (pandas/matplotlib) to execute the analysis. "
                "Focus on seasonality + anomaly detection. Mention any helper functions."
            )
        }
    )
    context["code"] = coder_result["output"]

    # Step 3: Reviewer checks the work
    print("\n" + "="*80)
    print("📋 REVIEWER AGENT - Quality Check")
    print("="*80)
    
    reviewer_result = reviewer.invoke(
        {
            "input": (
                "Review the following materials:\n"
                f"Plan:\n{context['plan']}\n\n"
                f"Code snippet:\n{context['code']}\n\n"
                "Respond with PASS or FAIL and list concrete reasons."
            )
        }
    )
    context["review"] = reviewer_result["output"]

    # Final summary
    print("\n" + "="*80)
    print("📋 FINAL SUMMARY")
    print("="*80)
    
    print("\n" + "="*80)
    print("🔍 RESEARCH AGENT OUTPUT")
    print("="*80)
    print(context["plan"])
    print("\n--- Tool Calls ---")
    for step in format_steps(research_result):
        print(step)

    print("\n" + "="*80)
    print("💻 CODER AGENT OUTPUT")
    print("="*80)
    print(context["code"])
    print("\n--- Tool Calls ---")
    for step in format_steps(coder_result):
        print(step)

    print("\n" + "="*80)
    print("📋 REVIEWER AGENT OUTPUT")
    print("="*80)
    print(context["review"])
    print("\n--- Tool Calls ---")
    for step in format_steps(reviewer_result):
        print(step)


def main() -> None:
    task = (
        "Find seasonality, anomalies, and 2 recommendations using the dataset time_series.csv. "
        "Return a punchy summary at the end."
    )
    
    print("\n" + "="*80)
    print("🧠 Multi-Agent Pipeline (LangChain Tool-Calling)")
    print("="*80)
    print(f"📋 Task: {task}")
    print(f"🧠 Model: {OPENROUTER_MODEL}")
    print("="*80)
    
    run_pipeline(task)


if __name__ == "__main__":
    main()