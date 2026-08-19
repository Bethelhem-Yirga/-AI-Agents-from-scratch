"""
Simple CrewAI Introduction: Getting Started with Multi-Agent Systems

This example uses OpenRouter instead of OpenAI.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

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
# ✅ FIX: Configure CrewAI to use OpenRouter
# ============================================================================

# CrewAI looks for these environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

# Set the model to use
os.environ["OPENAI_MODEL_NAME"] = "google/gemini-2.0-flash-exp:free"

# Verify configuration
if not os.environ["OPENAI_API_KEY"]:
    print("❌ ERROR: OPENROUTER_API_KEY not found in .env")
    print("Please add: OPENROUTER_API_KEY=your-key-here")
    sys.exit(1)

print(f"✅ Using OpenRouter with model: {os.environ['OPENAI_MODEL_NAME']}")
print(f"✅ API Key found: {os.environ['OPENAI_API_KEY'][:10]}...")

# ============================================================================
# Import CrewAI (after environment setup)
# ============================================================================

from crewai import Agent, Task, Crew, Process


# ============================================================================
# Step 1: Create Agents
# ============================================================================

market_researcher = Agent(
    role='Market Research Analyst',
    goal='Analyze market trends and identify target audiences',
    backstory="""You are an experienced market researcher who excels at
    understanding consumer behavior, market trends, and competitive landscapes.
    You provide data-driven insights that inform business decisions.""",
    verbose=True,
    allow_delegation=False,
)

marketing_strategist = Agent(
    role='Marketing Strategist',
    goal='Develop effective marketing strategies based on research',
    backstory="""You are a creative marketing strategist with a proven track
    record of successful product launches. You excel at crafting compelling
    marketing messages and choosing the right channels to reach target audiences.""",
    verbose=True,
    allow_delegation=False,
)


# ============================================================================
# Step 2: Define Tasks
# ============================================================================

research_task = Task(
    description="""
    Conduct market research for a new AI-powered productivity app.

    Focus on:
    1. Target audience demographics (age, profession, tech-savviness)
    2. Main competitors and their strengths/weaknesses
    3. Key market trends in productivity software
    4. Potential challenges and opportunities

    Provide a concise market analysis report.
    """,
    agent=market_researcher,
    expected_output="A comprehensive market analysis report covering target audience, competitors, trends, and opportunities."
)

strategy_task = Task(
    description="""
    Based on the market research, develop a marketing strategy for launching
    the AI-powered productivity app.

    Include:
    1. Key marketing messages and value propositions
    2. Recommended marketing channels (social media, content, ads, etc.)
    3. Target audience segments to prioritize
    4. Launch timeline and milestones
    5. Success metrics to track

    Create a clear, actionable marketing plan.
    """,
    agent=marketing_strategist,
    expected_output="A detailed marketing strategy with messaging, channels, timeline, and success metrics."
)


# ============================================================================
# Step 3: Create and Run the Crew
# ============================================================================

product_launch_crew = Crew(
    agents=[market_researcher, marketing_strategist],
    tasks=[research_task, strategy_task],
    process=Process.sequential,
    verbose=True,
)


def main():
    """
    Run the simple CrewAI example.
    """
    print("\n" + "="*80)
    print("🚀 Simple CrewAI Example: Product Launch Team")
    print("="*80)
    print("\nThis example demonstrates:")
    print("  1. Creating agents with specific roles")
    print("  2. Defining tasks for each agent")
    print("  3. Running a crew in sequential process")
    print("\n" + "="*80 + "\n")

    print("🧠 Starting the product launch crew...\n")

    try:
        result = product_launch_crew.kickoff()
        
        print("\n" + "="*80)
        print("✅ FINAL RESULT")
        print("="*80 + "\n")
        print(result)
        
        # Save to file
        output_file = Path("product_launch_strategy.txt")
        output_file.write_text(str(result), encoding='utf-8')
        print(f"\n\n📁 Strategy saved to: {output_file.absolute()}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting Tips:")
        print("  1. Check your .env file has: OPENROUTER_API_KEY=your-key")
        print("  2. Verify the API key is valid")
        print("  3. Check your internet connection")


if __name__ == "__main__":
    main()