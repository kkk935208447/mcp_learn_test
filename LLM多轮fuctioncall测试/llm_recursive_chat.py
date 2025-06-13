import os
import json
from openai import OpenAI
from openai.resources.chat.completions.completions import NOT_GIVEN
from openai.types.chat.chat_completion import ChatCompletion
from dotenv import load_dotenv
from loguru import logger
from typing import Any, List, Dict, Optional
from pprint import pprint


import os 
# 删除环境变量中的代理设置
proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
logger.warning(f"删除环境变量中的代理设置：{proxy_vars}")
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]


# 加载环境变量
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL")
if (not API_KEY) or (not BASE_URL):
    raise RuntimeError("OPENAI_API_KEY or OPENAI_BASE_URL environment variable not set")


# 工具函数定义，可以按需扩展
def add(a: float, b: float) -> float:
    """计算两个实数的和"""
    return a + b

def get_weather(location: str) -> str:
    """获取某地区的天气"""
    return f"{location}：晴，温度25℃"




class RecursiveLLMClient:
    """支持递归多轮function call的 OpenAI 客户端，function call 具体的【多轮】调用步骤见：https://platform.openai.com/docs/guides/function-calling?api-mode=chat"""

    def __init__(self):
        self.openai_client = OpenAI(
            base_url=BASE_URL,
            api_key=API_KEY
        )
        self.model = MODEL
        logger.info(f"{self.__class__.__name__} initialized, params: {self.__dict__}")

    @property
    def get_client(self):
        return self.openai_client

    @property
    def get_model(self):
        return self.model

    def get_chat_completions_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = NOT_GIVEN) -> ChatCompletion:
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else NOT_GIVEN
        )
        return response

    def call_local_tool(self, function_name: str, function_args: dict):
        """执行本地函数"""
        # globals() 是一个内置函数，它返回一个字典，表示当前全局符号表。这个字典包含了当前模块中定义的所有名称和它们所对应的对象。
        if function_name not in globals():
            logger.error(f"Function {function_name} is not implemented in globals.")
            raise RuntimeError(f"Function {function_name} is not implemented in globals.")
        return globals()[function_name](**function_args)

    def recursive_chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = NOT_GIVEN):
        """
        支持递归处理多轮function call，直到LLM回复content（没有tool_call为止）。
        每当检测到tool_call，则自动本地执行并将结果追加回到messages，再次调用LLM。
        返回最终assistant文本及消息列表。
        """

        iter_n = 0
        while True:
            response = self.get_chat_completions_response(messages=messages, tools=tools)
            choice = response.choices[0]
            finish_reason = choice.finish_reason

            iter_n += 1  # 增加迭代轮数
            if iter_n > 5:
                logger.error(f"迭代次数超过5次，疑似出现死循环，终止递归。")
                return None, messages

            if finish_reason == "tool_calls":
                tool_calls = choice.message.tool_calls or []
                logger.info(f"递归次数{iter_n}，检测到tool_calls, 共{len(tool_calls)}个，将递归执行：{[i.function.name for i in tool_calls]}")

                # 将（本次）LLM的tool_call(messsage)也追加，function call 具体的【多轮】调用步骤见：https://platform.openai.com/docs/guides/function-calling?api-mode=chat
                _message = choice.message.model_dump()
                # _message["content"] = None   # content 内容重置为None，有些类似qwen3的推理模型content不为空，重置为None
                messages.append(_message)

                # 按顺序执行全部tool_calls并记录内容
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except Exception as e:
                        logger.error(f"解析function arguments失败: {tool_call.function.arguments}, err: {e}")
                        function_args = {}
                    logger.info(f"调用本地函数: {function_name}, 参数: {function_args}")
                    function_response = self.call_local_tool(function_name, function_args)
                    logger.info(f"函数结果: {function_response}")

                    # tool role 的标准格式
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(function_response)
                    })

                # 继续下一轮带结果递归
                continue

            else:
                assistant_text = choice.message.content
                # 将最终回复加入历史
                messages.append({"role": "assistant", "content": assistant_text})
                # logger.info(f"递归结束，生成assistant回复: {assistant_text}")
                return assistant_text, messages
            

    
    def recursive_chatV2(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = NOT_GIVEN):
        """
        相对于上面的函数，这个版本会使用 role 为 `fuction` 的 message 来记录函数调用的结果，而不是使用 `tool` 的 message 来记录。
        # NOTE：实际测试下来，role 为 tool 比 role 为 function 更稳定，但是 role 为 function 更简洁。
        """

        iter_n = 0
        while True:
            # 打印当前的messages
            logger.info(f"当前轮的messages: \n{messages}")

            response = self.get_chat_completions_response(messages=messages, tools=tools)
            choice = response.choices[0]
            finish_reason = choice.finish_reason

            iter_n += 1  # 增加迭代轮数
            if iter_n > 5:
                logger.error(f"迭代次数超过5次，疑似出现死循环，终止递归。")
                return None, messages

            if finish_reason == "tool_calls":
                tool_calls = choice.message.tool_calls or []
                logger.info(f"递归次数{iter_n}，检测到tool_calls, 共{len(tool_calls)}个，将递归执行：{[i.function.name for i in tool_calls]}")

                # 按顺序执行全部tool_calls并记录内容
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except Exception as e:
                        logger.error(f"解析function arguments失败: {tool_call.function.arguments}, err: {e}")
                        function_args = {}
                    logger.info(f"调用本地函数: {function_name}, 参数: {function_args}")
                    function_response = self.call_local_tool(function_name, function_args)
                    logger.info(f"函数结果: {function_response}")

                    # role 使用function的格式
                    messages.append({
                        "role": "function",
                        "name": f"{function_name}",
                        "content": f"{str(function_response)}"
                    })

                # 继续下一轮带结果递归
                continue

            else:
                assistant_text = choice.message.content
                # 将最终回复加入历史
                messages.append({"role": "assistant", "content": assistant_text})
                # logger.info(f"递归结束，生成assistant回复: {assistant_text}")
                return assistant_text, messages




if __name__ == "__main__":
    # 示例函数工具定义（可自行扩充）
    tools = [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "计算两个实数的和",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "第一个实数"},
                        "b": {"type": "number", "description": "第二个实数"}
                    },
                    "required": ["a", "b"],
                    "additionalProperties": False
                },
                "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取某地区的天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "待查询的地区"}
                    },
                    "required": ["location"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]



    # 演示loop，与LLM对话
    client = RecursiveLLMClient()
    print(f"使用模型: {client.get_model}\n")
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个AI助手，你可以使用工具来获取信息。然后你可以根据这些信息来回答用户的问题。"
            )
        }
    ]



    print("开始多轮递归对话（输入exit退出）")
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        messages.append({"role": "user", "content": user_input})
        logger.info(f"当前轮的messages: \n")
        pprint(messages)

        # 对话
        assistant_text, messages = client.recursive_chat(messages=messages, tools=tools)
        # assistant_text, messages = client.recursive_chatV2(messages=messages, tools=tools)

        logger.success(f"Assistant:\n{assistant_text}")
