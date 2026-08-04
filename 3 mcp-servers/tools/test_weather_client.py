#!/usr/bin/env python3
"""
Test client for weather MCP server
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test():
    server_path = "weather_mcp_server.py"
    
    server_params = StdioServerParameters(
        command="python3",
        args=[server_path]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print("📋 Available Tools:")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description}")
            print()
            
            # Test 1: Get weather
            print("🌤️ Testing 'get_current_weather'...")
            result = await session.call_tool("get_current_weather", arguments={"city": "New York"})
            print(result.content[0].text)
            print()
            
            # Test 2: Get forecast
            print("📅 Testing 'get_forecast'...")
            result = await session.call_tool("get_forecast", arguments={"city": "London", "days": 3})
            print(result.content[0].text)
            print()
            
            # Test 3: Compare weather
            print("📊 Testing 'compare_weather'...")
            result = await session.call_tool("compare_weather", arguments={"city1": "Tokyo", "city2": "Paris"})
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(test())