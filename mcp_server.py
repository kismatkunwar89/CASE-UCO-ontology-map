from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Tool Server")

@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverses the input text"""
    return text[::-1]

mcp.run()
