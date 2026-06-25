"""
The place to put any code that needs to be run first
"""

from utils.logger import logger
import json


def setup_mcps():
    from mcps.mcp_registry import mcp_registry
    from mcps.mcp_loop import run_async

    with open("mcps/mcp_servers.json") as f:
        mcp_config = json.load(f)

    for server in mcp_config["servers"]:
        logger.info(f"Registering MCP server: {server['name']}")
        run_async(mcp_registry.register(server["name"], server))
        logger.info(f"Registered MCP server: {server['name']}")

    logger.debug(f"MCP Registered: {mcp_registry.get_tool_schemas()}")
