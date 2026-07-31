#!/usr/bin/env python3
"""
Minimal MCP Server - Works with latest SDK
"""

import asyncio
import sys

# Try to import the right version
try:
    from mcp.server import MCPServer
    from mcp.types import TextContent
    
    # Create server (new style)
    mcp = MCPServer("calculator-server")
    
    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b
    
    @mcp.tool()
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
    
    @mcp.tool()
    def power(base: int, exponent: int) -> int:
        """Raise a number to a power."""
        return base ** exponent
    
    if __name__ == "__main__":
        print("🚀 Starting MCP server...", file=sys.stderr)
        mcp.run(transport="stdio")

except ImportError:
    # Fallback for older versions
    print("MCP SDK not found. Please install: pip install mcp", file=sys.stderr)
    sys.exit(1)