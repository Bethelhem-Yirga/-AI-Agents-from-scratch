"""
🌐 Planning Agent Web Interface - Streamlit Version
A beautiful web UI for your planning agent with real-time step display
"""

import os
import sys
import json
import time
from pathlib import Path
import streamlit as st
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import your agent components
from src.agent import BaseAgent
from src.memory import TokenWindowMemory
from src.planning import ReActPlanner, TaskDecomposer, ThoughtStep
from src.tools import (
    CalculatorTool,
    WeatherTool,
    FlightSearchTool,
    HotelSearchTool,
    CurrencyConverterTool,
    SearchTool,
    CalendarTool,
    MapsTool
)

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="🧠 Planning Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS
# ============================================================================

st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #f0f2f6;
    }
    
    /* Header */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    
    .header h1 {
        margin: 0;
        font-size: 2em;
    }
    
    .header p {
        margin: 5px 0 0 0;
        opacity: 0.9;
    }
    
    /* Subtask cards */
    .subtask-card {
        background-color: white;
        padding: 15px 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .subtask-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }
    
    .subtask-card.completed {
        border-left-color: #28a745;
        background-color: #f0fff4;
    }
    
    .subtask-card.in-progress {
        border-left-color: #ffc107;
        background-color: #fff8e1;
    }
    
    .subtask-number {
        display: inline-block;
        background: #667eea;
        color: white;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        text-align: center;
        line-height: 28px;
        font-weight: bold;
        font-size: 14px;
        margin-right: 10px;
    }
    
    .subtask-number.completed {
        background: #28a745;
    }
    
    .subtask-number.in-progress {
        background: #ffc107;
    }
    
    /* Thought steps */
    .thought-step {
        background-color: #f8f9fa;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #6c757d;
        font-family: monospace;
        font-size: 0.9em;
    }
    
    .thought-step.thought {
        border-left-color: #6c757d;
        background-color: #f8f9fa;
    }
    
    .thought-step.action {
        border-left-color: #007bff;
        background-color: #e3f2fd;
    }
    
    .thought-step.observation {
        border-left-color: #28a745;
        background-color: #e8f5e9;
    }
    
    .thought-step.final {
        border-left-color: #fd7e14;
        background-color: #fff3e0;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
    }
    
    .status-badge.completed {
        background: #28a745;
        color: white;
    }
    
    .status-badge.in-progress {
        background: #ffc107;
        color: #333;
    }
    
    .status-badge.pending {
        background: #e9ecef;
        color: #6c757d;
    }
    
    /* Progress bar */
    .progress-container {
        background: #e9ecef;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transition: width 0.5s ease;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.8em;
        font-weight: 600;
    }
    
    /* Sidebar styling */
    .sidebar-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .sidebar-section h4 {
        margin-top: 0;
        color: #495057;
    }
    
    /* Tool tags */
    .tool-tag {
        display: inline-block;
        background: #e9ecef;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.7em;
        margin: 2px;
        color: #495057;
    }
    
    .tool-tag.active {
        background: #667eea;
        color: white;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Initialize Session State
# ============================================================================

if 'agent' not in st.session_state:
    st.session_state.agent = None
    st.session_state.messages = []
    st.session_state.subtasks = []
    st.session_state.answers = []
    st.session_state.steps = []
    st.session_state.is_running = False
    st.session_state.current_subtask = 0
    st.session_state.total_subtasks = 0

# ============================================================================
# Helper Functions
# ============================================================================

def format_steps(steps: list) -> str:
    """Format thought steps for display."""
    lines = []
    for index, step in enumerate(steps, start=1):
        lines.append(f"**Step {index}**")
        if step.thought:
            lines.append(f"💭 Thought: {step.thought}")
        if step.action:
            lines.append(f"🔧 Action: {step.action}")
        if step.action_input:
            lines.append(f"📥 Action Input: {step.action_input}")
        if step.observation:
            obs = step.observation[:200] + "..." if len(step.observation) > 200 else step.observation
            lines.append(f"👀 Observation: {obs}")
        if step.final_answer:
            lines.append(f"✅ Final Answer: {step.final_answer}")
        lines.append("")
    return "\n".join(lines)

def get_status_emoji(status: str) -> str:
    """Get emoji for status."""
    emojis = {
        "pending": "⏳",
        "in-progress": "🔄",
        "completed": "✅",
        "error": "❌"
    }
    return emojis.get(status, "⏳")

# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/artificial-intelligence.png", width=80)
    st.title("🧠 Planning Agent")
    st.caption("v2.0 - With Tools & Planning")
    
    st.divider()
    
    # Model info
    st.subheader("🧠 Model")
    st.info("**GPT-4o-mini**")
    
    st.divider()
    
    # Available Tools
    st.subheader("🛠️ Available Tools")
    tools = [
        ("🧮 Calculator", "Math operations"),
        ("🌤️ Weather", "Real weather API"),
        ("✈️ Flights", "Flight search"),
        ("🏨 Hotels", "Hotel search"),
        ("💱 Currency", "Exchange rates"),
        ("🔍 Search", "Web search"),
        ("📅 Calendar", "Date utilities"),
        ("🗺️ Maps", "Location services")
    ]
    
    for tool_name, tool_desc in tools:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; padding: 4px 0;">
            <span style="font-size: 1.2em;">{tool_name}</span>
            <span style="font-size: 0.8em; color: #6c757d;">- {tool_desc}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Stats
    st.subheader("📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tasks", len(st.session_state.subtasks))
    with col2:
        st.metric("Messages", len(st.session_state.messages))
    
    st.divider()
    
    # Help
    with st.expander("💡 How to Use", expanded=False):
        st.markdown("""
        1. **Enter your goal** in the chat box
        2. **Agent decomposes** the task into subtasks
        3. **Each subtask is solved** using ReAct
        4. **Final report** shows all results
        
        **Example Queries:**
        - "Plan a 3-day trip to Paris"
        - "Search for top restaurants in Tokyo"
        - "Compare flights from NYC to London"
        - "What's the weather in Barcelona?"
        """)
    
    st.divider()
    
    # Footer
    st.caption("Made with ❤️ using Streamlit + OpenRouter")

# ============================================================================
# Main Chat Area
# ============================================================================

# Header
st.markdown("""
<div class="header">
    <h1>🧠 Planning Agent</h1>
    <p>I can plan complex tasks, search the web, check weather, convert currency, and more!</p>
</div>
""", unsafe_allow_html=True)

# Progress bar if running
if st.session_state.is_running:
    progress = 0
    if st.session_state.total_subtasks > 0:
        progress = st.session_state.current_subtask / st.session_state.total_subtasks
    st.progress(progress, text=f"Processing subtask {st.session_state.current_subtask + 1}/{st.session_state.total_subtasks}...")

# Display subtasks and steps
if st.session_state.subtasks:
    st.subheader("📋 Task Breakdown")
    
    for idx, subtask in enumerate(st.session_state.subtasks):
        status = "completed" if idx < len(st.session_state.answers) else "in-progress" if idx == len(st.session_state.answers) else "pending"
        
        st.markdown(f"""
        <div class="subtask-card {status} fade-in">
            <span class="subtask-number {status}">{idx + 1}</span>
            <strong>{subtask}</strong>
            <span style="float: right;">
                <span class="status-badge {status}">{get_status_emoji(status)} {status.title()}</span>
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Show answer if available
        if idx < len(st.session_state.answers):
            with st.expander(f"✅ Subtask {idx + 1} Result", expanded=False):
                st.markdown(st.session_state.answers[idx])
        
        # Show steps if available
        if idx < len(st.session_state.steps):
            with st.expander(f"🧠 ReAct Steps for Subtask {idx + 1}", expanded=False):
                steps = st.session_state.steps[idx]
                for i, step in enumerate(steps, 1):
                    step_class = "thought"
                    if step.action:
                        step_class = "action"
                    elif step.observation:
                        step_class = "observation"
                    elif step.final_answer:
                        step_class = "final"
                    
                    st.markdown(f"""
                    <div class="thought-step {step_class}">
                        <strong>Step {i}</strong><br>
                        💭 <strong>Thought:</strong> {step.thought or "Processing..."}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if step.action:
                        st.markdown(f"""
                        <div class="thought-step action" style="margin-left: 20px;">
                            🔧 <strong>Action:</strong> {step.action}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if step.action_input:
                        st.markdown(f"""
                        <div class="thought-step action" style="margin-left: 40px;">
                            📥 <strong>Action Input:</strong> {step.action_input}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if step.observation:
                        obs = step.observation[:300] + "..." if len(step.observation) > 300 else step.observation
                        st.markdown(f"""
                        <div class="thought-step observation" style="margin-left: 20px;">
                            👀 <strong>Observation:</strong> {obs}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if step.final_answer:
                        st.markdown(f"""
                        <div class="thought-step final" style="margin-left: 20px;">
                            ✅ <strong>Final Answer:</strong> {step.final_answer}
                        </div>
                        """, unsafe_allow_html=True)

# Display chat messages
st.divider()
st.subheader("💬 Conversation")

chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                <div style="background: #dcf8c6; padding: 12px 16px; border-radius: 18px 18px 4px 18px; max-width: 80%;">
                    <b>👤 You</b><br>
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                <div style="background: white; padding: 12px 16px; border-radius: 18px 18px 18px 4px; max-width: 80%; border: 1px solid #e0e0e0;">
                    <b>🧠 Agent</b><br>
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# Chat Input
# ============================================================================

with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([8, 1])
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Describe a task you want to solve...",
            key="chat_input",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.form_submit_button("📤 Send", use_container_width=True)

# ============================================================================
# Process Message
# ============================================================================

def initialize_agent():
    """Initialize the planning agent."""
    if st.session_state.agent is None:
        memory = TokenWindowMemory(model="gpt-4o-mini", max_tokens=1500)
        agent = BaseAgent(
            system_prompt="You are a careful AI assistant. Reason step by step, call tools when needed.",
            memory=memory,
            temperature=0.2,
        )
        
        tools = [
            CalculatorTool(),
            WeatherTool(),
            FlightSearchTool(),
            HotelSearchTool(),
            CurrencyConverterTool(),
            SearchTool(),
            CalendarTool(),
            MapsTool()
        ]
        
        st.session_state.agent = agent
        st.session_state.planner = ReActPlanner(tools=tools, max_steps=8)
        st.session_state.decomposer = TaskDecomposer(max_steps=5)

def process_message(user_input):
    """Process a user message."""
    if not user_input:
        return
    
    # Initialize agent if needed
    initialize_agent()
    
    # Add user message
    st.session_state.messages.append({
        'role': 'user',
        'content': user_input
    })
    
    # Reset state
    st.session_state.subtasks = []
    st.session_state.answers = []
    st.session_state.steps = []
    st.session_state.is_running = True
    st.session_state.current_subtask = 0
    
    try:
        # Add initial thinking message
        st.session_state.messages.append({
            'role': 'assistant',
            'content': "🧠 Let me analyze your request and break it down into manageable steps..."
        })
        
        # Decompose task
        subtasks = st.session_state.decomposer.decompose(
            goal=user_input,
            agent=st.session_state.agent
        )
        
        if not subtasks:
            subtasks = [user_input]
        
        st.session_state.subtasks = subtasks
        st.session_state.total_subtasks = len(subtasks)
        
        # Solve each subtask
        for idx, subtask in enumerate(subtasks):
            st.session_state.current_subtask = idx
            
            # Update status message
            status_msg = f"🔄 Solving subtask {idx + 1}/{len(subtasks)}: {subtask[:50]}..."
            st.session_state.messages.append({
                'role': 'assistant',
                'content': status_msg
            })
            
            # Solve subtask
            answer, steps = st.session_state.planner.run(
                question=subtask,
                agent=st.session_state.agent
            )
            
            st.session_state.answers.append(answer)
            st.session_state.steps.append(steps)
        
        # Final report
        report = "📋 **Final Report**\n\n"
        for idx, (subtask, answer) in enumerate(zip(st.session_state.subtasks, st.session_state.answers), 1):
            report += f"**{idx}. {subtask}**\n"
            report += f"   {answer[:200]}{'...' if len(answer) > 200 else ''}\n\n"
        
        st.session_state.messages.append({
            'role': 'assistant',
            'content': report
        })
        
    except Exception as e:
        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"❌ Error: {str(e)}"
        })
    
    finally:
        st.session_state.is_running = False

# Process message when form is submitted
if send_button and user_input:
    process_message(user_input)

# ============================================================================
# Quick Action Buttons
# ============================================================================

st.divider()
st.caption("💡 Quick Actions")

cols = st.columns(4)
quick_actions = [
    ("✈️ Trip", "Plan a 3-day trip to Paris with a budget of $2000"),
    ("🌤️ Weather", "What's the weather forecast for Tokyo next week?"),
    ("🍽️ Restaurants", "Find the best Italian restaurants in Rome"),
    ("💱 Currency", "Convert 1000 USD to EUR")
]

for i, (label, msg) in enumerate(quick_actions):
    with cols[i]:
        if st.button(label, key=f"qa_{i}", use_container_width=True):
            process_message(msg)
            st.rerun()

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("🧠 Planning Agent with ReAct + Task Decomposition | Powered by OpenRouter + Streamlit")