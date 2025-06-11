"""
MCP 官方 Python SDK FastMCP 精简参数schema：去除 maximum/minimum/title 只保留 type/description/required
适用于 OpenAI function call 与自动工具描述无附加约束场景
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated

mcp = FastMCP(
    name="官方SDK进阶Server2",
    version="1.1.0"
)

# ======= PROMPT 注册（schema&描述齐全）=======

@mcp.prompt("trans text prompt", description="用于翻译文本的prompt模板，指明源语言和目标语言")
def translate_prompt(
    source_language: Annotated[str, Field(description="翻译文本的源语言，如'english'")],
    target_language: Annotated[str, Field(description="目标语言，如'chinese'")]
) -> str:
    """生成用于调用翻译LLM的prompt"""
    return f"你是一个专业翻译者。请将我输入的{source_language}内容翻译成{target_language}。"

@mcp.prompt("python code prompt", description="用于生成Python代码的prompt模板，参数可指定功能")
def python_code_prompt(
    arg1: Annotated[str, Field(description="指定要生成的Python代码的内容或说明")]
) -> str:
    """生成Python代码prompt"""
    return f"你是一名专业Python开发者，请根据描述'{arg1}'生成一段高质量Python代码。"

# ======= TOOL 注册（类型&schema友好）=======

@mcp.tool("add", description="加法运算工具，输入a,b返回和")
def add(
    a: Annotated[float, Field(description="第一个加数（实数）")],
    b: Annotated[float, Field(description="第二个加数（实数）")]
) -> str:
    """加法工具，返回计算结果（字符串）"""
    return f"tool `add` result: {a + b}"

@mcp.tool("subtract", description="减法运算工具，输入a,b返回差值（a-b）")
def subtract(
    a: Annotated[float, Field(description="被减数（实数）")],
    b: Annotated[float, Field(description="减数（实数）")]
) -> str:
    """减法工具，返回计算结果（字符串）"""
    return f"tool `subtract` result: {a - b}"

@mcp.tool("multiply", description="乘法运算工具，输入a,b返回乘积")
def multiply(
    a: Annotated[float, Field(description="第一个乘数（实数）")],
    b: Annotated[float, Field(description="第二个乘数（实数）")]
) -> str:
    """乘法工具，返回计算结果（字符串）"""
    return f"tool `multiply` result: {a * b}"

@mcp.tool("get_weather", description="根据地区返回天气（仅演示，固定输出）")
def get_weather(
    location: Annotated[str, Field(description="待查询地区，如'上海'")]
) -> str:
    """天气查询工具，字符串返回，适配函数调用格式"""
    return f"tool `get_weather` result: {location}：晴，温度25℃"



if __name__ == "__main__":
    mode = "stdio"
    print(f"当前运行模式：{mode}, mcp 服务器启动")
    mcp.run(transport=mode)
