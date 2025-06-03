import asyncio
import logging
import os
from mysql.connector import connect, Error
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from pydantic import AnyUrl
from dotenv import load_dotenv

from duckduckgo_search import DDGS





# 日志相关配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mysql_mcp_server")



# 实例化Server
app = Server("duckduckgo_mcp_server")


# 声明 list_tools 函数为一个列出工具的接口
# 列出可用的 MySQL 工具
@app.list_tools()
async def list_tools() -> list[Tool]:
    logger.info("Listing tools...")
    # 函数返回一个列表，其中包含一个 Tool 对象
    # 每个 Tool 对象代表一个工具，其属性定义了工具的功能和输入要求
    return [
        Tool(
            # 工具的名称
            name="duckduckgo_web_search",
            # 工具的描述
            description="执行搜索查询",
            # 定义了工具的输入模式（Schema），用于描述输入数据的格式和要求
            inputSchema={
                # 定义输入为一个 JSON 对象
                "type": "object",
                # 定义输入对象的属性
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (max 400 chars, 50 words)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Number of results,default 10",
                        "default": 10
                    },
                },
                # 列出输入对象的必需属性
                "required": ["query"]
            }
        )
    ]


# 声明 call_tool 函数为一个工具调用的接口
# 根据传入的工具名称和参数执行相应的命令
# name: 工具的名称（字符串），指定要调用的工具
# arguments: 一个字典，包含工具所需的参数
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    # 检查工具名称 name 是否是 "duckduckgo_web_search"
    # 如果 query 为空或未提供，抛出 ValueError 异常，提示用户必须提供查询语句
    if name != "duckduckgo_web_search":
        raise ValueError(f"Unknown tool: {name}")
    
    query = arguments.get("query")
    max_results = arguments.get("max_results")
    if not query:
        raise ValueError("Query is required")

    try:
        results = DDGS().text(
            keywords=query,
            region="cn-zh",
            safesearch='off',
            timelimit='7d',
            max_results=max_results
        )
        # 拼接字符串
        results = "\n".join(f"{item['title']} - {item['href']} - {item['body']}" for item in results)
        # 返回一个包含查询结果的 TextContent 对象
        return [TextContent(type="text", text=results)]

    # 捕获操作期间发生的任何异常
    except Error as e:
        logger.error(f"Error executing search '{query}': {e}")
        return [TextContent(type="text", text=f"Error executing query: {str(e)}")]


# 启动 MCP服务器
async def main():
    logger.info("Starting DuckDuckGo Search MCP server...")

    # 启动 stdio_server，通过标准输入/输出（stdin/stdout）与客户端通信
    # async with 是异步上下文管理器，确保 stdio_server 资源在使用完成后自动清理
    # 返回的 (read_stream, write_stream) 是两个流对象
    # read_stream: 用于从客户端读取输入的流对象
    # write_stream: 用于向客户端发送输出的流对象
    async with stdio_server() as (read_stream, write_stream):
        try:
            # 异步运行 MCP 应用程序
            await app.run(
                read_stream,
                write_stream,
                # 用于初始化应用程序的选项，通常包含配置或上下文信息
                app.create_initialization_options()
            )
        # 捕获运行 app.run() 时发生的所有异常
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)
            raise




if __name__ == "__main__":
    asyncio.run(main())