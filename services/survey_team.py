from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.models import UserMessage
from autogen_agentchat.agents import UserProxyAgent
import asyncio
from autogen_agentchat.messages import TextMessage

from agents.article_research.survey_director import get_survey_director
from agents.article_research.paper_retriver import get_paper_retriever
from agents.article_research.paper_summarizer import get_paper_summarizer
from agents.article_research.survey_analyst import get_survey_analyst

from autogen_agentchat.conditions import TextMentionTermination


async def run_survey_workflow(topic: str):
    print("开始工作流初始化...")

    # build agents
    survey_director = get_survey_director()
    paper_retriever = get_paper_retriever()
    paper_summarizer = get_paper_summarizer()
    survey_analyst = get_survey_analyst()

    print("代理初始化完成")

    # add user proxy
    user_proxy = UserProxyAgent(
        name="user",
        description="人工用户，可以进行批准、细化或者补充检索",
        input_func=input
    )

    """
    async def simple_user_agent():
    agent = UserProxyAgent("user_proxy")
    response = await asyncio.create_task( agent.on_messages( [TextMessage(content="What is your name? ", source="user")],
    cancellation_token=CancellationToken(), ) ) 
    assert isinstance(response.chat_message, TextMessage) 
    print(f"Your name is {response.chat_message.content}")
    """

    # create terminate condition: check key words
    termination_condition = TextMentionTermination("APPROVE")

    print("团队创建完成，开始运行流...")
    # create team: use many agents and set turns
    team = RoundRobinGroupChat(
        [survey_director, paper_retriever, paper_summarizer, survey_analyst, user_proxy],  # particapates
        termination_condition=termination_condition,  # when occurs APPROVE the workflow is terminate
        # max_turns= 3 ,
        # custom_message_types=[TextMessage], #TextMessage是默认注册
        emit_team_events=True  # enable team event stream
    )

    # start task stream
    message_stream = team.run_stream(task=f"开始调研主题：{topic}")

    print("消息流启动，等待控制台输出...")

    # use console to consume message_stream
    result = await Console(
        message_stream,
        no_inline_images=True, #禁用内联图
        output_stats=True # 开启统计信息
    )

    print("工作流结束，结果：", result)

    return result

# 示例调用
if __name__ == "__main__":
    asyncio.run(run_survey_workflow("大语言模型在推荐系统中的应用"))
