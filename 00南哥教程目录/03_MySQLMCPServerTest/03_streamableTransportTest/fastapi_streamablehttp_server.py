import uvicorn
import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from starlette.routing import Mount
from dotenv import load_dotenv
from mysqlMCPServer import mcp
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import contextlib
import logging
from typing import AsyncIterator

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_streamablehttp_server")

# 环境变量
load_dotenv()
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 创建流式HTTP会话管理器
session_manager = StreamableHTTPSessionManager(
    app=mcp,
    event_store=None,
    json_response=None,
    stateless=True,
)

# FastAPI应用
app = FastAPI(
    title="FastAPI MCP StreamableHTTP",
    description="基于FastAPI的MCP StreamableHTTP服务器",
    version="0.1.0",
)

# 定义一个原生ASGI handler
async def mcp_asgi_app(scope, receive, send):
    await session_manager.handle_request(scope, receive, send)

# 用Starlette的Mount挂载ASGI handler到 /mcp
app.router.routes.append(Mount("/mcp", app=mcp_asgi_app))

# 生命周期管理
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with session_manager.run():
        logger.info("FastAPI StreamableHTTP session manager started!")
        yield
        logger.info("FastAPI StreamableHTTP session manager stopped!")

app.router.lifespan_context = lifespan

# 启动函数
def run():
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

if __name__ == "__main__":
    run() 