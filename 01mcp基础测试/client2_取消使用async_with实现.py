import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("当前工作目录：", os.getcwd())

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

# ==============================
#  1. MCP 客户端参数配置
# ==============================
# StdioServerParameters 封装了启动 MCP 服务器进程的方式
# 这里指定通过 python 运行 server1.py 与服务端通信
server_params = StdioServerParameters(
    command="python",           # 启动进程命令
    args=["server1.py"],        # 启动参数，等价于 python server1.py
    # env=None                 # 可以指定自定义环境变量（通常用默认环境就行）
)

# ===================================
#  2. MCP 标准输入输出客户端封装类
# ===================================

class StdioServerClient:
    """
    MCP 客户端，负责启动/关闭与 MCP 服务器的异步连接，并暴露会话对象 session 供多种操作。

    注：
      - 本类适合反复 open()/close() 使用，且可在多协程并发环境下安全调用。
      - 重点说明异步 context manager 手动生命周期管理以及加锁安全机制。
    """
    def __init__(self, server_params: StdioServerParameters = server_params):
        # 保存启动参数
        self.server_params = server_params

        # 异步上下文管理对象（context manager object）
        self.client_ctx = None     # 控制标准输入输出流 stdio_client(...)，原本通常配合 async with 使用
        self.session_ctx = None    # 管理 MCP 客户端会话对象

        # 底层流和 session
        self.read = None           # 服务端的标准输出流（读取服务端返回数据）
        self.write = None          # 服务端的标准输入流（发送数据到服务端）
        self.session = None        # 真正的会话对象（ClientSession 实例，用于协议交互）
        self.capabilities = None   # 记录服务端返回的能力信息

        # 保护 open/close 的 asyncio.Lock，防止多个并发协程对连接资源状态竞争
        self._open_lock = asyncio.Lock()
        self._is_open = False      # 状态位：记录当前是否已开连接

    async def open(self):
        """
        手动建立连接，等价于两层 async with:
           async with stdio_client(...) as (read, write):
               async with ClientSession(read, write) as session:
                   ...
        拆成底层显式 __aenter__ 调用，让会话及底层流全生命周期掌控在 client 实例中。
        加锁以确保线程/协程安全（防止并发 open 混乱）。
        """
        async with self._open_lock:
            if self._is_open:
                # 已经打开则直接跳过，多次 open 安全幂等
                return

            # 1. 创建与服务器 subprocess 通信的标准流，client_ctx 是异步 context manager
            #    stdio_client(...) 返回异步生成器对象，实际可通过 __aenter__/__aexit__ 控制资源
            self.client_ctx = stdio_client(self.server_params)
            self.read, self.write = await self.client_ctx.__aenter__()  # 启动 subprocess，获取读写流对象

            # 2. 创建 MCP Session，上面拿到的 read/write 用于与 server 交互
            self.session_ctx = ClientSession(self.read, self.write)
            self.session = await self.session_ctx.__aenter__()  # 进入协议会话生命周期
            self.capabilities = await self.session.initialize() # 初始化 handshake，协商能力
            self._is_open = True

    async def close(self):
        """
        主动关闭连接。
        关闭顺序与 open 相反，先关闭协议 session，再关闭底层通信流，最后清空状态。
        通过加锁与 _is_open 保证多协程/多次 close() 安全幂等。
        """
        async with self._open_lock:
            if not self._is_open:
                # 已关则跳过，幂等
                return

            # 首先关闭协议 session（释放协议缓冲、流等资源）
            if self.session_ctx is not None:
                await self.session_ctx.__aexit__(None, None, None)
                self.session_ctx = None
                self.session = None

            # 然后关闭 subprocess 管理的标准流
            if self.client_ctx is not None:
                await self.client_ctx.__aexit__(None, None, None)
                self.client_ctx = None
                self.read = None
                self.write = None

            self._is_open = False

    async def list_tools(self):
        """
        业务示例：调用 servers 的 list_tools 工具，并打印服务端响应。
        前提必须 open() 后才可调用 session（即建立好底层流和协议会话）。
        任何需要与服务端通信的操作都应在 open()~close() 间进行。
        """
        tools = await self.session.list_tools()   # 通过 MCP 协议调用服务器的工具资源
        print("tools:", tools)                    # 打印服务器支持的 tool 信息


    @property
    def get_session(self):
        return self.session
    
    @property
    def get_capabilities(self):
        return self.capabilities



# =====================================
#  3. 客户端主流程：示范如何使用上面 client
# =====================================

async def main():
    client = StdioServerClient()
    try:
        await client.open()    # 显式建立与 MCP server 的异步连接
        await client.list_tools()     # 执行 MCP 相关业务逻辑
    finally:
        await client.close()   # 无论是否抛异常，最后都需关闭资源，防止资源泄漏

if __name__ == "__main__":
    # 用 asyncio 事件循环驱动异步 main 入口。标准写法。
    asyncio.run(main())
