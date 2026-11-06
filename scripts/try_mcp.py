import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "meta_ads_autopause.mcp_server"],
        env=dict(os.environ),
        cwd=os.getcwd(),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool in ["get_settings", "preview_decisions"]:
                result = await session.call_tool(tool, {})
                print(f"--- {tool} ---")
                for block in result.content:
                    print(block.text)


asyncio.run(main())