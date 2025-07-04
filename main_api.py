"""
文献调研顺序交互主API服务
修正版本：与新的base_workflow.py完全兼容
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

# 导入文献调研工作流会话
from workflows.survey_workflow import SurveyWorkflowSession

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Literature Survey Sequential Pipeline API")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话管理 - 专注于文献调研
active_sessions: Dict[str, Any] = {}

# 连接限制配置
MAX_SESSIONS = 5


async def cleanup_idle_sessions():
    """清理空闲会话"""
    try:
        total_cleaned = 0
        to_remove = []
        for session_id, session in active_sessions.items():
            if not session.is_running:
                try:
                    await session.cleanup()
                except Exception as e:
                    logger.warning(f"清理会话 {session_id} 时出错: {e}")
                to_remove.append(session_id)
                total_cleaned += 1

        for session_id in to_remove:
            del active_sessions[session_id]

        if total_cleaned > 0:
            logger.info(f"清理了 {total_cleaned} 个空闲会话")
            gc.collect()

    except Exception as e:
        logger.error(f"清理会话时出错: {e}")


async def check_session_limits() -> bool:
    """检查会话限制"""
    await cleanup_idle_sessions()
    return len(active_sessions) < MAX_SESSIONS


async def handle_websocket_survey(websocket: WebSocket):
    """处理文献调研WebSocket连接"""
    session_id = str(uuid.uuid4())
    session = None

    try:
        await websocket.accept()
        logger.info(f"文献调研WebSocket连接已接受，会话 {session_id}")

        # 检查会话限制
        if not await check_session_limits():
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "❌ 文献调研连接数已达上限，请稍后再试",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
            return

        # 创建并初始化文献调研会话
        session = SurveyWorkflowSession(websocket, session_id)
        active_sessions[session_id] = session

        if not await session.initialize():
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "无法初始化文献调研会话",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))
            return

        # 发送文献调研欢迎消息
        welcome_message = """🔬 欢迎使用文献调研智能助手！

📋 **顺序执行流程**:
1. 📋 **任务分配阶段** (SurveyDirector)
   - 分析研究主题，制定调研策略
   - 确定检索关键词和数据库选择
   
2. 🔍 **论文获取阶段** (PaperRetriever)
   - 根据策略检索相关学术论文
   - 筛选高质量文献资源
   
3. 📝 **单篇摘要阶段** (PaperSummarizer)
   - 逐一分析每篇论文
   - 生成结构化摘要
   
4. 📊 **综述报告阶段** (SurveyAnalyst)
   - 整合所有摘要信息
   - 生成完整综述报告

💡 **交互方式**:
- 每个阶段完成后会等待您的确认
- 您可以选择 **继续下一阶段** 或 **重新执行当前阶段**
- 可以提供具体调整意见指导智能体优化工作

🚀 **开始使用**:
请输入您的研究主题，开始文献调研："""

        await websocket.send_text(json.dumps({
            "type": "system_message",
            "content": welcome_message,
            "name": "system",
            "timestamp": datetime.now().isoformat()
        }))

        workflow_started = False

        while True:
            # 等待客户端消息
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            except asyncio.TimeoutError:
                # 检查工作流是否完成
                if hasattr(session, 'is_workflow_completed') and session.is_workflow_completed():
                    logger.info(f"检测到文献调研完成，准备关闭连接，会话 {session_id}")
                    await asyncio.sleep(1)
                    break
                continue
            except WebSocketDisconnect:
                logger.info(f"客户端主动断开连接，会话 {session_id}")
                break

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"收到无效JSON消息: {data}")
                continue

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
                    "content": "👋 文献调研会话已关闭，感谢使用！",
                    "name": "system",
                    "timestamp": datetime.now().isoformat()
                }))
                break

            if not workflow_started:
                # 启动文献调研工作流
                try:
                    success = await session.start_workflow(content)
                    if success:
                        workflow_started = True
                        await websocket.send_text(json.dumps({
                            "type": "system_message",
                            "content": "✅ 文献调研工作流已启动，将按顺序执行各个阶段...",
                            "name": "system",
                            "timestamp": datetime.now().isoformat()
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "content": "启动文献调研失败，请重试",
                            "name": "system",
                            "timestamp": datetime.now().isoformat()
                        }))
                except Exception as e:
                    logger.error(f"启动工作流时出错: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": f"启动文献调研失败: {str(e)}",
                        "name": "system",
                        "timestamp": datetime.now().isoformat()
                    }))
            else:
                # 处理用户的阶段决策
                try:
                    session.handle_user_input(content)

                    # 检查是否是结束指令
                    if content.upper().strip() in ["END", "FINISH"]:
                        logger.info(f"收到结束指令: {content}，会话 {session_id}")

                        await websocket.send_text(json.dumps({
                            "type": "system_message",
                            "content": "✅ 正在结束文献调研...",
                            "name": "system",
                            "timestamp": datetime.now().isoformat()
                        }))

                        # 等待工作流处理结束指令
                        await asyncio.sleep(2)

                        # 发送最终完成消息
                        await websocket.send_text(json.dumps({
                            "type": "workflow_completed",
                            "content": "🎉 文献调研工作流已成功完成！感谢您的参与。",
                            "name": "system",
                            "timestamp": datetime.now().isoformat()
                        }))

                        await asyncio.sleep(1)
                        break
                    else:
                        # 普通阶段决策，发送确认消息
                        if content.upper() in ["APPROVE", "确认"]:
                            decision_msg = "继续下一阶段"
                        elif content.upper() in ["REGENERATE", "重新生成"]:
                            decision_msg = "重新执行当前阶段"
                        else:
                            decision_msg = "根据您的意见调整当前阶段"

                        await websocket.send_text(json.dumps({
                            "type": "system_message",
                            "content": f"✅ 已收到您的决策: {decision_msg}，智能体将据此执行...",
                            "name": "system",
                            "timestamp": datetime.now().isoformat()
                        }))
                except Exception as e:
                    logger.error(f"处理用户输入时出错: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": f"处理输入时出错: {str(e)}",
                        "name": "system",
                        "timestamp": datetime.now().isoformat()
                    }))

    except WebSocketDisconnect:
        logger.info(f"文献调研WebSocket断开连接，会话 {session_id}")
    except Exception as e:
        logger.error(f"文献调研WebSocket错误，会话 {session_id}: {e}")
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
            try:
                await session.cleanup()
            except Exception as e:
                logger.warning(f"清理会话时出错: {e}")

        if session_id in active_sessions:
            del active_sessions[session_id]
            logger.info(f"文献调研会话 {session_id} 已从活跃会话中移除")

        # 关闭WebSocket连接
        try:
            await websocket.close()
            logger.info(f"WebSocket连接已关闭，会话 {session_id}")
        except:
            pass


@app.websocket("/ws/survey")
async def websocket_survey_endpoint(websocket: WebSocket):
    """文献调研工作流WebSocket端点"""
    await handle_websocket_survey(websocket)


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Literature Survey Sequential Pipeline API is running",
        "version": "7.0.0",
        "mode": "文献调研顺序执行模式",
        "description": "专注于文献调研的顺序交互式AI助手",
        "features": [
            "4阶段顺序执行: 任务分配 → 论文获取 → 单篇摘要 → 综述报告",
            "每阶段完成后等待用户确认",
            "支持继续/重新生成/自定义调整",
            "智能体协作完成完整文献调研",
            "可视化进度跟踪"
        ],
        "workflow": {
            "name": "文献调研工作流",
            "endpoint": "/ws/survey",
            "stages": [
                {
                    "stage": 1,
                    "name": "任务分配阶段",
                    "agent": "SurveyDirector",
                    "description": "分析研究主题，制定调研策略和检索方案"
                },
                {
                    "stage": 2,
                    "name": "论文获取阶段",
                    "agent": "PaperRetriever",
                    "description": "根据策略检索相关学术论文"
                },
                {
                    "stage": 3,
                    "name": "单篇摘要阶段",
                    "agent": "PaperSummarizer",
                    "description": "逐一分析论文，生成结构化摘要"
                },
                {
                    "stage": 4,
                    "name": "综述报告阶段",
                    "agent": "SurveyAnalyst",
                    "description": "整合摘要，生成完整综述报告"
                }
            ]
        },
        "interaction_commands": {
            "approve": "输入 'APPROVE' 或 '确认' - 继续下一阶段",
            "regenerate": "输入 'REGENERATE' 或 '重新生成' - 重做当前阶段",
            "custom": "输入具体调整意见 - 根据要求优化当前阶段",
            "end": "输入 'END' - 提前结束工作流",
            "quit": "输入 'QUIT' - 退出会话"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        running_sessions = sum(1 for session in active_sessions.values() if hasattr(session, 'is_running') and session.is_running)
        waiting_sessions = sum(1 for session in active_sessions.values()
                              if hasattr(session, 'is_waiting_for_user_input') and session.is_waiting_for_user_input())
    except Exception as e:
        logger.warning(f"健康检查时出错: {e}")
        running_sessions = 0
        waiting_sessions = 0

    return {
        "status": "healthy",
        "service": "文献调研顺序执行服务",
        "active_sessions": len(active_sessions),
        "running_sessions": running_sessions,
        "waiting_for_approval_sessions": waiting_sessions,
        "max_sessions": MAX_SESSIONS,
        "available_slots": MAX_SESSIONS - len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/sessions")
async def list_sessions():
    """列出活跃会话"""
    sessions_info = []
    for session_id, session in active_sessions.items():
        try:
            waiting_for_approval = (hasattr(session, 'is_waiting_for_user_input') and
                                  session.is_waiting_for_user_input())

            # 获取工作流进度
            progress = {}
            if hasattr(session, 'get_workflow_progress'):
                try:
                    progress = session.get_workflow_progress()
                except:
                    progress = {"error": "无法获取进度"}

            sessions_info.append({
                "session_id": session_id,
                "workflow_name": session.get_workflow_name() if hasattr(session, 'get_workflow_name') else "未知",
                "is_running": session.is_running if hasattr(session, 'is_running') else False,
                "waiting_for_approval": waiting_for_approval,
                "workflow_completed": getattr(session, 'workflow_completed', False),
                "progress": progress
            })
        except Exception as e:
            logger.warning(f"获取会话 {session_id} 信息时出错: {e}")

    return {
        "active_sessions": len(sessions_info),
        "sessions": sessions_info,
        "service_description": "文献调研顺序执行服务 - SurveyDirector → PaperRetriever → PaperSummarizer → SurveyAnalyst"
    }


@app.post("/cleanup")
async def manual_cleanup():
    """手动清理空闲会话"""
    await cleanup_idle_sessions()

    return {
        "message": "清理完成",
        "remaining_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动文献调研顺序执行API服务器...")
    print("=" * 80)
    print("🔬 **专注服务**: 文献调研智能助手")
    print("📋 **执行模式**: 顺序交互 - 一步一确认")
    print("🎯 **工作流程**: SurveyDirector → PaperRetriever → PaperSummarizer → SurveyAnalyst")
    print("-" * 80)
    print("🔗 WebSocket连接: ws://localhost:8000/ws/survey")
    print("📊 服务状态: http://localhost:8000/health")
    print("📋 会话管理: http://localhost:8000/sessions")
    print("=" * 80)
    print("💡 **交互指南**:")
    print("✅ 'APPROVE/确认' - 继续下一阶段")
    print("🔄 'REGENERATE/重新生成' - 重做当前阶段")
    print("📝 输入具体意见 - 指导优化当前阶段")
    print("🏁 'END' - 提前结束")
    print("❌ 'QUIT' - 退出会话")
    print("=" * 80)
    print("🌟 **核心优势**: 完全控制每个研究环节，确保调研质量！")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )