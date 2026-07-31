"""
Tutorial 03-A: Simple MCP Server from Scratch (FIXED)
Works with MCP SDK 1.0.0+
"""

import asyncio
import sys
from typing import Any, List
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult


class SimpleMCPServer:
    """A basic MCP server with calculator tools."""

    def __init__(self):
        self.server = Server("simple-calculator-server")
        self.setup_handlers()

    def setup_handlers(self):
        """Register tool handlers with the MCP server."""

        # 🔧 CORRECT: Using the request handler pattern
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return the list of available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="add",
                        description="Add two numbers together",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "a": {"type": "number", "description": "First number"},
                                "b": {"type": "number", "description": "Second number"}
                            },
                            "required": ["a", "b"]
                        }
                    ),
                    Tool(
                        name="multiply",
                        description="Multiply two numbers",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "a": {"type": "number", "description": "First number"},
                                "b": {"type": "number", "description": "Second number"}
                            },
                            "required": ["a", "b"]
                        }
                    ),
                    Tool(
                        name="power",
                        description="Raise a number to a power (a^b)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "base": {"type": "number", "description": "Base number"},
                                "exponent": {"type": "number", "description": "Exponent"}
                            },
                            "required": ["base", "exponent"]
                        }
                    )
                ]
            )

        # 🔧 CORRECT: Using the request handler pattern
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: dict[str, Any] | None
        ) -> List[TextContent]:
            """Execute the requested tool."""
            
            if arguments is None:
                arguments = {}

            if name == "add":
                a = arguments.get("a", 0)
                b = arguments.get("b", 0)
                result = a + b
                return [TextContent(type="text", text=f"The sum of {a} and {b} is {result}")]

            elif name == "multiply":
                a = arguments.get("a", 0)
                b = arguments.get("b", 0)
                result = a * b
                return [TextContent(type="text", text=f"The product of {a} and {b} is {result}")]

            elif name == "power":
                base = arguments.get("base", 0)
                exponent = arguments.get("exponent", 0)
                result = base ** exponent
                return [TextContent(type="text", text=f"{base} raised to the power of {exponent} is {result}")]

            else:
                raise ValueError(f"Unknown tool: {name}")

    async def run(self):
        """Run the MCP server using stdio transport."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            print("🚀 Simple MCP Server started!", file=sys.stderr)
            print("Available tools: add, multiply, power", file=sys.stderr)
            
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="simple-calculator-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
    """Run the server."""
    server = SimpleMCPServer()
    await server.run()


if __name__ == "__main__":
    print("="*60, file=sys.stderr)
    print("SIMPLE MCP SERVER - Calculator", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print("\nThis is an MCP server that exposes calculator tools.", file=sys.stderr)
    print("It communicates via stdio (standard input/output).", file=sys.stderr)
    print("\nTo use this server:", file=sys.stderr)
    print("1. Install: pip install mcp", file=sys.stderr)
    print("2. Configure it in your MCP client (like Claude Desktop)", file=sys.stderr)
    print("3. The AI will be able to use these calculator tools!", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    asyncio.run(main())