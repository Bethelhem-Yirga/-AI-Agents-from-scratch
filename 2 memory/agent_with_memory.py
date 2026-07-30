"""
Tutorial 02: AI Agent with Memory (OpenRouter Version)
Demonstrates various memory implementations using OpenRouter's free models.
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv


class MemoryAgent:
    """
    An AI agent with basic conversation memory using OpenRouter.
    
    This agent maintains a full conversation history, allowing it to
    remember all previous interactions in the current session.
    """

    def __init__(self, 
                 model="google/gemma-4-26b-a4b-it:free", 
                 system_prompt=None,
                 temperature=0.7,
                 max_tokens=500):
        """Initialize agent with memory capabilities."""
        load_dotenv()
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Get OpenRouter API key
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Please set it in your .env file.\n"
                "Get your free key at: https://openrouter.ai/keys"
            )

        # Set system prompt
        self.system_prompt = system_prompt or "You are a helpful AI assistant."

        # 🧠 CONVERSATION HISTORY
        self.conversation_history = []
        
        print(f"✅ MemoryAgent initialized!")
        print(f"📊 Model: {self.model}")
        print(f"🌡️  Temperature: {self.temperature}")
        print(f"📝 Max tokens: {self.max_tokens}")
        print(f"🧠 Memory: Enabled\n")

    def add_to_history(self, role, content):
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_context_messages(self):
        """Build message list with system prompt and history."""
        return [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

    def generate_response(self, user_message):
        """Generate a response with full conversation context."""
        # Add user message to history
        self.add_to_history("user", user_message)

        # Build messages with context
        messages = self.get_context_messages()

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            # Make API call
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content']
                
                # Add agent response to history
                self.add_to_history("assistant", response_text)
                return response_text
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"API Error ({response.status_code}): {error_msg}")
                
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error: Could not reach OpenRouter API.")
        except requests.exceptions.Timeout:
            raise Exception("Timeout: The request took too long.")

    def run(self):
        """Run interactive conversation loop."""
        print("\n" + "="*60)
        print("🧠 Memory Agent - Interactive Mode")
        print("="*60)
        print("This agent remembers your conversation!")
        print("Type 'quit' to exit, 'history' to see conversation history.")
        print("="*60 + "\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nAgent: Goodbye!\n")
                break

            if user_input.lower() == 'history':
                self.show_history()
                continue

            if not user_input:
                continue

            try:
                print("\nAgent: ", end="", flush=True)
                response = self.generate_response(user_input)
                print(f"{response}\n")
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    def show_history(self):
        """Display conversation history."""
        print("\n" + "="*60)
        print("📜 Conversation History")
        print("="*60)
        
        if not self.conversation_history:
            print("  (No conversation yet)")
        else:
            for i, msg in enumerate(self.conversation_history, 1):
                role = msg['role'].capitalize()
                content = msg['content']
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"{i:2d}. {role}: {content}")
        
        print("="*60 + f" ({len(self.conversation_history)} messages)\n")


class BufferMemoryAgent(MemoryAgent):
    """
    An agent with buffer memory (sliding window).
    
    Keeps only the last N messages to avoid exceeding token limits.
    """

    def __init__(self, 
                 model="google/gemma-4-26b-a4b-it:free",
                 system_prompt=None,
                 temperature=0.7,
                 max_tokens=500,
                 max_history=10):
        """
        Initialize agent with buffer memory.

        Args:
            max_history: Maximum number of messages to keep in memory
        """
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.max_history = max_history

    def add_to_history(self, role, content):
        """Add message and maintain buffer size."""
        super().add_to_history(role, content)

        # Keep only last max_history messages
        if len(self.conversation_history) > self.max_history:
            removed = self.conversation_history.pop(0)
            print(f"  🔄 BUFFER: Forgot: '{removed['content'][:30]}...'")
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_memory_info(self):
        """Get information about memory usage."""
        return {
            "current_messages": len(self.conversation_history),
            "max_messages": self.max_history,
            "buffer_full": len(self.conversation_history) >= self.max_history
        }

    def run(self):
        """Enhanced run with buffer info."""
        print("\n" + "="*60)
        print("🧠 Buffer Memory Agent - Interactive Mode")
        print("="*60)
        print(f"📊 Buffer Size: {self.max_history}")
        print("I remember the last N messages!")
        print("Type 'quit' to exit, 'history' to see conversation history.")
        print("="*60 + "\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nAgent: Goodbye!\n")
                break

            if user_input.lower() == 'history':
                self.show_history()
                continue

            if user_input.lower() == 'info':
                info = self.get_memory_info()
                print(f"\n📊 Memory Info: {info}\n")
                continue

            if not user_input:
                continue

            try:
                print("\nAgent: ", end="", flush=True)
                response = self.generate_response(user_input)
                print(f"{response}\n")
                
                # Show buffer status
                info = self.get_memory_info()
                print(f"📊 Buffer: {info['current_messages']}/{info['max_messages']}")
                
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


class PersistentMemoryAgent(BufferMemoryAgent):
    """
    An agent that can save and load conversations from disk.
    """

    def __init__(self, 
                 model="google/gemma-4-26b-a4b-it:free",
                 system_prompt=None,
                 temperature=0.7,
                 max_tokens=500,
                 max_history=10,
                 memory_file="conversation_memory.json"):
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history=max_history
        )
        self.memory_file = memory_file
        self.load_conversation(memory_file)

    def save_conversation(self, filename=None):
        """Save conversation to a JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"

        data = {
            "system_prompt": self.system_prompt,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_history": self.max_history,
            "timestamp": datetime.now().isoformat(),
            "history": self.conversation_history
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Conversation saved to {filename}")
        return filename

    def load_conversation(self, filename):
        """Load conversation from a JSON file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.conversation_history = data.get("history", [])
            if "system_prompt" in data:
                self.system_prompt = data["system_prompt"]
            if "max_history" in data:
                self.max_history = data["max_history"]

            print(f"✅ Loaded {len(self.conversation_history)} messages from {filename}")
            return len(self.conversation_history)
        except FileNotFoundError:
            print(f"ℹ️  No existing memory file: {filename}")
            return 0
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON in {filename}, starting fresh")
            return 0

    def clear_history(self):
        """Clear conversation history."""
        message_count = len(self.conversation_history)
        self.conversation_history = []
        print(f"🧹 Cleared {message_count} messages from history.")
        return message_count

    def run(self):
        """Enhanced run with save/load commands."""
        print("\n" + "="*60)
        print("💾 Persistent Memory Agent - Interactive Mode")
        print("="*60)
        print(f"📊 Memory File: {self.memory_file}")
        print(f"📊 Buffer Size: {self.max_history}")
        print("\nCommands:")
        print("  • 'quit' - Exit")
        print("  • 'history' - Show conversation history")
        print("  • 'save' - Save conversation to file")
        print("  • 'save <filename>' - Save to specific file")
        print("  • 'load <filename>' - Load conversation from file")
        print("  • 'clear' - Clear conversation history")
        print("  • 'info' - Show memory info")
        print("="*60 + "\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                # Auto-save before exit
                self.save_conversation(self.memory_file)
                print("\nAgent: Goodbye! Memory saved.\n")
                break

            if user_input.lower() == 'history':
                self.show_history()
                continue

            if user_input.lower() == 'save':
                self.save_conversation(self.memory_file)
                continue

            if user_input.lower().startswith('save '):
                filename = user_input[5:].strip()
                self.save_conversation(filename)
                continue

            if user_input.lower().startswith('load '):
                filename = user_input[5:].strip()
                self.load_conversation(filename)
                continue

            if user_input.lower() == 'clear':
                self.clear_history()
                continue

            if user_input.lower() == 'info':
                info = self.get_memory_info()
                print(f"\n📊 Memory Info: {info}\n")
                continue

            if not user_input:
                continue

            try:
                print("\nAgent: ", end="", flush=True)
                response = self.generate_response(user_input)
                print(f"{response}\n")
                
                # Show buffer status
                info = self.get_memory_info()
                print(f"📊 Buffer: {info['current_messages']}/{info['max_messages']}")
                
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


# ============================================
# DEMONSTRATION FUNCTIONS
# ============================================

def demo_basic_memory():
    """Demonstrate basic memory functionality."""
    print("\n" + "="*70)
    print("📖 DEMO 1: Basic Memory")
    print("="*70)
    
    agent = MemoryAgent()

    questions = [
        "My name is Sarah",
        "I love Python programming",
        "What's my name?",
        "What do I like?"
    ]

    for q in questions:
        print(f"\nYou: {q}")
        response = agent.generate_response(q)
        print(f"Agent: {response}")


def demo_buffer_memory():
    """Demonstrate buffer memory with size limits."""
    print("\n" + "="*70)
    print("📖 DEMO 2: Buffer Memory")
    print("="*70)
    
    agent = BufferMemoryAgent(max_history=4)

    # Add more messages than buffer can hold
    for i in range(6):
        print(f"\nYou: Message {i+1}")
        agent.generate_response(f"This is message number {i+1}")
        info = agent.get_memory_info()
        print(f"📊 Buffer: {info['current_messages']}/{info['max_messages']}")

    print(f"\n🎯 Final buffer size: {len(agent.conversation_history)}")
    print("(Should be 4, as older messages were removed)")


def demo_persistent_memory():
    """Demonstrate persistent memory across sessions."""
    print("\n" + "="*70)
    print("📖 DEMO 3: Persistent Memory")
    print("="*70)
    
    # Session 1
    print("\n🔹 SESSION 1:")
    agent1 = PersistentMemoryAgent(memory_file="test_memory.json")
    
    agent1.generate_response("My name is Alex")
    agent1.generate_response("I live in New York")
    agent1.generate_response("I love pizza")
    
    print("\n💾 Saving memory...")
    agent1.save_conversation("test_memory.json")
    
    # Session 2 (new agent)
    print("\n🔹 SESSION 2 (New Agent):")
    agent2 = PersistentMemoryAgent(memory_file="test_memory.json")
    
    print("\n✅ Memory loaded!")
    print(f"📊 Messages in history: {len(agent2.conversation_history)}")
    
    response = agent2.generate_response("What do you know about me?")
    print(f"\nAgent: {response}")

    # Clean up
    import os
    if os.path.exists("test_memory.json"):
        os.remove("test_memory.json")
        print("\n🧹 Test memory file cleaned up")


# ============================================
# EXERCISE: Chef Agent with Memory
# ============================================

def exercise_chef_with_memory():
    """
    Exercise: Create a Chef Agent with Persistent Memory
    
    This combines the chef personality from Tutorial 01
    with persistent memory from Tutorial 02.
    """
    
    chef_prompt = """You are a professional chef assistant with a passion for cooking!

    CHARACTER TRAITS:
    - You LOVE cooking and sharing your culinary knowledge
    - You are patient, encouraging, and supportive of all skill levels
    - You remember what dishes users have tried before
    - You give personalized recipe recommendations

    YOUR RESPONSIBILITIES:
    - Provide clear, step-by-step recipes
    - Remember user's dietary preferences
    - Suggest dishes based on past preferences
    - Offer cooking tips and techniques

    SAFETY FIRST:
    - Always mention food safety
    - Remind about potential allergens
    """

    print("\n" + "="*70)
    print("🍳 CHEF AGENT WITH MEMORY")
    print("="*70)
    print("This chef remembers your preferences and past conversations!")
    print("\nFeatures:")
    print("  • Remembers your dietary restrictions")
    print("  • Suggests recipes based on past likes")
    print("  • Saves conversation to file")
    print("  • Loads previous conversations\n")

    agent = PersistentMemoryAgent(
        model="google/gemma-4-26b-a4b-it:free",
        system_prompt=chef_prompt,
        max_history=15,
        memory_file="chef_memory.json"
    )
    
    agent.run()


# ============================================
# MAIN MENU
# ============================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧠 TUTORIAL 02: MEMORY AGENTS (OpenRouter Version)")
    print("="*70)
    print("\nChoose a demo:")
    print("  1. Basic Memory Agent")
    print("  2. Buffer Memory Agent (Sliding Window)")
    print("  3. Persistent Memory Agent (Save/Load)")
    print("  4. Demo: Basic Memory")
    print("  5. Demo: Buffer Memory")
    print("  6. Demo: Persistent Memory")
    print("  7. 🍳 Chef Agent with Memory (Exercise)")
    print("  8. All Demos")
    print("  q. Quit")
    
    choice = input("\nYour choice: ").strip()
    
    if choice == "1":
        agent = MemoryAgent()
        agent.run()
    elif choice == "2":
        agent = BufferMemoryAgent(max_history=10)
        agent.run()
    elif choice == "3":
        agent = PersistentMemoryAgent()
        agent.run()
    elif choice == "4":
        demo_basic_memory()
    elif choice == "5":
        demo_buffer_memory()
    elif choice == "6":
        demo_persistent_memory()
    elif choice == "7":
        exercise_chef_with_memory()
    elif choice == "8":
        demo_basic_memory()
        print("\n" + "="*70)
        demo_buffer_memory()
        print("\n" + "="*70)
        demo_persistent_memory()
    elif choice.lower() == 'q':
        print("\nGoodbye! 🧠👋\n")
    else:
        print("Invalid choice. Running basic agent...")
        agent = MemoryAgent()
        agent.run()