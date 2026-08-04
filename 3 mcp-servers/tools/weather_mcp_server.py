"""
Tutorial 03-B: MCP Server with Advanced Tools
Works with ALL MCP SDK versions
"""

import asyncio
import json
import os
import random
from datetime import datetime
import sys
from typing import Any

import mcp

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ImportError:
    print("❌ MCP SDK not found. Install: pip install mcp", file=sys.stderr)
    sys.exit(1)


class WeatherMCPServer:
    """MCP server that provides weather-related tools."""

    def __init__(self):
        self.server = Server("weather-tools-server")
        
        # Simulated weather database
        self.weather_db = {
            "new york": {"temp": 72, "condition": "Sunny", "humidity": 60},
            "london": {"temp": 65, "condition": "Cloudy", "humidity": 75},
            "tokyo": {"temp": 80, "condition": "Clear", "humidity": 55},
            "paris": {"temp": 68, "condition": "Partly Cloudy", "humidity": 65},
            "sydney": {"temp": 75, "condition": "Sunny", "humidity": 70},
            "mumbai": {"temp": 85, "condition": "Humid", "humidity": 80},
            "dubai": {"temp": 95, "condition": "Hot", "humidity": 45},
            "singapore": {"temp": 82, "condition": "Thunderstorms", "humidity": 85}
        }
        
        self.setup_handlers()

    def setup_handlers(self):
        """Register tool handlers - using request_handlers dict."""
        
        # ✅ CORRECT: Use request_handlers dictionary
        self.server.request_handlers["tools/list"] = self._handle_list_tools
        self.server.request_handlers["tools/call"] = self._handle_call_tools

    async def _handle_list_tools(self, request):
        """Handle tools/list request."""
        return {
            "tools": [
                {
                    "name": "get_current_weather",
                    "description": "Get the current weather for a city",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city name (e.g., 'New York', 'London')"
                            },
                            "units": {
                                "type": "string",
                                "enum": ["fahrenheit", "celsius"],
                                "description": "Temperature units",
                                "default": "fahrenheit"
                            }
                        },
                        "required": ["city"]
                    }
                },
                {
                    "name": "get_forecast",
                    "description": "Get a weather forecast for a city",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city name"
                            },
                            "days": {
                                "type": "number",
                                "description": "Number of days (1-7)",
                                "default": 3
                            }
                        },
                        "required": ["city"]
                    }
                },
                {
                    "name": "compare_weather",
                    "description": "Compare weather between two cities",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city1": {"type": "string", "description": "First city"},
                            "city2": {"type": "string", "description": "Second city"}
                        },
                        "required": ["city1", "city2"]
                    }
                },
                {
                    "name": "save_weather_alert",
                    "description": "Save a weather alert to a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City name"},
                            "alert_type": {
                                "type": "string",
                                "enum": ["rain", "storm", "heat", "cold", "thunderstorm"],
                                "description": "Type of weather alert"
                            },
                            "message": {"type": "string", "description": "Alert message"}
                        },
                        "required": ["city", "alert_type", "message"]
                    }
                }
            ]
        }

    async def _handle_call_tools(self, request):
        """Handle tools/call request."""
        name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        result = await self._execute_tool(name, arguments)
        
        # Convert to dict format
        if isinstance(result, list) and len(result) > 0:
            content = []
            for item in result:
                if hasattr(item, 'text'):
                    content.append({"type": "text", "text": item.text})
                elif isinstance(item, dict):
                    content.append(item)
                else:
                    content.append({"type": "text", "text": str(item)})
            return {"content": content}
        else:
            return {"content": [{"type": "text", "text": str(result)}]}

    async def _execute_tool(self, name: str, arguments: dict):
        """Execute the requested tool."""
        if name == "get_current_weather":
            return await self._get_current_weather(arguments)
        elif name == "get_forecast":
            return await self._get_forecast(arguments)
        elif name == "compare_weather":
            return await self._compare_weather(arguments)
        elif name == "save_weather_alert":
            return await self._save_weather_alert(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _get_current_weather(self, args: dict):
        """Get current weather for a city."""
        city = args["city"].lower()
        units = args.get("units", "fahrenheit")

        if city not in self.weather_db:
            available = ', '.join([c.title() for c in self.weather_db.keys()])
            return [TextContent(
                type="text",
                text=f"❌ Weather data for '{city}' not available.\n\nAvailable cities: {available}"
            )]

        weather = self.weather_db[city]
        temp = weather["temp"]

        if units == "celsius":
            temp = round((temp - 32) * 5/9, 1)
            unit_symbol = "°C"
        else:
            unit_symbol = "°F"

        response = f"""
┌─────────────────────────────────────────┐
│          🌤️ WEATHER REPORT              │
├─────────────────────────────────────────┤
│  City:     {city.title():<20} │
│  Temp:     {temp}{unit_symbol:<14} │
│  Cond:     {weather['condition']:<20} │
│  Humidity: {weather['humidity']}%                 │
│  Time:     {datetime.now().strftime('%H:%M')}                 │
└─────────────────────────────────────────┘
        """
        return [TextContent(type="text", text=response)]

    async def _get_forecast(self, args: dict):
        """Generate a weather forecast."""
        city = args["city"].lower()
        days = min(int(args.get("days", 3)), 7)

        if city not in self.weather_db:
            return [TextContent(
                type="text",
                text=f"❌ Weather data for '{city}' not available."
            )]

        base_weather = self.weather_db[city]
        conditions = ["Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Clear", "Windy", "Humid"]

        response = f"📅 {days}-Day Forecast for {city.title()}\n"
        response += "─" * 40 + "\n"

        for i in range(days):
            temp_variation = random.randint(-8, 8)
            date = datetime.now().strftime("%Y-%m-%d")
            high = base_weather["temp"] + temp_variation + 5
            low = base_weather["temp"] + temp_variation - 5
            condition = random.choice(conditions)
            precip = random.randint(0, 60)

            response += f"\n📆 Day {i+1} ({date})\n"
            response += f"   High: {high}°F  Low: {low}°F\n"
            response += f"   Condition: {condition}\n"
            response += f"   Precipitation: {precip}%\n"

        return [TextContent(type="text", text=response)]

    async def _compare_weather(self, args: dict):
        """Compare weather between two cities."""
        city1 = args["city1"].lower()
        city2 = args["city2"].lower()

        if city1 not in self.weather_db or city2 not in self.weather_db:
            return [TextContent(
                type="text",
                text="❌ One or both cities not found in database."
            )]

        w1 = self.weather_db[city1]
        w2 = self.weather_db[city2]

        warmer = city1.title() if w1['temp'] > w2['temp'] else city2.title()
        diff = abs(w1['temp'] - w2['temp'])

        response = f"""
┌─────────────────────────────────────────────────────┐
│              📊 WEATHER COMPARISON                  │
├──────────────────┬──────────────────┬────────────────┤
│                  │ {city1.title():^16} │ {city2.title():^16} │
├──────────────────┼──────────────────┼────────────────┤
│ Temperature      │ {w1['temp']:^16}°F │ {w2['temp']:^16}°F │
│ Condition        │ {w1['condition']:^16} │ {w2['condition']:^16} │
│ Humidity         │ {w1['humidity']:^16}% │ {w2['humidity']:^16}% │
├──────────────────┴──────────────────┴────────────────┤
│ 🔥 Warmer city: {warmer}                              │
│ 📊 Temp difference: {diff}°F                         │
└─────────────────────────────────────────────────────┘
        """
        return [TextContent(type="text", text=response)]

    async def _save_weather_alert(self, args: dict):
        """Save a weather alert to file."""
        city = args["city"]
        alert_type = args["alert_type"]
        message = args["message"]

        os.makedirs("weather_alerts", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_alerts/{city}_{alert_type}_{timestamp}.json"

        alert_data = {
            "city": city,
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        with open(filename, 'w') as f:
            json.dump(alert_data, f, indent=2)

        return [TextContent(
            type="text",
            text=f"""
✅ Weather Alert Saved!

   City:        {city}
   Alert Type:  {alert_type}
   Message:     {message}
   File:        {filename}
   Time:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
        )]

    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            print("🚀 Weather MCP Server running!", file=sys.stderr)
            print("📚 Tools: get_current_weather, get_forecast, compare_weather, save_weather_alert", file=sys.stderr)
            
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    server = WeatherMCPServer()
    await server.run()


if __name__ == "__main__":
    print("="*60, file=sys.stderr)
    print("WEATHER MCP SERVER", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print("\n🌤️ Weather Tools:", file=sys.stderr)
    print("  • get_current_weather - Current weather", file=sys.stderr)
    print("  • get_forecast - Forecast", file=sys.stderr)
    print("  • compare_weather - Compare cities", file=sys.stderr)
    print("  • save_weather_alert - Save alerts", file=sys.stderr)
    print("\n" + "="*60, file=sys.stderr)
    asyncio.run(main())