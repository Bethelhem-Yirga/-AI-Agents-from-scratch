"""
Tutorial 01: Simple AI Agent (OpenRouter Version)
A basic conversational AI agent using OpenRouter's API with free models.
"""

import os
import requests
import json
from dotenv import load_dotenv


class SimpleAgentOpenRouter:
    """
    A simple AI agent that can have conversations using OpenRouter.
    """

    def __init__(self, model="google/gemma-4-26b-a4b-it:free", 
                 system_prompt=None, temperature=0.7, max_tokens=1000):
        """
        Initialize the agent with OpenRouter model and system prompt.

        Args:
            model (str): The OpenRouter model to use
            system_prompt (str): Instructions that define agent behavior
            temperature (float): Creativity level (0.0 to 2.0)
            max_tokens (int): Maximum length of response
        """
        # Load environment variables
        load_dotenv()

        self.model = model
        self.temperature = temperature  # ← Store temperature
        self.max_tokens = max_tokens    # ← Store max_tokens
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        # Get OpenRouter API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Please set it in your .env file.\n"
                "Get your free key at: https://openrouter.ai/keys"
            )

        self.api_key = api_key

        # Set default system prompt
        self.system_prompt = system_prompt or """You are a helpful AI assistant.
You provide clear, concise, and accurate responses to user questions.
You are friendly and professional."""

        print(f"✅ Agent initialized with model: {self.model}")
        print(f"🌡️  Temperature: {self.temperature}")
        print(f"📝 Max tokens: {self.max_tokens}")
        print(f"💡 Using OpenRouter - Free tier!\n")

    def generate_response(self, user_message):
        """
        Generate a response to a user message using OpenRouter.

        Args:
            user_message (str): The user's input text

        Returns:
            str: The agent's response
        """
        # Prepare the headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Prepare the request data
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": self.max_tokens,  # ← Use stored value
            "temperature": self.temperature  # ← Use stored value
        }

        # Make the API call
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                # Handle API errors
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                
                # Special handling for model errors
                if "unavailable" in str(error_msg).lower() or "404" in str(response.status_code):
                    raise Exception(f"Model '{self.model}' is not available. Try one of these free models:\n"
                                  f"  • google/gemini-2.0-flash-exp:free (RECOMMENDED)\n"
                                  f"  • mistralai/mistral-7b-instruct:free\n"
                                  f"  • qwen/qwen-2.5-7b-instruct:free\n"
                                  f"  • deepseek/deepseek-chat:free\n"
                                  f"  • microsoft/phi-3.5-mini-128k-instruct:free")
                else:
                    raise Exception(f"API Error ({response.status_code}): {error_msg}")
                
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error: Could not reach OpenRouter API. Check your internet.")
        except requests.exceptions.Timeout:
            raise Exception("Timeout: The request took too long. Try again.")

    def run(self):
        """
        Run the agent in an interactive loop.
        """
        print("\n" + "="*60)
        print("Simple AI Agent (OpenRouter) - Interactive Mode")
        print("="*60)
        print(f"🤖 Model: {self.model}")
        print(f"🌡️  Temperature: {self.temperature}")
        print("\nAgent: Hello! I'm your AI assistant powered by OpenRouter.")
        print("       Type your message and press Enter.")
        print("       Type 'quit', 'exit', or 'bye' to end the conversation.")
        print("="*60 + "\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nAgent: Goodbye! Have a great day!\n")
                break

            if not user_input:
                continue

            try:
                print("\nAgent: ", end="", flush=True)
                response = self.generate_response(user_input)
                print(f"{response}\n")

            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'quit' to exit.\n")


# ============================================
# EXERCISE 1: CHEF AGENT SOLUTION
# ============================================

def exercise_1_chef_agent():
    """
    Exercise 1: Create a Chef Assistant Agent

    Goal: Modify the system prompt to create a cooking assistant

    Example questions to try:
    - "How do I make pasta carbonara?"
    - "What's a good beginner recipe?"
    - "How do I dice an onion?"
    """
    
    # ✅ COMPLETED: Professional Chef System Prompt
    chef_prompt = """You are a professional chef assistant with a passion for cooking!

    CHARACTER TRAITS:
    - You LOVE cooking and sharing your culinary knowledge
    - You are patient, encouraging, and supportive of all skill levels
    - You have a warm, friendly personality with a dash of humor
    - You believe anyone can cook with the right guidance
    - You're enthusiastic about food and flavor combinations

    YOUR RESPONSIBILITIES:
    - Provide clear, step-by-step recipes with exact measurements
    - Include preparation time, cooking time, and serving size
    - Suggest ingredient substitutions for dietary restrictions
    - Explain cooking techniques and WHY they work
    - Give pro tips to elevate dishes
    - Offer wine pairings when appropriate
    - Help troubleshoot cooking problems

    FORMAT YOUR RESPONSES:
    - Use bullet points and numbered steps for clarity
    - Separate ingredients and instructions
    - Highlight important tips with emojis (🍳, 🔥, 💡, ✨)
    - Keep responses organized and easy to follow

    SAFETY FIRST:
    - Always mention food safety (cooking temperatures, storage)
    - Remind about potential allergens
    - Suggest modifications for dietary restrictions

    Remember: Every great chef started with their first meal. Be encouraging and make cooking fun! 🍽️
    """

    # Create the chef agent
    print("="*60)
    print("🍳 EXERCISE 1: CHEF ASSISTANT AGENT")
    print("="*60)
    print("✅ Chef prompt completed!")
    print("👨‍🍳 Creating your personal cooking assistant...\n")
    
    # Create agent with chef personality
    agent = SimpleAgentOpenRouter(
        model="google/gemma-4-26b-a4b-it:free",  # ← FIXED: Use working model
        system_prompt=chef_prompt,
        temperature=0.7,    # Balanced for clear instructions
        max_tokens=1500     # Allow long recipe responses
    )
    
    # Custom welcome message
    print("\n" + "="*60)
    print("🍳 WELCOME TO YOUR CHEF ASSISTANT! 🍳")
    print("="*60)
    print("👨‍🍳 I'm your personal chef assistant!")
    print("📋 I can help you with:")
    print("   • Recipes for any dish")
    print("   • Cooking techniques and tips")
    print("   • Ingredient substitutions")
    print("   • Meal planning ideas")
    print("   • Troubleshooting cooking problems")
    print("\n💡 Try asking me:")
    print("   'How do I make pasta carbonara?'")
    print("   'What's a good beginner recipe?'")
    print("   'How do I dice an onion properly?'")
    print("="*60 + "\n")
    
    # Run the agent
    agent.run()


# ============================================
# MAIN - RUN THE EXERCISE
# ============================================

if __name__ == "__main__":
    # Run the chef agent directly
    exercise_1_chef_agent()