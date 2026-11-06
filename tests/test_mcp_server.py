import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "run_check", "preview_decisions", "get_ad_performance",
    "get_decision_log", "get_settings",
}

async def list_tool_names():
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "meta_ads_autopause.mcp_server"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return {tool.name for tool in result.tools}
        
def test_server_starts_and_lists_tools():
    assert asyncio.run(list_tool_names()) == EXPECTED_TOOLS