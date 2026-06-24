from mcps.mcp_client import MCPClient


class MCPRegistry:
    def __init__(self):
        self._clients: dict[str, MCPClient] = {}
        self._tools: dict[str, tuple[str, any]] = {}
        # tool_name -> (server_name, tool_def), and thats what it looks like

    async def register(self, name: str, config: dict):
        client = MCPClient(config)
        await client.connect()
        self._clients[name] = client
        for tool in await client.list_tools():
            self._tools[tool.name] = (name, tool)

    async def call(self, tool_name: str, arguments: dict):
        server_name, _ = self._tools[tool_name]
        return await self._clients[server_name].call_tool(tool_name, arguments)

    def get_tool_schemas(self) -> list[dict]:
        return [
            {
                "name": name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for name, (_, tool) in self._tools.items()
        ]


mcp_registry = MCPRegistry()
