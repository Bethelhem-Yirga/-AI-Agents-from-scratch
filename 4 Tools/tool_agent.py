"""
Tutorial 03: AI Agent with Tools (OpenRouter Version)
Demonstrates how to build agents that can use external tools and functions.
Uses OpenRouter's free API for LLM integration.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests


# ============================================================================
# Load .env from parent directory (project root)
# ============================================================================
# Get the parent directory of this script (project root)
script_dir = Path(__file__).parent
project_root = script_dir.parent  # Go up one level
env_path = project_root / '.env'

# Load the .env file from the parent directory
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️ .env file not found at: {env_path}")
    print("📝 Make sure your .env file is in the project root folder")

# ============================================================================
# Tool Functions
# ============================================================================

def calculator(operation, a, b):
    """
    Perform basic mathematical operations.

    Args:
        operation: One of 'add', 'subtract', 'multiply', 'divide'
        a: First number
        b: Second number

    Returns:
        Result of the operation
    """
    operations = {
        'add': lambda x, y: x + y,
        'subtract': lambda x, y: x - y,
        'multiply': lambda x, y: x * y,
        'divide': lambda x, y: x / y if y != 0 else "Error: Division by zero"
    }

    if operation not in operations:
        return f"Error: Unknown operation '{operation}'"

    try:
        result = operations[operation](float(a), float(b))
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def get_current_time(timezone="UTC"):
    """
    Get the current time in a specified timezone.

    Args:
        timezone: Timezone name (e.g., 'UTC', 'EST', 'PST')

    Returns:
        Current time information
    """
    current_time = datetime.now()
    return {
        "timezone": timezone,
        "time": current_time.strftime("%H:%M:%S"),
        "date": current_time.strftime("%Y-%m-%d"),
        "timestamp": current_time.isoformat()
    }


# ============================================================================
# Real Weather Tool
# ============================================================================

def get_real_weather(location, unit="celsius"):
    """
    Get REAL weather information from WeatherAPI.com.
    
    Args:
        location: City name (e.g., 'New York', 'London')
        unit: Temperature unit ('celsius' or 'fahrenheit')
    
    Returns:
        Weather data dictionary with real values
    """
    # Get API key from environment
    api_key = os.getenv("WEATHER_API_KEY")
    
    # Check if API key exists
    if not api_key:
        return {
            "error": "WEATHER_API_KEY not found in .env file. Please add your WeatherAPI.com key."
        }
    
    # Build the API URL
    # WeatherAPI.com endpoint for current weather
    base_url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": api_key,
        "q": location,  # City name
        "aqi": "no"     # Air quality (optional)
    }
    
    try:
        # Make the API call
        response = requests.get(base_url, params=params, timeout=10)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract weather data
            return {
                "location": {
                    "name": data['location']['name'],
                    "region": data['location']['region'],
                    "country": data['location']['country']
                },
                "temperature": data['current']['temp_c'] if unit == "celsius" else data['current']['temp_f'],
                "unit": unit,
                "condition": data['current']['condition']['text'],
                "icon": data['current']['condition']['icon'],
                "humidity": data['current']['humidity'],
                "wind_speed": data['current']['wind_kph'],
                "feels_like": data['current']['feelslike_c'] if unit == "celsius" else data['current']['feelslike_f'],
                "last_updated": data['current']['last_updated']
            }
        
        elif response.status_code == 400:
            # City not found
            return {
                "error": f"City '{location}' not found. Please check the spelling."
            }
        else:
            # Other API errors
            return {
                "error": f"Weather API error: {response.status_code} - {response.text}"
            }
    
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error: Could not reach Weather API. Check your internet."}
    except requests.exceptions.Timeout:
        return {"error": "Timeout: The weather request took too long."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# ============================================================================
# Enhanced Weather Tool with Forecast
# ============================================================================

def get_weather_forecast(location, days=3, unit="celsius"):
    """
    Get REAL weather forecast from WeatherAPI.com.
    
    Args:
        location: City name
        days: Number of days to forecast (1-7)
        unit: Temperature unit ('celsius' or 'fahrenheit')
    
    Returns:
        Forecast data dictionary
    """
    api_key = os.getenv("WEATHER_API_KEY")
    
    if not api_key:
        return {"error": "WEATHER_API_KEY not found in .env file."}
    
    base_url = "https://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": api_key,
        "q": location,
        "days": days,
        "aqi": "no"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            forecast_days = []
            for day in data['forecast']['forecastday']:
                if unit == "celsius":
                    max_temp = day['day']['maxtemp_c']
                    min_temp = day['day']['mintemp_c']
                else:
                    max_temp = day['day']['maxtemp_f']
                    min_temp = day['day']['mintemp_f']
                
                forecast_days.append({
                    "date": day['date'],
                    "max_temperature": max_temp,
                    "min_temperature": min_temp,
                    "condition": day['day']['condition']['text'],
                    "chance_of_rain": day['day']['daily_chance_of_rain'],
                    "chance_of_snow": day['day']['daily_chance_of_snow']
                })
            
            return {
                "location": f"{data['location']['name']}, {data['location']['country']}",
                "unit": unit,
                "forecast": forecast_days
            }
        
        elif response.status_code == 400:
            return {"error": f"City '{location}' not found."}
        else:
            return {"error": f"Weather API error: {response.status_code}"}
    
    except Exception as e:
        return {"error": f"Error: {str(e)}"}



def search_web(query, num_results=3):
    """
    Search the web for information (mock implementation).

    Args:
        query: Search query string
        num_results: Number of results to return

    Returns:
        List of search results
    """
    return {
        "query": query,
        "num_results": num_results,
        "results": [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is information about {query}. Lorem ipsum dolor sit amet..."
            }
            for i in range(num_results)
        ]
    }


# ============================================================================
# Tool Schemas (Function Definitions for OpenRouter)
# ============================================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform basic mathematical operations (add, subtract, multiply, divide)",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The mathematical operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time in a specified timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone name (e.g., 'UTC', 'EST', 'PST')",
                        "default": "UTC"
                    }
                }
            }
        }
    },

     {
        "type": "function",
        "function": {
            "name": "get_real_weather",
            "description": "Get REAL current weather for any city using WeatherAPI.com. Use this instead of the mock version.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name (e.g., 'New York', 'London, UK', 'Tokyo')"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit",
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get REAL weather forecast for a city for the next few days",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of forecast days (1-7)",
                        "default": 3
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit",
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        }
    },
  
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information on a given topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# ============================================================================
# Tool Registry
# ============================================================================

class ToolRegistry:
    """
    Manages available tools for the agent.

    Provides methods to register tools, execute them, and get their schemas.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self.tools = {}
        self.schemas = []

    def register(self, name, function, schema):
        """
        Register a new tool.

        Args:
            name: Tool name
            function: Callable function
            schema: OpenRouter function schema
        """
        self.tools[name] = {
            'function': function,
            'schema': schema
        }
        self.schemas.append(schema)
        print(f"✅ Registered tool: {name}")

    def execute(self, name, **parameters):
        """
        Execute a tool by name with given parameters.

        Args:
            name: Tool name
            **parameters: Tool parameters

        Returns:
            Tool execution result
        """
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}

        try:
            tool_function = self.tools[name]['function']
            result = tool_function(**parameters)
            return result
        except TypeError as e:
            return {"error": f"Invalid parameters: {str(e)}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def get_schemas(self):
        """Get all tool schemas for the LLM."""
        return self.schemas

    def get_tool_names(self):
        """Get list of available tool names."""
        return list(self.tools.keys())


# ============================================================================
# OpenRouter LLM Client
# ============================================================================

class OpenRouterClient:
    """
    OpenRouter API client for LLM interactions.
    Handles chat completions with tool support.
    """

    def __init__(self, model="google/gemma-4-26b-a4b-it:free", temperature=0.7):
        """
        Initialize the OpenRouter client.

        Args:
            model: The model to use (OpenRouter model ID)
            temperature: Temperature for response generation
        """
        load_dotenv()

        self.model = model
        self.temperature = temperature
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Please set it in your .env file.\n"
                "Get your free key at: https://openrouter.ai/keys"
            )

        print(f"🤖 OpenRouter Client initialized with model: {model}")

    def chat_completion(self, messages, tools=None, tool_choice="auto"):
        """
        Send a chat completion request to OpenRouter.

        Args:
            messages: List of message dictionaries
            tools: List of tool schemas (optional)
            tool_choice: Tool choice strategy

        Returns:
            Response object with choices
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",  # Required by OpenRouter
            "X-Title": "Tool Agent"  # Optional but recommended
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1000
        }

        if tools:
            data["tools"] = tools
            data["tool_choice"] = tool_choice

        try:
            response = requests.post(self.base_url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"API Error ({response.status_code}): {error_msg}")

        except requests.exceptions.ConnectionError:
            raise Exception("Connection error: Could not reach OpenRouter API.")
        except requests.exceptions.Timeout:
            raise Exception("Timeout: The request took too long.")


# ============================================================================
# Tool Agent (OpenRouter Version)
# ============================================================================

class ToolAgent:
    """
    An AI agent that can use external tools with OpenRouter.

    This agent can understand when to use tools, call them with appropriate
    parameters, and integrate the results into its responses.
    """

    def __init__(self, model="google/gemma-4-26b-a4b-it:free", system_prompt=None, temperature=0.7):
        """
        Initialize the tool agent.

        Args:
            model: OpenRouter model to use
            system_prompt: System prompt for the agent
            temperature: Temperature for response generation
        """
        # Initialize OpenRouter client
        self.llm = OpenRouterClient(model=model, temperature=temperature)

        self.system_prompt = system_prompt or """You are a helpful AI assistant with access to tools.
Use the available tools when they can help answer the user's question more accurately.
Always explain what tools you're using and why.

When you need to use a tool, call it with the appropriate parameters.
After getting the result, explain it to the user in a clear and friendly way.

Important: You have access to these tools:
- calculator: For mathematical operations
- get_current_time: To get the current time
- get_weather: To check weather in a city
- search_web: To search for information online

If you don't need to use a tool, just respond naturally to the user's question."""

        self.conversation_history = []
        self.tool_registry = ToolRegistry()
        self._setup_default_tools()

    def _setup_default_tools(self):
        """Register default tools."""
        tool_functions = {
            "calculator": calculator,
            "get_current_time": get_current_time,
            "get_real_weather": get_real_weather,        # ← NEW: Real weather
            "get_weather_forecast": get_weather_forecast, # ← NEW: Forecast
            "search_web": search_web
        }

        for schema in TOOL_SCHEMAS:
            func_name = schema["function"]["name"]
            if func_name in tool_functions:
                self.tool_registry.register(
                    func_name,
                    tool_functions[func_name],
                    schema
                )

    def generate_response(self, user_message, max_tool_calls=5):
        """
        Generate a response with tool support.

        Args:
            user_message: User's input message
            max_tool_calls: Maximum number of tool iterations

        Returns:
            Agent's response string
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        tool_calls_made = 0

        while tool_calls_made < max_tool_calls:
            # Call LLM with tools
            response_data = self.llm.chat_completion(
                messages=messages,
                tools=self.tool_registry.get_schemas(),
                tool_choice="auto"
            )

            # ✅ FIXED: Extract message from response
            response_message = response_data['choices'][0]['message']
            content = response_message.get('content', '')
            tool_calls = response_message.get('tool_calls', [])

            # ✅ FIXED: Check if LLM wants to use tools
            if not tool_calls:
                # No tool calls - return final response
                final_response = content or "I don't have a specific answer right now."
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response
                })
                return final_response

            # LLM wants to use tools
            print(f"\n[🔧 Tool calls requested: {len(tool_calls)}]")

            # Add assistant message with tool calls to messages
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls
            })

            # ✅ FIXED: Execute each tool call
            for tool_call in tool_calls:
                function = tool_call.get('function', {})
                tool_name = function.get('name', '')
                tool_args = json.loads(function.get('arguments', '{}'))

                print(f"  • Calling {tool_name} with {tool_args}")

                # Execute the tool
                try:
                    result = self.tool_registry.execute(tool_name, **tool_args)
                    result_str = json.dumps(result, indent=2)
                    print(f"    ✅ Result: {result_str[:100]}...")
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
                    print(f"    ❌ Error: {e}")

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get('id', ''),
                    "content": result_str
                })

            tool_calls_made += 1

        # Get final response after all tool calls
        final_response_data = self.llm.chat_completion(messages=messages)
        final_content = final_response_data['choices'][0]['message'].get('content', 
            "I've gathered the information but need to process it.")

        self.conversation_history.append({
            "role": "assistant",
            "content": final_content
        })

        return final_content

    def run(self):
        """Run interactive conversation loop."""
        print("\n" + "="*60)
        print("🤖 Tool Agent (OpenRouter) - Interactive Mode")
        print("="*60)
        print(f"📚 Available tools: {', '.join(self.tool_registry.get_tool_names())}")
        print(f"🧠 Model: {self.llm.model}")
        print("\nCommands:")
        print("  - 'quit': Exit")
        print("  - 'tools': List available tools")
        print("  - 'clear': Clear conversation history")
        print("="*60 + "\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n🤖 Agent: Goodbye! Have a great day! 👋\n")
                break

            if user_input.lower() == 'tools':
                print(f"\n📚 Available tools: {', '.join(self.tool_registry.get_tool_names())}\n")
                continue

            if user_input.lower() == 'clear':
                self.conversation_history = []
                print("🧹 Conversation history cleared!\n")
                continue

            if not user_input:
                continue

            try:
                print("\n🤖 Agent: ", end="", flush=True)
                response = self.generate_response(user_input)
                print(f"{response}\n")
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


# ============================================================================
# Demonstrations
# ============================================================================

def demo_calculator():
    """Demonstrate calculator tool usage."""
    print("\n" + "="*60)
    print("📊 Demo: Calculator Tool")
    print("="*60 + "\n")

    agent = ToolAgent()

    questions = [
        "What is 1234 multiplied by 5678?",
        "Calculate 100 divided by 7",
        "What's 2500 minus 873?"
    ]

    for question in questions:
        print(f"👤 You: {question}")
        response = agent.generate_response(question)
        print(f"🤖 Agent: {response}\n")
        print("-"*50)


def demo_multiple_tools():
    """Demonstrate using multiple tools in one query."""
    print("\n" + "="*60)
    print("🔧 Demo: Multiple Tools")
    print("="*60 + "\n")

    agent = ToolAgent()

    question = "What's the weather in Tokyo and what time is it there?"
    print(f"👤 You: {question}")
    response = agent.generate_response(question)
    print(f"🤖 Agent: {response}\n")


def demo_search_and_calculate():
    """Demonstrate search and calculator combined."""
    print("\n" + "="*60)
    print("🔍 Demo: Search + Calculate")
    print("="*60 + "\n")

    agent = ToolAgent()

    question = "Search for the population of Japan and calculate what 10% of that would be"
    print(f"👤 You: {question}")
    response = agent.generate_response(question)
    print(f"🤖 Agent: {response}\n")

# ============================================================================
# Demo Function to Test Real Weather
# ============================================================================

def demo_real_weather():
    """Demonstrate real weather tool usage."""
    print("\n" + "="*60)
    print("🌤️ Demo: Real Weather Tool")
    print("="*60 + "\n")
    
    # Test current weather
    print("Testing current weather:")
    print("-" * 40)
    
    weather = get_real_weather("New York")
    if "error" in weather:
        print(f"❌ {weather['error']}")
    else:
        print(f"🌆 {weather['location']['name']}, {weather['location']['country']}")
        print(f"🌡️ Temperature: {weather['temperature']}°{'C' if weather['unit'] == 'celsius' else 'F'}")
        print(f"☁️ Condition: {weather['condition']}")
        print(f"💧 Humidity: {weather['humidity']}%")
        print(f"💨 Wind: {weather['wind_speed']} km/h")
        print(f"🤔 Feels like: {weather['feels_like']}°{'C' if weather['unit'] == 'celsius' else 'F'}")
        print(f"🕐 Last updated: {weather['last_updated']}")
    
    print("\n" + "-" * 40)
    
    # Test forecast
    print("Testing forecast:")
    print("-" * 40)
    
    forecast = get_weather_forecast("London", days=3)
    if "error" in forecast:
        print(f"❌ {forecast['error']}")
    else:
        print(f"📅 Forecast for {forecast['location']}")
        for day in forecast['forecast']:
            print(f"\n📆 {day['date']}")
            print(f"   High: {day['max_temperature']}°{'C' if forecast['unit'] == 'celsius' else 'F'}")
            print(f"   Low: {day['min_temperature']}°{'C' if forecast['unit'] == 'celsius' else 'F'}")
            print(f"   Condition: {day['condition']}")
            print(f"   ☔ Chance of rain: {day['chance_of_rain']}%")



# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🤖 TOOL AGENT (OpenRouter Version)")
    print("="*70)
    print("\nChoose a mode:")
    print("  1. Interactive Mode (Chat with the agent)")
    print("  2. Demo: Calculator Tool")
    print("  3. Demo: Multiple Tools")
    print("  4. Demo: Search + Calculate")
    print("  5. Demo: Wether")
    print("  q. Quit")

    choice = input("\nYour choice: ").strip()

    if choice == "1":
        agent = ToolAgent()
        agent.run()
    elif choice == "2":
        demo_calculator()
    elif choice == "3":
        demo_multiple_tools()
    elif choice == "4":
        demo_search_and_calculate()
    elif choice == "5":
        demo_real_weather()
    elif choice.lower() == 'q':
        print("\nGoodbye! 👋\n")
    else:
        print("Invalid choice. Running interactive mode...")
        agent = ToolAgent()
        agent.run()