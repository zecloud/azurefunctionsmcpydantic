"""
Azure Functions MCP Pydantic Tool
Convert Pydantic models to Azure Functions MCP toolProperties format
"""

from .pydanticutil import pydantic_to_tool_properties

__version__ = "0.1.0"
__all__ = ["pydantic_to_tool_properties"]