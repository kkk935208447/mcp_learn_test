# 此脚本模拟了一个 mcp 客户端，通过标准输入/输出与服务器交互
# 执行的主要任务：
# 启动服务器
# 初始化客户端与服务器的连接
# 列出服务器支持的 prompts
# 获取一个具体的 prompt


# ClientSession 表示客户端会话，用于与服务器交互
# StdioServerParameters 定义与服务器的 stdio 连接参数
from mcp import ClientSession, StdioServerParameters
# 提供与服务器的 stdio 连接上下文管理器
from mcp.client.stdio import stdio_client
import asyncio




# 为 stdio 连接创建服务器参数
server_params = StdioServerParameters(
    # 服务器执行的命令，这里是 python
    command="python",
    # 启动命令的附加参数，这里是运行 example_server.py
    args=["server.py"],
    # 环境变量，默认为 None，表示使用当前环境变量
    # env=None
)


async def run():
    # 创建与服务器的标准输入/输出连接，并返回 read 和 write 流
    async with stdio_client(server_params) as (read, write):
        # 创建一个客户端会话对象，通过 read 和 write 流与服务器交互
        async with ClientSession(read, write) as session:
            # 向服务器发送初始化请求，确保连接准备就绪
            # 建立初始状态，并让服务器返回其功能和版本信息
            capabilities = await session.initialize()
            print("capabilities:", capabilities)
            print("Supported capabilities:", capabilities.capabilities)

            # 请求服务器列出所有支持的 prompt
            # 返回包含 prompt 元信息的列表，例如名称、描述及参数
            prompts = await session.list_prompts()
            print("prompts:",prompts)

            # 请求服务器获取一个特定的 prompt 实例
            # 返回prompt 对象，包含消息和相关信息
            prompt = await session.get_prompt("example-prompt", arguments={"arg1": "value"})
            print("prompt:", prompt)


if __name__ == "__main__":
    # 使用 asyncio 启动异步的 run() 函数
    asyncio.run(run())