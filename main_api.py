"""
修复后的主API服务 - 支持多个工作流路由和连接池管理
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import gc

# 导入工作流会话
from workflows.survey_workflow import SurveyWorkflowSession
from workflows.solution_workflow import SolutionDesignWorkflowSession
from workflows.paper_workflow import PaperWritingWorkflowSession

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoGen Multi-Workflow Research API")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局会话管理 - 分工作流类型管理
active_sessions: Dict[str, Dict[str, Any]] = {
    "survey": {},
    "solution": {},
    "paper": {}
}

# 工作流类型映射
WORKFLOW_TYPES = {
    "survey": SurveyWorkflowSession,
    "solution": SolutionDesignWorkflowSession,
    "paper": PaperWritingWorkflowSession
}

# 连接限制配置
MAX_SESSIONS_PER_WORKFLOW = 3
MAX_TOTAL_SESSIONS = 5


async def cleanup_idle_sessions():
    """清理空闲会话"""
    try:
        total_cleaned = 0
        for workflow_type, sessions in active_sessions.items():
            to_remove = []
            for session_id, session in sessions.items():
                if not session.is_running:
                    await session.cleanup()
                    to_remove.append(session_id)
                    total_cleaned += 1

            for session_id in to_remove:
                del sessions[session_id]

        if total_cleaned > 0:
            logger.info(f"清理了 {total_cleaned} 个空闲会话")
            gc.collect()  # 强制垃圾回收

    except Exception as e:
        logger.error(f"清理会话时出错: {e}")


async def check_session_limits(workflow_type: str) -> bool:
    """检查会话限制"""
    # 清理空闲会话
    await cleanup_idle_sessions()

    # 检查特定工作流限制
    if len(active_sessions[workflow_type]) >= MAX_SESSIONS_PER_WORKFLOW:
        return False

    # 检查总会话限制
    total_sessions = sum(len(sessions) for sessions in active_sessions.values())
    if total_sessions >= MAX_TOTAL_SESSIONS:
        return False

    return True


async def handle_websocket_workflow(websocket: WebSocket, workflow_type: str):
    """处理WebSocket工作流通信的通用函数"""
    session_id = str(uuid.uuid4())
    session = None

    try:
        await websocket.accept()
        logger.info(f"WebSocket连接已接受，{workflow_type} 工作流，会话 {session_id}")

        # 检查会话限制
        if not await check_session_limits(workflow_type):
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": f"❌ {workflow_type} 工作流连接数已达上限，请稍后再试",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
            return

        # 根据工作流类型创建会话
        workflow_class = WORKFLOW_TYPES.get(workflow_type)
        if not workflow_class:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": f"不支持的工作流类型: {workflow_type}",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
            return

        # 创建并初始化会话
        session = workflow_class(websocket, session_id)
        active_sessions[workflow_type][session_id] = session

        if not await session.initialize():
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "无法初始化会话",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
            return

        # 发送欢迎消息
        welcome_messages = {
            "survey": "🔍 欢迎使用文献调研工作流！\n\n💡 使用指南:\n- 发送您要研究的主题开始调研\n- 工作流会逐步进行，您可以随时提供指导\n- 输入 'APPROVE' 完成工作流\n\n请发送您的研究主题:",
            "solution": "🏗️ 欢迎使用方案设计工作流！\n\n💡 使用指南:\n- 基于文献调研结果描述您的技术方案需求\n- 系统会进行方案设计、评审和细化\n- 您可以在每个阶段提供反馈\n- 输入 'APPROVE' 完成工作流\n\n请描述您的方案需求:",
            "paper": "📝 欢迎使用论文写作工作流！\n\n💡 使用指南:\n- 基于实验结果描述您要撰写的论文\n- 系统会协助完成各个章节的写作\n- 您可以指导写作方向和风格\n- 输入 'APPROVE' 完成工作流\n\n请描述您的论文主题:"
        }

        await websocket.send_text(json.dumps({
            "type": "system_message",
            "content": welcome_messages.get(workflow_type, "欢迎使用AI研究助手！"),
            "name": "system",
            "timestamp": datetime.now().isoformat()
        }))

        workflow_started = False

        while True:
            # 等待客户端消息
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=600.0)  # 10分钟超时
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({
                    "type": "system_message",
                    "content": "⏰ 连接超时，会话即将关闭",
                    "name": "system",
                    "timestamp": datetime.now().isoformat()
                }))
                break

            message = json.loads(data)
            content = message.get("content", "").strip()

            if not content:
                continue

            # 显示用户消息
            await websocket.send_text(json.dumps({
                "type": "user_message",
                "content": content,
                "name": "user",
                "timestamp": datetime.now().isoformat()
            }))

            # 检查是否是控制指令
            if content.upper() in ["QUIT", "EXIT", "CLOSE"]:
                await websocket.send_text(json.dumps({
                    "type": "system_message",
                    "content": "👋 会话已关闭，感谢使用！",
                    "name": "system",
                    "timestamp": datetime.now().isoformat()
                }))
                break

            if not workflow_started:
                # 启动工作流
                success = await session.start_workflow(content)
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
                # 处理用户输入
                session.handle_user_input(content)

                # 检查是否要结束会话
                if content.upper().strip() in ["APPROVE", "END", "FINISH"]:
                    await asyncio.sleep(2)  # 等待工作流处理
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket断开连接，{workflow_type} 工作流，会话 {session_id}")
    except Exception as e:
        logger.error(f"WebSocket错误，{workflow_type} 工作流，会话 {session_id}: {e}")
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
        # 清理会话
        if session:
            await session.cleanup()

        if session_id in active_sessions.get(workflow_type, {}):
            del active_sessions[workflow_type][session_id]
            logger.info(f"{workflow_type.title()} 工作流会话 {session_id} 已从活跃会话中移除")


@app.websocket("/ws/survey")
async def websocket_survey_endpoint(websocket: WebSocket):
    """文献调研工作流WebSocket端点"""
    await handle_websocket_workflow(websocket, "survey")


@app.websocket("/ws/solution")
async def websocket_solution_endpoint(websocket: WebSocket):
    """方案设计工作流WebSocket端点"""
    await handle_websocket_workflow(websocket, "solution")


@app.websocket("/ws/paper")
async def websocket_paper_endpoint(websocket: WebSocket):
    """论文写作工作流WebSocket端点"""
    await handle_websocket_workflow(websocket, "paper")


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "AutoGen Multi-Workflow Research API is running",
        "version": "2.1.0",
        "features": [
            "持续交互式工作流",
            "智能会话管理",
            "连接池优化",
            "用户控制的工作流终止"
        ],
        "workflows": {
            "survey": "/ws/survey",
            "solution": "/ws/solution",
            "paper": "/ws/paper"
        },
        "endpoints": {
            "health": "/health",
            "sessions": "/sessions",
            "cleanup": "/cleanup"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    workflow_stats = {}
    total_sessions = 0

    for workflow_type, sessions in active_sessions.items():
        running_count = sum(1 for session in sessions.values() if session.is_running)
        workflow_stats[workflow_type] = {
            "total": len(sessions),
            "running": running_count,
            "idle": len(sessions) - running_count
        }
        total_sessions += len(sessions)

    return {
        "status": "healthy",
        "active_sessions": total_sessions,
        "max_sessions": MAX_TOTAL_SESSIONS,
        "workflow_stats": workflow_stats,
        "memory_usage": "监控中",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/sessions")
async def list_sessions():
    """列出活跃会话"""
    sessions_info = []
    for workflow_type, sessions in active_sessions.items():
        for session_id, session in sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "workflow_type": workflow_type,
                "workflow_name": session.get_workflow_name(),
                "is_running": session.is_running,
                "has_team": session.team is not None,
                "continue_interaction": getattr(session, 'continue_interaction', True)
            })

    return {
        "active_sessions": len(sessions_info),
        "sessions": sessions_info
    }


@app.post("/cleanup")
async def manual_cleanup():
    """手动清理空闲会话"""
    await cleanup_idle_sessions()

    total_sessions = sum(len(sessions) for sessions in active_sessions.values())
    return {
        "message": "清理完成",
        "remaining_sessions": total_sessions,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/workflows")
async def list_workflows():
    """列出支持的工作流"""
    workflows = []
    for workflow_type, workflow_class in WORKFLOW_TYPES.items():
        current_sessions = len(active_sessions[workflow_type])
        workflows.append({
            "type": workflow_type,
            "name": workflow_class.__name__,
            "endpoint": f"/ws/{workflow_type}",
            "description": f"{workflow_type.title()} workflow for research automation",
            "current_sessions": current_sessions,
            "max_sessions": MAX_SESSIONS_PER_WORKFLOW,
            "available": current_sessions < MAX_SESSIONS_PER_WORKFLOW
        })

    return {
        "supported_workflows": workflows,
        "total_count": len(workflows)
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动AutoGen多工作流研究API服务器...")
    print("=" * 60)
    print("📡 文献调研工作流: ws://localhost:8000/ws/survey")
    print("🏗️ 方案设计工作流: ws://localhost:8000/ws/solution")
    print("📝 论文写作工作流: ws://localhost:8000/ws/paper")
    print("-" * 60)
    print("🔍 健康检查: http://localhost:8000/health")
    print("📋 会话列表: http://localhost:8000/sessions")
    print("🧹 手动清理: http://localhost:8000/cleanup")
    print("🔧 工作流列表: http://localhost:8000/workflows")
    print("=" * 60)
    print("💡 新功能:")
    print("- 持续交互式工作流，支持多轮对话")
    print("- 用户可随时输入 'APPROVE' 结束工作流")
    print("- 智能连接池管理，避免资源冲突")
    print("- 自动清理空闲会话")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )