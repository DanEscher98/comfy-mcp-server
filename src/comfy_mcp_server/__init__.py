"""ComfyUI MCP Server - Enhanced version with workflow automation capabilities.

This server provides comprehensive ComfyUI integration for Claude Code:
- System monitoring and queue management
- Node and model discovery
- Workflow execution and creation
- Full workflow automation capabilities

Version: 0.2.0
"""

__version__ = "0.2.0"

import logging

from mcp.server.fastmcp import FastMCP

from .api import check_connection
from .settings import settings
from .tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Comfy MCP Server")

# Register all tools
register_all_tools(mcp)


def run_server():
    """Start the MCP server."""
    print(f"Starting Comfy MCP Server v{__version__}...")
    print(f"  ComfyUI URL: {settings.comfy_url}")
    print(f"  Workflows: {settings.workflows_dir or 'Not configured'}")
    print(f"  Output mode: {settings.output_mode}")
    print(f"  Poll timeout: {settings.poll_timeout}s")

    # Test connection
    connected, version = check_connection(timeout=5)
    if connected:
        print(f"  Connected to ComfyUI {version}")
    else:
        print("  Warning: Cannot connect to ComfyUI")

    mcp.run()


# Export key components for testing
__all__ = [
    "__version__",
    "mcp",
    "run_server",
    "settings",
]


if __name__ == "__main__":
    run_server()
