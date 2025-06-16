"""
稳定版基础工作流架构 - 修复完成流程显示
"""

import asyncio
import json
import logging
import threading
import queue
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import uuid
from abc import ABC, abstractmethod

from fastapi import WebSocket, WebSocketDisconnect
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import FunctionCall
from autogen_core.models import FunctionExecutionResult

logger = logging.getLogger(__name__)


class InteractiveUserProxyAgent(UserProxyAgent):
    """交互式用户代理 - 兼容版本"""

    def __init__(self, websocket: WebSocket, name: str = "user_proxy"):
        self.websocket = websocket
        self.input_queue = queue.Queue()
        self.workflow_active = True
        self.message_count = 0
        self.last_interaction_count = 0

        # 使用标准的input_func初始化
        super().__init__(name, input_func=self._get_user_input)

    def _get_user_input(self, prompt: str = "") -> str:
        """标准的输入函数接口"""
        try:
            self.message_count += 1

            # 决定是否需要用户交互
            if self._should_request_interaction():
                return asyncio.run(self._request_user_input_async(prompt))
            else:
                # 自动继续
                return "继续执行下一步"

        except Exception as e:
            logger.error(f"获取用户输入时出错: {e}")
            return "继续"

    def _should_request_interaction(self) -> bool:
        """判断是否需要用户交互"""
        # 每隔3-4条消息请求一次交互
        if self.message_count - self.last_interaction_count >= 3:
            self.last_interaction_count = self.message_count
            return True
        return False

    async def _request_user_input_async(self, context: str) -> str:
        """异步请求用户输入"""
        try:
            # 发送交互请求
            await self._send_interaction_request(context)

            # 等待用户输入
            try:
                user_input = self.input_queue.get(timeout=300)  # 5分钟超时
                logger.info(f"收到用户输入: {user_input}")

                # 检查终止条件
                if str(user_input).upper().strip() in ["APPROVE", "END", "FINISH", "EXIT"]:
                    self.workflow_active = False
                    return "用户已批准，工作流结束。APPROVE"  # 明确的终止信号

                return str(user_input)

            except queue.Empty:
                logger.warning("用户输入超时，继续工作流")
                return "请继续"

        except Exception as e:
            logger.error(f"请求用户输入时出错: {e}")
            return "继续"

    async def _send_interaction_request(self, context: str):
        """发送交互请求"""
        try:
            # 创建新的事件循环（如果当前线程没有）
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            message = {
                "type": "user_input_requested",
                "content": f"""
🎯 **工作流进展**: 
{context[:200] if context else '工作流正在进行中...'}

💭 **请选择您的操作**:
• 输入具体指导意见 (如: "请重点关注最新研究", "分析得很好")
• 输入 **"继续"** 让系统继续自动执行
• 输入 **"APPROVE"** 完成并结束工作流

⌨️ 请输入您的回复:""",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }

            await self.websocket.send_text(json.dumps(message))
            logger.info("交互请求发送成功")

        except Exception as e:
            logger.error(f"发送交互请求时出错: {e}")

    def provide_user_input(self, user_input: str):
        """接收外部用户输入"""
        try:
            # 清空队列并添加新输入
            while not self.input_queue.empty():
                try:
                    self.input_queue.get_nowait()
                except queue.Empty:
                    break

            self.input_queue.put(user_input, timeout=1)
            logger.info(f"用户输入已处理: {user_input}")

        except Exception as e:
            logger.error(f"处理用户输入时出错: {e}")

    def is_workflow_active(self) -> bool:
        """检查工作流是否仍然活跃"""
        return self.workflow_active

    def stop_workflow(self):
        """停止工作流"""
        self.workflow_active = False
        try:
            self.input_queue.put("APPROVE")
        except:
            pass


class BaseWorkflowSession(ABC):
    """基础工作流会话 - 修复完成流程显示"""

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.model_client = None
        self.team = None
        self.user_proxy = None
        self.is_running = False
        self.workflow_thread = None
        self.termination_condition = None
        self.workflow_completed = False  # 添加完成标志

    @abstractmethod
    async def get_agents(self) -> List:
        """获取工作流所需的智能体列表"""
        pass

    @abstractmethod
    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        pass

    async def initialize(self):
        """初始化工作流会话"""
        try:
            logger.info(f"初始化 {self.get_workflow_name()} 会话 {self.session_id}")

            from model_factory import create_model_client
            self.model_client = create_model_client("default_model")

            # 创建交互式用户代理
            self.user_proxy = InteractiveUserProxyAgent(self.websocket, "user_proxy")

            # 获取工作流特定的智能体
            agents = await self.get_agents()

            # 使用标准的 TextMentionTermination
            self.termination_condition = TextMentionTermination("APPROVE")

            # 创建团队 - 包含用户代理
            all_agents = agents + [self.user_proxy]
            self.team = RoundRobinGroupChat(
                all_agents,
                termination_condition=self.termination_condition,
                max_turns=30  # 限制最大轮次
            )

            logger.info(f"会话 {self.session_id} 初始化成功")
            return True

        except Exception as e:
            logger.error(f"初始化会话 {self.session_id} 时出错: {e}")
            return False

    async def start_workflow(self, task: str):
        """启动工作流"""
        if self.is_running:
            logger.warning(f"会话 {self.session_id} 已在运行中")
            return False

        try:
            self.is_running = True

            # 发送开始通知
            await self._safe_send_text(json.dumps({
                "type": "workflow_started",
                "content": f"🚀 开始{self.get_workflow_name()}: {task}",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))

            # 在单独线程中运行工作流
            self.workflow_thread = threading.Thread(
                target=self._run_workflow_sync,
                args=(task,),
                daemon=True
            )
            self.workflow_thread.start()

            logger.info(f"{self.get_workflow_name()} 启动成功，会话 {self.session_id}")
            return True

        except Exception as e:
            logger.error(f"启动工作流失败: {e}")
            self.is_running = False
            await self._send_error_message(f"启动{self.get_workflow_name()}失败: {str(e)}")
            return False

    def _run_workflow_sync(self, task: str):
        """同步运行工作流"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info(f"开始执行 {self.get_workflow_name()}，任务: {task}")

            async def run_workflow():
                # 清洁的任务描述
                clean_task = f"研究主题: {task}\n\n请开始相关工作，在重要步骤完成后等待进一步指示。"

                stream = self.team.run_stream(task=clean_task)

                async for message in stream:
                    await self._forward_message(message)

                    # 检查用户代理是否还活跃
                    if not self.user_proxy.is_workflow_active():
                        logger.info("用户代理停止，结束工作流")
                        break

                    # 检查消息内容是否包含完成信号
                    content = str(getattr(message, 'content', ''))
                    if any(term in content for term in ["APPROVE", "用户已批准"]):
                        logger.info("检测到完成信号，准备结束工作流")
                        self.workflow_completed = True
                        break

                # 发送完成消息
                await self._send_completion_message()

            loop.run_until_complete(run_workflow())

            logger.info(f"{self.get_workflow_name()} 执行完成，会话 {self.session_id}")

        except Exception as e:
            logger.exception(f"{self.get_workflow_name()} 执行出错: {e}")
            try:
                loop.run_until_complete(
                    self._send_error_message(f"{self.get_workflow_name()}执行出错: {str(e)}")
                )
            except:
                pass
        finally:
            self.is_running = False
            # 清理异步任务
            self._cleanup_async_tasks(loop)

    def _cleanup_async_tasks(self, loop):
        """清理异步任务"""
        try:
            # 获取所有待处理的任务
            pending_tasks = []
            for task in asyncio.all_tasks(loop):
                if not task.done():
                    pending_tasks.append(task)
                    task.cancel()

            # 等待所有任务完成或取消
            if pending_tasks:
                logger.info(f"正在清理 {len(pending_tasks)} 个待处理任务")
                try:
                    loop.run_until_complete(
                        asyncio.gather(*pending_tasks, return_exceptions=True)
                    )
                except Exception as e:
                    logger.error(f"清理任务时出错: {e}")

        except Exception as e:
            logger.error(f"清理异步任务时出错: {e}")
        finally:
            try:
                loop.close()
            except Exception as e:
                logger.error(f"关闭事件循环时出错: {e}")

    def _serialize_function_call(self, func_obj):
        """序列化函数调用对象"""
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
        """转发消息到客户端"""
        try:
            if hasattr(message, 'content'):
                if isinstance(message.content, (FunctionCall, FunctionExecutionResult)):
                    content = self._serialize_function_call(message.content)
                else:
                    content = getattr(message, 'content', str(message))
            else:
                content = str(message)

            name = getattr(message, 'source', 'system')
            msg_type = "agent_message"

            # 过滤掉空消息和系统调试信息
            if not content or str(content).strip() == "":
                return

            # 过滤掉包含敏感信息的消息
            content_str = str(content)
            if any(keyword in content_str.lower() for keyword in ["models_usage", "metadata", "datetime", "tzinfo"]):
                return

            # 过滤掉简单的"继续执行"消息
            if content_str.strip() in ["继续执行下一步", "继续", "请继续"]:
                return

            await self._safe_send_text(json.dumps({
                "type": msg_type,
                "content": content,
                "name": name,
                "timestamp": datetime.now().isoformat()
            }))

            logger.info(f"已转发来自 {name} 的消息")

        except WebSocketDisconnect:
            logger.warning("转发消息时连接已断开")
            self.is_running = False
        except Exception as e:
            logger.exception(f"转发消息时出错: {e}")

    async def _safe_send_text(self, message: str):
        """安全发送WebSocket消息"""
        try:
            # 检查WebSocket连接状态
            if hasattr(self.websocket, 'client_state'):
                from starlette.websockets import WebSocketState
                if self.websocket.client_state != WebSocketState.CONNECTED:
                    logger.warning("WebSocket连接已断开，跳过消息发送")
                    return False

            await self.websocket.send_text(message)
            return True

        except WebSocketDisconnect:
            logger.warning("WebSocket连接已断开")
            return False
        except RuntimeError as e:
            if "websocket.send" in str(e) and "websocket.close" in str(e):
                logger.warning("WebSocket已关闭，跳过消息发送")
                return False
            else:
                logger.error(f"发送消息时出现运行时错误: {e}")
                return False
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")
            return False

    async def _send_completion_message(self):
        """发送完成消息"""
        try:
            # 发送工作流完成消息
            await self._safe_send_text(json.dumps({
                "type": "workflow_completed",
                "content": f"✅ {self.get_workflow_name()}已完成！感谢您的参与。",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))

            # 标记为已完成
            self.workflow_completed = True

            logger.info(f"{self.get_workflow_name()} 完成消息已发送")

        except Exception as e:
            logger.error(f"发送完成消息时出错: {e}")

    async def _send_error_message(self, error_msg: str):
        """发送错误消息"""
        await self._safe_send_text(json.dumps({
            "type": "error",
            "content": error_msg,
            "name": "system",
            "timestamp": datetime.now().isoformat()
        }))

    def handle_user_input(self, user_input: str):
        """处理用户输入"""
        if self.user_proxy:
            self.user_proxy.provide_user_input(user_input)

            # 检查是否是终止指令
            if str(user_input).upper().strip() in ["APPROVE", "END", "FINISH", "EXIT", "QUIT"]:
                self.user_proxy.stop_workflow()
                self.workflow_completed = True  # 立即标记为完成
        else:
            logger.warning("没有可用的用户代理来处理输入")

    def is_workflow_completed(self) -> bool:
        """检查工作流是否已完成"""
        return self.workflow_completed

    async def cleanup(self):
        """清理会话"""
        try:
            logger.info(f"清理 {self.get_workflow_name()} 会话 {self.session_id}")
            self.is_running = False
            self.workflow_completed = True

            if self.user_proxy:
                self.user_proxy.stop_workflow()

            # 发送关闭消息
            try:
                await self._safe_send_text(json.dumps({
                    "type": "session_closing",
                    "content": "会话正在关闭",
                    "name": "system",
                    "timestamp": datetime.now().isoformat()
                }))
                await asyncio.sleep(0.2)
            except:
                pass

            # 等待工作流线程结束
            if self.workflow_thread and self.workflow_thread.is_alive():
                logger.info("等待工作流线程结束...")
                self.workflow_thread.join(timeout=5)
                if self.workflow_thread.is_alive():
                    logger.warning("工作流线程未能在5秒内结束")

            # 关闭模型客户端
            if self.model_client:
                try:
                    await self.model_client.close()
                except Exception as e:
                    logger.error(f"关闭模型客户端时出错: {e}")

            logger.info(f"会话 {self.session_id} 清理完成")

        except Exception as e:
            logger.error(f"清理时出错: {e}")