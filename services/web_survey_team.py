from autogen_agentchat.base import TaskResult
from autogen_core import FunctionCall
from autogen_core.models import FunctionExecutionResult
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import threading
import queue
from typing import Dict, Any, Optional, Union
from datetime import datetime
import uuid
import sys

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from model_factory import create_model_client

# Import your agent modules
from agents.article_research.survey_director import get_survey_director
from agents.article_research.paper_retriever import get_paper_retriever
from agents.article_research.paper_summarizer import get_paper_summarizer
from agents.article_research.paper_analyzer import get_survey_analyst
from autogen_agentchat.messages import ChatMessage

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoGen Research Workflow API")

# Add CORS middleware，完成跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebSocketUserProxyAgent(UserProxyAgent):
    """
    websocket user proxy
    """

    def __init__(self, websocket: WebSocket, name: str = "user_proxy"):
        self.websocket = websocket
        self.input_queue = queue.Queue()  # 线程安全的输入队列
        super().__init__(name, input_func=self._websocket_input_func)

    def _websocket_input_func(self, prompt: str) -> str:
        """
        自定义输入函数，通过WebSocket获取用户输入
        这个函数被AutoGen同步调用，所以我们需要处理同步/异步桥接
        """
        try:
            logger.info(f"Requesting user input: {prompt}")

            # 在事件循环中发送输入请求
            asyncio.run_coroutine_threadsafe(
                self._send_input_request(prompt),
                asyncio.get_event_loop(),
            ).result(timeout=5.0)

            # waiting for user input
            try:
                user_input = self.input_queue.get(timeout=300)  # 5分钟超时
                logger.info(f"Received user input: {user_input}")
                return user_input
            except queue.Empty:
                logger.warning("User input timeout, using default response")
                return "继续"

        except Exception as e:
            logger.error(f"Error in _websocket_input_func: {e}")
            return "继续"

    async def _send_input_request(self, prompt: str):
        """向WebSocket客户端发送输入请求"""
        try:
            message = {
                "type": "user_input_requested",
                "content": prompt,
                "name": "user_proxy",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send_text(json.dumps(message))
            logger.info("Input request sent successfully")
        except Exception as e:
            logger.error(f"Error sending input request: {e}")

    def provide_user_input(self, user_input: str):
        """接收来自WebSocket的用户输入"""
        try:
            self.input_queue.put(user_input, timeout=1)
            logger.info(f"User input queued: {user_input}")
        except queue.Full:
            logger.warning("Input queue is full, discarding input")


class ResearchWorkflowSession:
    """管理单个研究工作流会话"""

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.model_client = None
        self.team = None
        self.user_proxy = None
        self.is_running = False
        self.workflow_thread = None
        self.termination_condition = None

    async def initialize(self):
        """初始化工作流会话"""
        try:
            logger.info(f"Initializing session {self.session_id}")

            self.model_client = create_model_client("default_model")

            # websocket user proxy
            self.user_proxy = WebSocketUserProxyAgent(self.websocket, "user_proxy")

            # workflow agent
            survey_director = get_survey_director()
            paper_retriever = get_paper_retriever()
            paper_summarizer = get_paper_summarizer()
            survey_analyst = get_survey_analyst()

            # create end signal
            self.termination_condition = TextMentionTermination("APPROVE")

            # team group
            self.team = RoundRobinGroupChat(
                [survey_director, paper_retriever, paper_summarizer, survey_analyst, self.user_proxy],
                termination_condition=self.termination_condition,
            )

            logger.info(f"Session {self.session_id} initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing session {self.session_id}: {e}")
            return False

    # send start message to client and run _run_workflow_sync
    async def start_research(self, topic: str):
        """启动研究工作流"""
        if self.is_running:
            logger.warning(f"Session {self.session_id} is already running")
            return False

        try:
            self.is_running = True

            # send start notice
            await self.websocket.send_text(json.dumps({
                "type": "workflow_started",
                "content": f"开始研究主题: {topic}",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))

            # single thread to run thread
            self.workflow_thread = threading.Thread(
                target=self._run_workflow_sync,
                args=(topic,),
                daemon=True
            )
            self.workflow_thread.start()

            logger.info(f"Research started for session {self.session_id} with topic: {topic}")
            return True

        except Exception as e:
            logger.error(f"Error starting research: {e}")
            self.is_running = False
            await self._send_error_message(f"启动研究失败: {str(e)}")
            return False

    def _run_workflow_sync(self, topic: str):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info(f"Starting workflow execution for topic: {topic}")

            # 创建异步任务运行工作流
            async def run_workflow():
                # 使用 run_stream 捕获消息流
                stream = self.team.run_stream(task=f"Research topic: {topic}")

                # 处理消息流
                async for message in stream:
                    # 转发消息到客户端
                    await self._forward_message(message)

                    # 检查终止条件
                    content = getattr(message, 'content', '')
                    if any(term in content for term in ["APPROVE"]):
                        logger.info("检测到终止信号，停止工作流")
                        await self._send_completion_message()
                        return

            # 运行异步任务
            loop.run_until_complete(run_workflow())

            # 发送完成消息
            loop.run_until_complete(self._send_completion_message())

            logger.info(f"Workflow completed for session {self.session_id}")

        except Exception as e:
            logger.exception(f"Error in workflow execution: {e}")
            loop.run_until_complete(
                self._send_error_message(f"工作流程执行出错: {str(e)}")
            )
        finally:
            self.is_running = False
            # 关闭事件循环
            loop.close()

    def _serialize_function_call(self, func_obj):
        """序列化 FunctionCall 和 FunctionExecutionResult 对象"""
        if isinstance(func_obj, FunctionCall):
            return {
                "type": "function_call",
                "name": getattr(func_obj, 'name', 'unknown'),
                "arguments": getattr(func_obj, 'arguments', {}),
                "call_id": getattr(func_obj, 'call_id', '')
            }
        elif isinstance(func_obj, FunctionExecutionResult):
            return {
                "type": "function_result",
                "name": getattr(func_obj, 'name', 'unknown'),
                "content": getattr(func_obj, 'content', ''),
                "is_error": getattr(func_obj, 'is_error', False),
                "call_id": getattr(func_obj, 'call_id', '')
            }
        return str(func_obj)

    async def _forward_message(self, message: Any):
        """安全地将消息转发到客户端，处理特殊对象"""
        try:
            # 处理不同类型的消息内容
            if hasattr(message, 'content'):
                # 处理 FunctionCall 和 FunctionExecutionResult 对象
                if isinstance(message.content, (FunctionCall, FunctionExecutionResult)):
                    content = self._serialize_function_call(message.content)
                else:
                    content = getattr(message, 'content', str(message))
            else:
                content = str(message)

            # 提取发送者名称
            name = getattr(message, 'source', 'system')

            # 确定消息类型
            msg_type = "agent_message"
            if hasattr(message, 'type'):
                msg_type = getattr(message, 'type', 'agent_message').lower()

            # 发送到客户端
            await self.websocket.send_text(json.dumps({
                "type": msg_type,
                "content": content,
                "name": name,
                "timestamp": datetime.now().isoformat()
            }))

            logger.info(f"已转发来自 {name} 的消息: {content[:50]}...")
        except WebSocketDisconnect:
            logger.warning("转发消息时连接已断开")
            self.is_running = False  # 停止工作流
        except Exception as e:
            logger.exception(f"转发消息时出错: {e}")

    async def _send_completion_message(self):
        try:
            await self.websocket.send_text(json.dumps({
                "type": "workflow_completed",
                "content": "研究工作流程已完成",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending completion message: {e}")

    async def _send_error_message(self, error_msg: str):
        try:
            await self.websocket.send_text(json.dumps({
                "type": "error",
                "content": error_msg,
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    # put into a input queue
    def handle_user_input(self, user_input: str):
        if self.user_proxy:
            self.user_proxy.provide_user_input(user_input)
        else:
            logger.warning("No user proxy available to handle input")

    async def cleanup(self):
        """clean up client session"""
        try:
            logger.info(f"Cleaning up session {self.session_id}")
            self.is_running = False  # 确保工作流停止

            # 发送会话关闭通知
            try:
                await self.websocket.send_text(json.dumps({
                    "type": "session_closing",
                    "content": "会话正在关闭",
                    "name": "system",
                    "timestamp": datetime.now().isoformat()
                }))
                await asyncio.sleep(0.3)  # 给客户端处理时间
            except:
                pass

            # waiting for thread
            if self.workflow_thread and self.workflow_thread.is_alive():
                self.workflow_thread.join(timeout=30)

            # close client
            if self.model_client:
                await self.model_client.close()

            logger.info(f"Session {self.session_id} cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# global session
active_sessions: Dict[str, ResearchWorkflowSession] = {}


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点处理研究工作流通信"""
    session_id = str(uuid.uuid4())

    try:
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for session {session_id}")

        # create and initialize a session->开启socket监听，并且创建
        session = ResearchWorkflowSession(websocket, session_id)
        active_sessions[session_id] = session

        if not await session.initialize():
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "无法初始化会话",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
            return

        # send a text
        await websocket.send_text(json.dumps({
            "type": "system_message",
            "content": "🎯 欢迎使用AI研究助手！请发送您要研究的主题开始工作流程。",
            "name": "system",
            "timestamp": datetime.now().isoformat()
        }))

        workflow_started = False

        while True:
            # wait for client
            data = await websocket.receive_text()
            message = json.loads(data)

            content = message.get("content", "").strip()
            if not content:
                continue

            # show user messages
            await websocket.send_text(json.dumps({
                "type": "user_message",
                "content": content,
                "name": "user",
                "timestamp": datetime.now().isoformat()
            }))

            if not workflow_started:
                # start workflow
                success = await session.start_research(content)
                if success:
                    workflow_started = True
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "启动工作流失败，请重试",
                        "name": "system",
                        "timestamp": datetime.now().isoformat()
                    }))
            else:
                # handle user input
                session.handle_user_input(content)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": f"连接出错: {str(e)}",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
        except:
            pass
    finally:
        # clean session
        if session_id in active_sessions:
            await active_sessions[session_id].cleanup()
            del active_sessions[session_id]
            logger.info(f"Session {session_id} removed from active sessions")


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "AutoGen Research Workflow API is running",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/chat",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "session_ids": list(active_sessions.keys()),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/sessions")
async def list_sessions():
    """列出活跃会话"""
    sessions_info = []
    for session_id, session in active_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "is_running": session.is_running,
            "has_team": session.team is not None
        })

    return {
        "active_sessions": len(active_sessions),
        "sessions": sessions_info
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动AutoGen研究工作流API服务器...")
    print("📡 WebSocket端点: ws://localhost:8000/ws/chat")
    print("🔍 健康检查: http://localhost:8000/health")
    print("📋 会话列表: http://localhost:8000/sessions")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # 在生产环境中设为False
    )
