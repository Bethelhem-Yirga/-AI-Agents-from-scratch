"""
🌐 AI Agent Web Interface - Streamlit Version
A beautiful web UI for your AI agent with tools and memory
"""

import os
import json
import sys
import ast
import builtins
from pathlib import Path
import streamlit as st
from datetime import datetime

# Add the current directory to path so we can import the agent
sys.path.append(os.path.dirname(__file__))

# Import your agent
from tool_agent import ToolAgent, get_real_weather, get_weather_forecast

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="AI Agent",
    page_icon="🤖",
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
    
    /* Chat messages */
    .user-message {
        background-color: #dcf8c6;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        float: right;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background-color: #ffffff;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        float: left;
        clear: both;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    .tool-call {
        background-color: #fff3cd;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 4px 0;
        font-size: 0.9em;
        font-family: monospace;
        border-left: 3px solid #ffc107;
        clear: both;
    }
    
    /* Sidebar */
    .sidebar-content {
        padding: 20px;
    }
    
    /* Memory display */
    .memory-item {
        background-color: #f8f9fa;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        font-size: 0.9em;
        border-left: 3px solid #6c757d;
    }
    
    /* Tool cards */
    .tool-card {
        background-color: white;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 6px 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .tool-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Initialize Session State
# ============================================================================

if 'agent' not in st.session_state:
    st.session_state.agent = ToolAgent()
    st.session_state.messages = []
    st.session_state.tool_calls = []
    st.session_state.memory_visible = False


# ============================================================================
# ✅ MESSAGE PROCESSING FUNCTION - DEFINED BEFORE IT'S USED
# ============================================================================

def process_message(user_input):
    """Process a user message and generate a response."""
    if not user_input:
        return
    
    # Add user message to chat
    st.session_state.messages.append({
        'role': 'user',
        'content': user_input
    })
    
    # Check for special commands
    if user_input.startswith('/'):
        command = user_input.lower()
        if command == '/tools':
            tools_list = "\n".join([f"• {t}" for t in st.session_state.agent.tool_registry.get_tool_names()])
            response = f"📚 **Available Tools:**\n\n{tools_list}"
            st.session_state.messages.append({
                'role': 'assistant',
                'content': response
            })
        elif command == '/memory':
            st.session_state.memory_visible = True
            st.session_state.messages.append({
                'role': 'assistant',
                'content': "📖 Memory viewer opened in the sidebar!"
            })
        elif command == '/clear':
            st.session_state.messages = []
            st.session_state.tool_calls = []
            st.session_state.messages.append({
                'role': 'assistant',
                'content': "🧹 Chat history cleared!"
            })
        elif command == '/forget':
            st.session_state.agent.memory.clear_long_term()
            st.session_state.messages.append({
                'role': 'assistant',
                'content': "🗑️ All long-term memories forgotten!"
            })
        else:
            st.session_state.messages.append({
                'role': 'assistant',
                'content': f"Unknown command: {command}. Try: /tools, /memory, /clear, /forget"
            })
    else:
        # Generate response using the agent
        try:
            # Capture tool calls
            tool_calls_captured = []
            original_print = builtins.print
            
            # Override print to capture tool calls
            def capture_print(*args, **kwargs):
                msg = ' '.join(str(a) for a in args)
                if 'Calling' in msg:
                    parts = msg.split('Calling ')[-1].split(' with ')
                    if len(parts) == 2:
                        tool_name = parts[0]
                        try:
                            # Parse arguments safely
                            args_str = parts[1]
                            try:
                                args_dict = ast.literal_eval(args_str)
                            except:
                                args_dict = {}
                            tool_calls_captured.append({
                                'tool': tool_name,
                                'args': args_dict,
                                'result': 'Processing...'
                            })
                        except:
                            pass
                original_print(*args, **kwargs)
            
            # Redirect print to capture tool calls
            builtins.print = capture_print
            
            # Generate response
            response = st.session_state.agent.generate_response(user_input)
            
            # Restore print
            builtins.print = original_print
            
            # Add tool calls to session state
            message_index = len(st.session_state.messages)
            for tc in tool_calls_captured:
                # Get actual result by re-executing the tool
                try:
                    tool_name = tc['tool']
                    tool_args = tc.get('args', {})
                    
                    # Execute the tool to get the result
                    result = st.session_state.agent.tool_registry.execute(tool_name, **tool_args)
                    result_str = json.dumps(result, indent=2)
                except Exception as e:
                    result_str = f"Error: {str(e)}"
                
                st.session_state.tool_calls.append({
                    'tool': tc['tool'],
                    'args': tc.get('args', {}),
                    'result': result_str,
                    'message_index': message_index
                })
            
            # Add response to chat
            st.session_state.messages.append({
                'role': 'assistant',
                'content': response
            })
            
        except Exception as e:
            st.session_state.messages.append({
                'role': 'assistant',
                'content': f"❌ Error: {str(e)}"
            })
    
    # Trigger rerun to update the UI
    st.rerun()


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/chatbot.png", width=80)
    st.title("🤖 AI Agent")
    st.caption("v1.0 - With Tools & Memory")
    
    st.divider()
    
    # Model info
    st.subheader("🧠 Model")
    st.info(f"**{st.session_state.agent.llm.model}**")
    
    st.divider()
    
    # Tools section
    st.subheader("🛠️ Available Tools")
    tools = st.session_state.agent.tool_registry.get_tool_names()
    
    tool_icons = {
        "calculator": "🧮",
        "get_current_time": "⏰",
        "get_real_weather": "🌤️",
        "get_weather_forecast": "📅",
        "search_web": "🔍"
    }
    
    for tool in tools:
        icon = tool_icons.get(tool, "🔧")
        st.markdown(f"""
        <div class="tool-card">
            {icon} <b>{tool}</b>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Memory section
    st.subheader("🧠 Memory")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 Show Memory", use_container_width=True):
            st.session_state.memory_visible = not st.session_state.memory_visible
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Memory", use_container_width=True):
            st.session_state.agent.memory.clear_long_term()
            st.rerun()
    
    if st.session_state.memory_visible:
        st.divider()
        st.subheader("💾 Stored Memories")
        
        long_term = st.session_state.agent.memory.get_long_term()
        if long_term:
            for mem in long_term[-10:]:
                st.markdown(f"""
                <div class="memory-item">
                    📌 {mem['content'][:100]}{'...' if len(mem['content']) > 100 else ''}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No memories stored yet.")
        
        st.caption(f"Total: {len(long_term)} memories")
    
    st.divider()
    
    # Stats
    st.subheader("📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Tools", len(tools))
    st.metric("Memories", len(st.session_state.agent.memory.get_long_term()))
    
    st.divider()
    
    # Commands
    with st.expander("⌨️ Commands", expanded=False):
        st.code("""
        Commands in chat:
        • /tools - List tools
        • /memory - Show memory
        • /clear - Clear chat
        • /forget - Clear memory
        """)
    
    st.divider()
    
    # Footer
    st.caption("Made with ❤️ using Streamlit + OpenRouter")

# ============================================================================
# Main Chat Area
# ============================================================================

# Header
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.title("💬 AI Agent Chat")
    st.caption("Ask me anything! I have tools for math, weather, time, and search.")

st.divider()

# Chat container
chat_container = st.container()

# Display messages
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #6c757d;">
            <p style="font-size: 1.2em;">👋 Welcome to your AI Agent!</p>
            <p>Try asking me something like:</p>
            <div style="display: inline-block; text-align: left; margin: 10px auto;">
                <code>📐 What is 1234 × 5678?</code><br>
                <code>🌤️ What's the weather in Tokyo?</code><br>
                <code>⏰ What time is it in London?</code><br>
                <code>📅 Give me a 5-day forecast for Paris</code><br>
                <code>🧠 My name is Alex and I love pizza</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, msg in enumerate(st.session_state.messages):
            if msg['role'] == 'user':
                st.markdown(f"""
                <div class="user-message">
                    <b>👤 You</b><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Check if there are tool calls associated with this message
                tool_calls = [tc for tc in st.session_state.tool_calls if tc.get('message_index') == i]
                
                if tool_calls:
                    for tc in tool_calls:
                        result_preview = tc['result'][:100] + '...' if len(tc['result']) > 100 else tc['result']
                        st.markdown(f"""
                        <div class="tool-call">
                            🔧 <b>{tc['tool']}</b> → {result_preview}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="assistant-message">
                    <b>🤖 Agent</b><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)

# ============================================================================
# Chat Input
# ============================================================================

# Use a form to handle input properly
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([8, 1])
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Type your message here...",
            key="chat_input",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.form_submit_button("📤 Send", use_container_width=True)

# Process message when form is submitted
if send_button and user_input:
    process_message(user_input)

# ============================================================================
# Quick Action Buttons
# ============================================================================

st.divider()
st.caption("💡 Quick Actions")

cols = st.columns(5)
quick_actions = [
    ("🧮 Math", "What is 1234 × 5678?"),
    ("🌤️ Weather", "What's the weather in Tokyo?"),
    ("⏰ Time", "What time is it in London?"),
    ("📅 Forecast", "Give me a 5-day forecast for Paris"),
    ("🧠 Memory", "My name is Alex and I love pizza")
]

for i, (label, msg) in enumerate(quick_actions):
    with cols[i]:
        if st.button(label, key=f"qa_{i}", use_container_width=True):
            process_message(msg)

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("🤖 AI Agent with Tools & Memory | Powered by OpenRouter + Streamlit")