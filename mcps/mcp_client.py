from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client


class MCPClient:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.session: ClientSession | None = None

    async def connect(self):
        if self.config["transport"] == "stdio":
            stdio_server_params = StdioServerParameters(
                command=self.config["command"],
                args=self.config.get("args", []),
                env=self.config.get("env"),
            )

            self.mcp_client = stdio_client(stdio_server_params)

        else:
            self.mcp_client = sse_client(self.config["url"])

        read, write = await self.mcp_client.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()

    async def list_tools(self) -> list:
        if self.session is None:
            raise RuntimeError("Session not initialized. Call connect() first.")
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, name: str, arguments: dict) -> any:
        if self.session is None:
            raise RuntimeError("Session not initialized. Call connect() first.")

        return await self.session.call_tool(name, arguments)

    async def disconnect(self):
        if self.session is None:
            raise RuntimeError("Session not initialized. Call connect() first.")

        await self.session.__aexit__(None, None, None)
        await self.mcp_client.__aexit__(None, None, None)
