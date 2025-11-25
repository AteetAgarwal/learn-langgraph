from fastmcp import FastMCP as FastMCPServer

server = FastMCPServer("arithmetic-mcp-server")


@server.tool()
async def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


@server.tool()
async def subtract(a: float, b: float) -> float:
    """Return the difference between two numbers."""
    return a - b


@server.tool()
async def multiply(a: float, b: float) -> float:
    """Return the product of two numbers."""
    return a * b


@server.tool()
async def divide(a: float, b: float) -> float:
    """Return the quotient of two numbers."""
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b


if __name__ == "__main__":
    server.run()