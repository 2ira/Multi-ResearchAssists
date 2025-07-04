import json
import logging
import os
from typing import Any, Awaitable, Callable, Optional

import aiofiles
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, UserInputRequestedEvent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI()

# 初始化配置cors,允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# 从你的代码导入代理创建函数
from agents.article_research.survey_director import get_survey_director
from agents.article_research.paper_retriever import get_paper_retriever
from agents.article_research.paper_summarizer import get_paper_summarizer
from agents.article_research.paper_analyzer import get_survey_analyst

#用于保存历史会话，服务中断仍然可以持续执行
state_path = "team_state.json"
history_path = "team_history.json"

# 用户代理类，异步介绍从websocket发送的消息
class CustomUserProxyAgent(UserProxyAgent):
    def __init__(self, name, websocket):
        super().__init__(name=name)
        self.websocket = websocket

    async def get_human_input(self, prompt: str) -> str:
        # 发送提示到前端并等待用户输入
        await self.websocket.send_json({
            "type": "UserInputRequestedEvent",
            "content": prompt,
            "source": "system"
        })
        data = await self.websocket.receive_json()
        message = TextMessage.model_validate(data)
        return message.content

# 根据配置文件创建客户端以及多个智能体
async def get_team(websocket: WebSocket) -> RoundRobinGroupChat:

    # 创建代理
    survey_director = get_survey_director()
    paper_retriever = get_paper_retriever()
    paper_summarizer = get_paper_summarizer()
    survey_analyst = get_survey_analyst()

    # UserProxy
    user_proxy = CustomUserProxyAgent(
        name="user",
        websocket=websocket
    )

    # terminate condition
    termination = TextMentionTermination("APPROVE")

    # create team
    team = RoundRobinGroupChat(
        [survey_director, paper_retriever, paper_summarizer, survey_analyst, user_proxy],
        termination_condition=termination,
        emit_team_events=True
    )

    # load status if exists
    if os.path.exists(state_path):
        async with aiofiles.open(state_path, "r") as file:
            state = json.loads(await file.read())
        await team.load_state(state)

    return team

# load history if exists
async def get_history() -> list[dict[str, Any]]:
    """Get chat history from file."""
    if not os.path.exists(history_path):
        return []
    async with aiofiles.open(history_path, "r") as file:
        return json.loads(await file.read())


@app.get("/history")
async def history() -> list[dict[str, Any]]:
    try:
        return await get_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()

    # wait socket receive massage and run
    try:
        # 接收初始主题
        data = await websocket.receive_json()
        initial_message = TextMessage.model_validate(data)
        topic = initial_message.content

        # 创建团队
        team = await get_team(websocket)
        history = await get_history()

        # 启动工作流
        stream = team.run_stream(task=f"开始调研主题：{topic}")

        # 处理消息流
        async for message in stream:
            if isinstance(message, TaskResult):
                continue

            # 发送消息到前端
            await websocket.send_json(message.model_dump())

            # 保存到历史（除了用户输入请求）
            if not isinstance(message, UserInputRequestedEvent):
                history.append(message.model_dump())

        # 保存团队状态和历史
        async with aiofiles.open(state_path, "w") as file:
            state = await team.save_state()
            await file.write(json.dumps(state))

        async with aiofiles.open(history_path, "w") as file:
            await file.write(json.dumps(history))


    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    try:
        await websocket.send_json({
            "type": "error",
            "content": f"Unexpected error: {str(e)}",
            "source": "system"
        })
    except:
        pass


# Example usage
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)