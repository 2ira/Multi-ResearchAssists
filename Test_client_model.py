import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
from tools.search_tool import search_arxiv
# Define a model client. You can use other model client that implements
# the `ChatCompletionClient` interface.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    base_url="https://api.agicto.cn/v1",
    api_key="sk-D3IUWYvD1LkNdjcpAyT7lttrggfA7ah2NuZxgIhTIfKz3JMK",
)

# Define a simple function tool that the agent can use.
# For this example, we use a fake weather tool for demonstration purposes.
async def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is 73 degrees and Sunny."



# 创建工具时使用更详细的描述
arxiv_tool = FunctionTool(
    func=search_arxiv,
    description="Search academic papers on arXiv. Use this tool when users ask about research papers, scientific topics, or academic literature.",
    strict=True  # 改为True以确保参数严格匹配
)

#
weather_tool = FunctionTool(
    func=get_weather,
    description="Get weather information for a specific city.",
    strict=True
)

# Define an AssistantAgent with the model, tool, system message, and reflection enabled.
# The system message instructs the agent via natural language.
# 创建代理，使用更详细的系统消息
agent = AssistantAgent(
    name="research_assistant",
    model_client=model_client,
    tools=[weather_tool, arxiv_tool],  # 同时包含两个工具
    system_message="""You are a helpful research assistant. You can:
1. Provide weather information for cities using the get_weather tool
2. Search for academic papers on arXiv using the search_arxiv tool
3. Answer questions about research topics by searching relevant papers

When a user asks about weather, use the get_weather tool.
When a user asks about academic topics, research papers, or scientific concepts, use the search_arxiv tool.
Always try to use the appropriate tool to provide accurate and helpful responses.""",
    reflect_on_tool_use=True,
    model_client_stream=True,
)

# Run the agent and stream the messages to the console.
async def main() -> None:
    print("🚀 启动测试...")

    # 1. 先测试原函数是否工作
    result = await search_arxiv("GNN")
    print("原函数测试:", result)

    # 测试天气查询
    print("\n=== 测试天气查询 ===")
    try:
        await Console(agent.run_stream(task="What is the weather in New York?"))
    except Exception as e:
        print(f"Weather query error: {e}")

    print("\n=== 测试arXiv搜索 ===")
    # 测试arXiv搜索
    try:
        await Console(
            agent.run_stream(task="What is GNN? Please search for recent papers about Graph Neural Networks."))
    except Exception as e:
        print(f"arXiv search error: {e}")

    # 关闭模型客户端连接
    await model_client.close()
    print("✅ 测试完成")

# NOTE: if running this inside a Python script you'll need to use asyncio.run(main()).
asyncio.run(main())
