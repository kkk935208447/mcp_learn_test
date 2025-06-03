# 此脚本实现了一个支持 MCP 协议的服务器：
# 提供了一个名为 example-prompt 的 prompt
# 支持客户端通过标准输入/输出与服务器通信
# 能够响应客户端的 list_prompts 和 get_prompt 请求，返回相应的内容


# Server 提供服务器实例化功能
# NotificationOptions 用于配置通知选项
from mcp.server import Server, NotificationOptions
# 服务器初始化时的选项
from mcp.server.models import InitializationOptions
# 提供标准输入/输出支持，用于与外部工具交互
import mcp.server.stdio
# 定义与 mcp 协议相关的类型
import mcp.types as types
import asyncio




# 创建一个名为 example-server 的服务器实例
server = Server("example-server")

# 注册一个回调函数，返回服务器支持的 prompt 列表
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    # 返回一个包含 Prompt 对象的列表
    return [
        # 定义了一个prompt，包含以下信息
        types.Prompt(
            name="example-prompt",
            description="An example prompt template",
            arguments=[
                types.PromptArgument(
                    name="arg1",
                    description="Example argument",
                    required=True
                )
            ]
        )
    ]


# 注册一个回调函数，用于根据 prompt 名称和参数生成具体的 prompt 内容
@server.get_prompt()
async def handle_get_prompt(
    name: str,
    arguments: dict[str, str] | None
) -> types.GetPromptResult:
    if name != "example-prompt":
        raise ValueError(f"Unknown prompt: {name}")

    # 返回一个GetPromptResult 对象，包含 prompt 的详细信息
    return types.GetPromptResult(
        description="Example prompt",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text="Example prompt text"
                )
            )
        ]
    )


async def run():
    # 使用 stdio_server 启动标准输入/输出的服务器模式
    # 提供 read_stream 和 write_stream 用于数据传输
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # 启动服务器，使用初始化选项 InitializationOptions
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="example",
                server_version="0.1.0",
                # 配置服务器功能，包括通知选项和实验性功能
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )



if __name__ == "__main__":
    # 使用 asyncio 运行异步的 run() 函数，启动服务器
    asyncio.run(run())