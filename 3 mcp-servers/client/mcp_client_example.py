#!/usr/bin/env python3
"""
Simple MCP Client - Easy to debug
"""

import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_server():
    """Test the MCP server."""
    
    # Get server path
    script_dir = Path(__file__).parent
    server_path = script_dir / "simple_mcp_server.py"
    
    # If not found, try the basic folder
    if not server_path.exists():
        server_path = Path("/home/mercy/Desktop/AI-Agents-from-scratch/3 mcp-servers/basic/simple_mcp_server.py")
    
    print(f"📂 Server: {server_path}")
    
    if not server_path.exists():
        print(f"❌ Server not found!")
        return
    
    print("🔌 Connecting...")
    
    try:
        # Set up server parameters
        server_params = StdioServerParameters(
            command="python3",
            args=[str(server_path)]
        )
        
        # Connect
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                print("🔄 Initializing...")
                await session.initialize()
                print("✅ Connected!")
                
                # List tools
                print("\n📋 Listing tools...")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description}")
                
                # Test add
                print("\n🧪 Testing 'add'...")
                result = await session.call_tool("add", arguments={"a": 15, "b": 27})
                print(f"  15 + 27 = {result.content[0].text}")
                
                # Test multiply
                print("\n🧪 Testing 'multiply'...")
                result = await session.call_tool("multiply", arguments={"a": 6, "b": 7})
                print(f"  6 * 7 = {result.content[0].text}")
                
                # Test power
                print("\n🧪 Testing 'power'...")
                result = await session.call_tool("power", arguments={"base": 2, "exponent": 10})
                print(f"  2^10 = {result.content[0].text}")
                
                print("\n✅ All tests passed!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_server())