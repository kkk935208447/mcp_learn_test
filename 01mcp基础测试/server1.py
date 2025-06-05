# 一个简单的 stdio 标准输入/输出的 mcp 服务器

from mcp.server import Server, NotificationOptions  # 提供服务器实例化功能和通知选项
from mcp.server.models import InitializationOptions  # 提供服务器初始化时的选项
import mcp.server.stdio  # 提供标准输入/输出支持，用于与外部工具交互
import mcp.types as types
import asyncio
from typing import Any


app = Server(name="我第一个mcp服务器", version="1.0.0")  # 创建一个名为 “我第一个mcp服务器” 的服务器实例


# 注册一个回调函数，返回服务器支持的 prompt 列表
@app.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    print()
    # 返回一个包含 Prompt 对象的列表
    return [
        types.Prompt(
            name="trans text prompt",
            description="用于翻译文本的 prompt 模板",
            arguments=[
                types.PromptArgument(
                    name="source_language",
                    description="翻译文本源语言",
                    required=True
                ),
                types.PromptArgument(
                    name="target_language",
                    description="翻译文本目标语言",
                    required=True
                )
            ]
        ),
        types.Prompt(
            name="python code prompt",
            description="用于生成 Python 代码的 prompt 模板",
            arguments=[
                types.PromptArgument(
                    name="arg1",
                    description="仅用于测试用的参数",
                    required=True
                )
            ]
        )
    ]


# 注册一个回调函数，用于根据 prompt 名称和参数生成具体的 prompt 内容
@app.get_prompt()
async def handle_get_prompt(
    name: str,
    arguments: dict[str, str]
) -> types.GetPromptResult:
    
    if name == "trans text prompt":
        source_language = arguments.get("source_language")
        target_language = arguments.get("target_language")

        prompt = f"你是一个专业的翻译者，你会根据用户提供的{source_language}语言和{target_language}语言，将用户提供的文本翻译成{target_language}语言: "

        return types.GetPromptResult(
            description="翻译文本的具体 prompt",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=prompt
                    )
                )
            ]
        )
    elif name == "python code prompt":
        arg1 = arguments.get("arg1")
        prompt = f"你是一个专业的 Python 代码生成者，你会根据用户提供的参数{arg1}，生成一段 Python 代码: "
        return types.GetPromptResult(
            description="生成 Python 代码的具体 prompt",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=prompt
                    )
                )
            ]
        )
    else:
        raise ValueError(f"Unknown prompt: {name}")
    

# 注册一个回调函数，用于列出已有的工具
@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    print()
    # 返回一个包含 Tool 对象的列表
    return [
        types.Tool(
            name="add",
            description="用于加法运算的工具",
            inputSchema={
                "type": "object",
                "properties": {
                    # "type": "number" openai 支持的数字类型
                    "a": {"type": "number", "description": "第一个加数，值域为实数"},
                    "b": {"type": "number", "description": "第二个加数，值域为实数"}
                },
                "required": ["a", "b"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="subtract",
            description="用于减法运算的工具",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "被减数，值域为实数"},
                    "b": {"type": "number", "description": "减数，值域为实数"}
                },
                "required": ["a", "b"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_weather",
            description="用于获取天气的工具",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "待查询的地区"}
                },
                "required": ["location"],
                "additionalProperties": False
            }
        )
    ]



def add(a, b):
    return float(a) + float(b)

def subtract(a, b):
    return float(a) - float(b)

def get_weather(location):
    return f"{location}：晴，温度25℃"


# 注册一个回调函数，用于根据工具名称和参数执行具体的工具操作
@app.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any] 
) -> list[types.TextContent]:
    
    if name not in ["add", "subtract", "get_weather"]:
        raise ValueError(f"Unknown tool: {name}")
    
    # 调用工具函数并将结果作为文本内容返回, globals() 是一个内置函数，它返回一个字典，表示当前全局符号表。
    fuction_res = globals()[name](**arguments)
    return [
        types.TextContent(
            type="text",
            text=f"tool `{name}` result: {fuction_res}"
        )
    ]




async def run():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            initialization_options=app.create_initialization_options()
        )


if __name__ == "__main__":
    print("Starting basic server...")
    asyncio.run(run())
