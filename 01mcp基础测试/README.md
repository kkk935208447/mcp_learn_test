# 简介
本项目是一个简单的 mcp 服务器的测试项目，使用的底层的stdio标准输入输出实现的 server端与client端，并且实现了基于LLM多轮对话递归调用mcp工具的功能




# 运行
1. mcp client 端简单测试
```bash
cd 01mcp基础测试 
uv run client1.py
```

2. mcp server 启动
```bash
cd 01mcp基础测试 
uv run server1.py
```

3. LLM 对话式调用测试
```bash
cd 01mcp基础测试
uv run llm_chat_openai库.py
```




# 简单的总结
1. 底层的 mcp 服务器 from mcp.server import Server 无法使用 mcp dev server 调试
2. LLM function call 具体可见 `LLM多轮fuctioncall测试` 目录介绍，当返回多个function时，需要调用全部function得到结果，然后分别加入到 messages 实现多轮对话（role 为 tool 相对于 role function 来说，LLM 输出更加稳定）
3. 若LLM本身不支持function call，则需要使用system prompt来加入 mcp 服务的工具资源，引导LLM进行格式化输出