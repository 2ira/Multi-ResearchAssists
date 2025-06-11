from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from tools.search_tool import search_arxiv
import asyncio
from model_factory import create_model_client

async def test_tool_call():
    # 创建工具
    arxiv_tool = FunctionTool(
        func=search_arxiv,
        description="Search arXiv papers",
        strict=False
    )

    # 创建agent
    model_client = create_model_client("default_model")
    assistant = AssistantAgent(
        "assistant",
        model_client=model_client,
        tools=[arxiv_tool],
        reflect_on_tool_use=False,  # 暂时关闭反射
        model_client_stream=False
    )

    # 生成回复（使用 async for 遍历流式响应）run_stream返回的是异步生成器，需要
    print("Agent response:")
    async for chunk in assistant.run_stream( task="What is GNN?"):
        # 处理每个流式响应块（例如打印或拼接内容）
        print(chunk, end="", flush=True)  # 逐字符打印，模拟流式效果
    print("\n\nComplete response above.")

    # 关闭客户端
    await model_client.close()


if __name__ == "__main__":
    asyncio.run(test_tool_call())