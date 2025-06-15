import asyncio
from autogen import GroupChat, GroupChatManager
import os
from agents.code_generate.code_assistant import get_code_assistant
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console

from autogen_agentchat.conditions import TextMentionTermination
async def run_code(plan:str):
    # 创建代理
    code_assistant = get_code_assistant()

    # 创建用户代理（任务发起者）
    user_proxy = UserProxyAgent(
        "UserProxy",
        input_func=input
    )

    termination_condition = TextMentionTermination("APPROVE")

    team = RoundRobinGroupChat(
        [code_assistant,user_proxy],  # particapates
        termination_condition=termination_condition,  # when occurs APPROVE the workflow is terminate
        emit_team_events=True  # enable team event stream
    )

    # start task stream
    message_stream = team.run_stream(task=f"请你写代码完成任务：{plan}")

    print("消息流启动，等待控制台输出...")

    # use console to consume message_stream
    result = await Console(
        message_stream,
        no_inline_images=True,  # 禁用内联图
        output_stats=True  # 开启统计信息
    )

    print("工作流结束，结果：", result)

    return result


# 示例调用
if __name__ == "__main__":
    asyncio.run(run_code("模拟10组房价以及面积的数据，写一个二次函数对其进行拟合"))
