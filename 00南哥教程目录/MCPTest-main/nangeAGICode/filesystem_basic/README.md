# filesystem_basic 示例教程

## 1. 环境准备
- Node.js 与 npm（或直接使用 npx）
- Python 3.7+
- 安装 MCP 客户端库：
  ```bash
  pip install mcp
  ```

## 2. 目录结构
```
00南哥教程目录/
└── MCPTest-main/
    └── nangeAGICode/
        └── filesystem_basic/
            ├── client.py
            └── README.md
```

## 3. 依赖介绍
- **mcp**：Python 端 MCP 协议实现  
- **@modelcontextprotocol/server-filesystem**：Node.js 文件系统 MCP 服务器包  
- **asyncio**：Python 异步 I/O 框架，用于非阻塞通信  

## 4. 核心源码解读

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import mcp.types as types

# 指定服务器可操作的文件根目录
DirPath = "/…/filesystem_basic"

# 配置 stdio 模式下服务器的启动命令与参数
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", DirPath],
    env=None
)
```

- **DirPath**：指定服务器对哪个目录执行文件操作。  
- **StdioServerParameters**：
  - `command="npx"`：使用 npx 启动 Node.js MCP 服务器  
  - `args`：
    - `"-y"`：跳过交互确认  
    - `"@modelcontextprotocol/server-filesystem"`：MCP 文件系统服务器包  
    - `DirPath`：注入工作目录  

```python
async def run():
    # 建立与服务器的 stdio 流连接
    async with stdio_client(server_params) as (read, write):
        # 在该流上创建 MCP JSON-RPC 会话
        async with ClientSession(read, write) as session:
            # 握手，获取服务器版本与能力
            capabilities = await session.initialize()
            # 列出可调用的工具列表
            tools = await session.list_tools()
            print("tools:", tools)

            # 基础文件操作示例：列出允许操作的根目录
            result = await session.call_tool("list_allowed_directories")
            print("result:", result)

if __name__ == "__main__":
    asyncio.run(run())
```

- **stdio_client**：返回 `(read, write)` 两个 asyncio 流，用于标准输入/输出交换 JSON-RPC 消息。  
- **ClientSession**：
  - `initialize()`：完成协议握手  
  - `list_tools()`：获取所有可用工具名称  
  - `call_tool(name, arguments)`：调用指定功能（如 `list_directory`, `read_file`, `write_file` 等）

## 5. 常用工具示例
```python
# 列出根目录
await session.call_tool("list_allowed_directories")
# 创建子目录 test
await session.call_tool("create_directory", {"path": "test"})
# 写文件
await session.call_tool("write_file", {"path": "test/a.txt", "content": "Hello MCP"})
# 读文件
await session.call_tool("read_file", {"path": "test/a.txt"})
# 搜索文件名包含 “a.txt”
await session.call_tool("search_files", {"path": "test", "pattern": "a.txt"})
```

## 6. 运行方法
在项目根目录执行：
```bash
python 00南哥教程目录/MCPTest-main/nangeAGICode/filesystem_basic/client.py
```

## 7. 技术要点
- MCP 基于 JSON-RPC，统一前后端交互接口  
- STDIO 方式无需网络，适合本地进程通信  
- Python `asyncio` 保证非阻塞、高并发 I/O  
- 可通过修改 `server_params.args` 切换不同 MCP 服务器实现  

## 8. 拓展思路
- 增加异常捕获与日志、重试机制  
- 并发处理多个目录或文件，提高吞吐量  
- 将客户端封装为命令行工具或 GUI，实现可视化文件管理
