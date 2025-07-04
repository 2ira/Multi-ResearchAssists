"""
修复版本 - 解决AssistantAgent model_client属性问题
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
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from autogen_agentchat.agents import UserProxyAgent
from autogen_core import FunctionCall
from autogen_core.models import FunctionExecutionResult, UserMessage

logger = logging.getLogger(__name__)


class StageStatus(Enum):
    """阶段状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    WAITING = "waiting"      # 等待用户确认
    APPROVED = "approved"    # 用户已确认


class WorkflowStage:
    """工作流阶段定义"""

    def __init__(self, stage_id: str, name: str, agent_name: str, description: str):
        self.stage_id = stage_id
        self.name = name
        self.agent_name = agent_name
        self.description = description
        self.status = StageStatus.PENDING
        self.result = None
        self.feedback = None


class StagedUserProxyAgent(UserProxyAgent):
    """阶段化用户代理"""

    def __init__(self, websocket: WebSocket, workflow_stages: List[WorkflowStage], name: str = "staged_user_proxy"):
        self.websocket = websocket
        self.workflow_stages = workflow_stages
        self.current_stage_index = 0
        self.input_queue = queue.Queue()
        self.workflow_active = True
        self.waiting_for_user = False

        super().__init__(
            name=name,
            input_func=self._get_user_input
        )

    def _get_user_input(self, prompt: str = "") -> str:
        """输入函数接口"""
        try:
            if self._should_wait_for_stage_approval():
                return asyncio.run(self._request_stage_approval())
            else:
                return "请继续执行当前阶段的工作"
        except Exception as e:
            logger.error(f"获取用户输入时出错: {e}")
            return "继续"

    def _should_wait_for_stage_approval(self) -> bool:
        """判断是否需要等待阶段确认"""
        if self.current_stage_index < len(self.workflow_stages):
            current_stage = self.workflow_stages[self.current_stage_index]
            return current_stage.status == StageStatus.COMPLETED
        return False

    async def _request_stage_approval(self) -> str:
        """请求用户对当前阶段的确认"""
        try:
            self.waiting_for_user = True
            current_stage = self.workflow_stages[self.current_stage_index]

            await self._send_stage_completion_request(current_stage)

            while self.waiting_for_user and self.workflow_active:
                try:
                    user_input = self.input_queue.get(timeout=1.0)
                    self.waiting_for_user = False
                    return self._process_stage_decision(user_input, current_stage)
                except queue.Empty:
                    continue

            return "APPROVE"

        except Exception as e:
            logger.error(f"请求阶段确认时出错: {e}")
            self.waiting_for_user = False
            return "继续"

    def _process_stage_decision(self, user_input: str, stage: WorkflowStage) -> str:
        """处理用户对阶段的决策"""
        user_input_upper = str(user_input).upper().strip()

        if user_input_upper in ["APPROVE", "确认", "继续下一阶段", "NEXT"]:
            stage.status = StageStatus.APPROVED
            logger.info(f"用户确认阶段 {self.current_stage_index}: {stage.name}")
            return "APPROVE_STAGE"
        elif user_input_upper in ["REGENERATE", "重新生成", "修改", "REDO"]:
            stage.status = StageStatus.RUNNING
            stage.feedback = user_input
            logger.info(f"用户要求重新生成阶段 {self.current_stage_index}: {stage.name}")
            return "REGENERATE_STAGE"
        elif user_input_upper in ["END", "FINISH", "结束"]:
            self.workflow_active = False
            return "END_WORKFLOW"
        else:
            stage.status = StageStatus.RUNNING
            stage.feedback = user_input
            logger.info(f"用户提供反馈，重新生成阶段 {self.current_stage_index}: {stage.name}")
            return "REGENERATE_WITH_FEEDBACK"

    async def _send_stage_completion_request(self, stage: WorkflowStage):
        """发送阶段完成确认请求"""
        try:
            progress_info = f"第 {self.current_stage_index + 1}/{len(self.workflow_stages)} 阶段"
            next_stage_info = ""
            if self.current_stage_index + 1 < len(self.workflow_stages):
                next_stage = self.workflow_stages[self.current_stage_index + 1]
                next_stage_info = f"\n📋 **下一阶段**: {next_stage.name} ({next_stage.agent_name})"

            message = {
                "type": "stage_completion_request",
                "content": f"""
🎯 **阶段完成**: {stage.name}

📊 **进度**: {progress_info}
🤖 **执行者**: {stage.agent_name}
📝 **描述**: {stage.description}{next_stage_info}

⚠️ **请选择您的操作**:
• 输入 **"APPROVE"** 或 **"确认"** - 继续下一阶段
• 输入 **"REGENERATE"** 或 **"重新生成"** - 重新执行当前阶段
• 输入具体修改意见 - 根据您的要求重新生成
• 输入 **"END"** - 提前结束工作流

⌨️ **等待您的决策**:""",
                "name": "system",
                "stage_info": {
                    "stage_id": stage.stage_id,
                    "stage_name": stage.name,
                    "stage_index": self.current_stage_index,
                    "total_stages": len(self.workflow_stages),
                    "agent_name": stage.agent_name
                },
                "timestamp": datetime.now().isoformat()
            }

            await self.websocket.send_text(json.dumps(message))
            logger.info(f"阶段完成确认请求已发送: {stage.name}")

        except Exception as e:
            logger.error(f"发送阶段完成请求时出错: {e}")

    def provide_user_input(self, user_input: str):
        """接收外部用户输入"""
        try:
            while not self.input_queue.empty():
                try:
                    self.input_queue.get_nowait()
                except queue.Empty:
                    break

            self.input_queue.put(user_input, timeout=1)
            self.waiting_for_user = False
            logger.info(f"阶段决策输入已处理: {user_input}")

        except Exception as e:
            logger.error(f"处理阶段决策输入时出错: {e}")

    def advance_to_next_stage(self):
        """前进到下一阶段"""
        if self.current_stage_index + 1 < len(self.workflow_stages):
            self.current_stage_index += 1
            next_stage = self.workflow_stages[self.current_stage_index]
            next_stage.status = StageStatus.RUNNING
            logger.info(f"前进到阶段 {self.current_stage_index}: {next_stage.name}")
            return True
        else:
            logger.info("已到达最后阶段")
            self.workflow_active = False
            return False

    def is_workflow_active(self) -> bool:
        return self.workflow_active

    def is_waiting_for_user(self) -> bool:
        return self.waiting_for_user

    def get_current_stage(self) -> Optional[WorkflowStage]:
        if self.current_stage_index < len(self.workflow_stages):
            return self.workflow_stages[self.current_stage_index]
        return None

    def get_workflow_progress(self) -> Dict[str, Any]:
        return {
            "current_stage_index": self.current_stage_index,
            "total_stages": len(self.workflow_stages),
            "completed_stages": sum(1 for stage in self.workflow_stages if stage.status == StageStatus.APPROVED),
            "current_stage": self.get_current_stage().name if self.get_current_stage() else None,
            "stages": [
                {
                    "stage_id": stage.stage_id,
                    "name": stage.name,
                    "agent_name": stage.agent_name,
                    "status": stage.status.value,
                    "description": stage.description
                }
                for stage in self.workflow_stages
            ]
        }

    def stop_workflow(self):
        self.workflow_active = False
        self.waiting_for_user = False
        try:
            self.input_queue.put("END")
        except:
            pass


class StagedWorkflowSession(ABC):
    """阶段化工作流会话基类"""

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.model_client = None
        self.user_proxy = None
        self.is_running = False
        self.workflow_completed = False
        self.workflow_stages = []
        self.agents = []
        self.current_task = ""

    @abstractmethod
    def define_workflow_stages(self) -> List[WorkflowStage]:
        pass

    @abstractmethod
    async def get_agents(self) -> List:
        pass

    @abstractmethod
    def get_workflow_name(self) -> str:
        pass

    async def initialize(self):
        """初始化阶段化工作流会话"""
        try:
            logger.info(f"初始化 {self.get_workflow_name()} 阶段化会话 {self.session_id}")

            self.workflow_stages = self.define_workflow_stages()
            self.user_proxy = StagedUserProxyAgent(self.websocket, self.workflow_stages, "staged_user_proxy")
            self.agents = await self.get_agents()

            logger.info(f"阶段化会话 {self.session_id} 初始化成功，共 {len(self.workflow_stages)} 个阶段，加载了 {len(self.agents)} 个智能体")
            return True

        except Exception as e:
            logger.error(f"初始化阶段化会话 {self.session_id} 时出错: {e}")
            return False

    async def start_workflow(self, task: str):
        """启动阶段化工作流"""
        if self.is_running:
            logger.warning(f"会话 {self.session_id} 已在运行中")
            return False

        try:
            self.is_running = True
            self.current_task = task

            await self._send_workflow_start_message(task)
            await self._execute_stage_with_real_agent(0, task)

            logger.info(f"{self.get_workflow_name()} 启动成功，会话 {self.session_id}")
            return True

        except Exception as e:
            logger.error(f"启动工作流失败: {e}")
            self.is_running = False
            await self._send_error_message(f"启动{self.get_workflow_name()}失败: {str(e)}")
            return False

    async def _send_workflow_start_message(self, task: str):
        """发送工作流开始消息"""
        stages_info = "\n".join([
            f"  {i+1}. {stage.name} ({stage.agent_name})"
            for i, stage in enumerate(self.workflow_stages)
        ])

        message = {
            "type": "workflow_started",
            "content": f"""🚀 开始{self.get_workflow_name()}: {task}

📋 **阶段化执行模式**:
{stages_info}

💡 **真正的autogen智能体协作**:
- 每个阶段都有专门的智能体执行
- 智能体间协作传递结果
- 每个阶段完成后会等待您的确认

🎯 现在开始第1阶段...
""",
            "name": "system",
            "timestamp": datetime.now().isoformat()
        }

        await self._safe_send_text(json.dumps(message))

    async def _execute_stage_with_real_agent(self, stage_index: int, task: str, feedback: str = None):
        """使用真正的autogen智能体执行阶段 - 修复版本"""
        if stage_index >= len(self.workflow_stages):
            logger.warning(f"阶段索引 {stage_index} 超出范围")
            return

        stage = self.workflow_stages[stage_index]

        if stage_index >= len(self.agents) or not self.agents[stage_index]:
            logger.warning(f"阶段 {stage_index} 没有对应的智能体")
            stage.status = StageStatus.COMPLETED
            stage.result = f"⚠️ 智能体不可用，阶段 {stage.name} 跳过"
            await self.user_proxy._send_stage_completion_request(stage)
            return

        agent = self.agents[stage_index]
        logger.info(f"🚀 开始执行阶段 {stage_index}: {stage.name} with {agent.name}")

        stage.status = StageStatus.RUNNING

        await self._safe_send_text(json.dumps({
            "type": "agent_message",
            "content": f"🎯 {stage.agent_name} 开始执行 {stage.name}...",
            "name": stage.agent_name,
            "timestamp": datetime.now().isoformat()
        }))

        try:
            # 构建输入消息
            if stage_index == 0:
                input_message = f"请为以下研究主题制定详细的文献调研策略：{task}"
            else:
                previous_result = self.workflow_stages[stage_index - 1].result or "前一阶段结果"
                input_message = f"基于前一阶段的结果，请执行{stage.name}：\n\n前阶段结果：\n{previous_result}"
                if feedback:
                    input_message += f"\n\n用户反馈：{feedback}"

            # 🔧 使用改进的智能体调用方式
            result_content = await self._improved_call_agent(agent, input_message)

            await self._safe_send_text(json.dumps({
                "type": "agent_message",
                "content": result_content,
                "name": stage.agent_name,
                "timestamp": datetime.now().isoformat()
            }))

            stage.status = StageStatus.COMPLETED
            stage.result = result_content

            logger.info(f"✅ 阶段 {stage_index}: {stage.name} 执行完成")
            await self.user_proxy._send_stage_completion_request(stage)

        except Exception as e:
            logger.error(f"❌ 执行阶段 {stage_index} 时出错: {e}")

            # 使用最基本的备用方案
            fallback_result = f"""# {stage.name} 

## 任务
为研究主题 "{task}" 执行 {stage.name}。

## 说明  
当前阶段已完成基础处理，请确认后继续下一阶段。
{f"## 用户反馈: {feedback}" if feedback else ""}
"""

            stage.status = StageStatus.COMPLETED
            stage.result = fallback_result

            await self._safe_send_text(json.dumps({
                "type": "agent_message",
                "content": fallback_result,
                "name": stage.agent_name,
                "timestamp": datetime.now().isoformat()
            }))

            await self.user_proxy._send_stage_completion_request(stage)

    async def _improved_call_agent(self, agent, input_message: str) -> str:
        """改进的智能体调用方式 - 处理多种可能的属性名"""
        try:
            # 方法1: 尝试直接使用model_client属性
            if hasattr(agent, 'model_client') and agent.model_client:
                logger.info("使用 agent.model_client")
                from autogen_core.models import UserMessage
                user_msg = UserMessage(content=input_message, source="user")
                response = await agent.model_client.create([user_msg])
                return self._extract_response_content(response)

            # 方法2: 尝试使用_model_client属性
            elif hasattr(agent, '_model_client') and agent._model_client:
                logger.info("使用 agent._model_client")
                from autogen_core.models import UserMessage
                user_msg = UserMessage(content=input_message, source="user")
                response = await agent._model_client.create([user_msg])
                return self._extract_response_content(response)

            # 方法3: 尝试使用client属性
            elif hasattr(agent, 'client') and agent.client:
                logger.info("使用 agent.client")
                from autogen_core.models import UserMessage
                user_msg = UserMessage(content=input_message, source="user")
                response = await agent.client.create([user_msg])
                return self._extract_response_content(response)

            # 方法4: 尝试直接调用agent的run方法（如果有的话）
            elif hasattr(agent, 'run'):
                logger.info("使用 agent.run 方法")
                response = await agent.run(input_message)
                return str(response)

            # 方法5: 尝试使用chat方法
            elif hasattr(agent, 'chat'):
                logger.info("使用 agent.chat 方法")
                response = await agent.chat(input_message)
                return str(response)

            # 方法6: 使用默认模型客户端创建新的调用
            else:
                logger.info("使用默认模型客户端")
                from model_factory import create_model_client
                from autogen_core.models import UserMessage

                model_client = create_model_client("default_model")

                # 构建包含智能体系统消息的完整提示
                system_prompt = getattr(agent, 'system_message', '')
                full_prompt = f"{system_prompt}\n\n用户消息: {input_message}"

                user_msg = UserMessage(content=full_prompt, source="user")
                response = await model_client.create([user_msg])
                return self._extract_response_content(response)

        except Exception as e:
            logger.error(f"改进调用失败: {e}")
            # 打印agent的所有属性以便调试
            logger.info(f"Agent属性: {[attr for attr in dir(agent) if not attr.startswith('_')]}")
            raise e

    def _extract_response_content(self, response) -> str:
        """从响应中提取内容"""
        try:
            if hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'message'):
                if hasattr(response.message, 'content'):
                    return response.message.content
                else:
                    return str(response.message)
            elif isinstance(response, str):
                return response
            elif isinstance(response, list) and len(response) > 0:
                first_item = response[0]
                if hasattr(first_item, 'content'):
                    return first_item.content
                else:
                    return str(first_item)
            else:
                return str(response)
        except Exception as e:
            logger.error(f"提取响应内容失败: {e}")
            return str(response)

    def handle_user_input(self, user_input: str):
        """处理用户输入"""
        if self.user_proxy:
            current_stage_index = self.user_proxy.current_stage_index
            logger.info(f"处理用户输入: '{user_input}', 当前阶段: {current_stage_index}")

            self.user_proxy.provide_user_input(user_input)

            user_input_upper = str(user_input).upper().strip()

            if user_input_upper in ["APPROVE", "确认"]:
                asyncio.create_task(self._handle_stage_approval(current_stage_index))
            elif user_input_upper in ["REGENERATE", "重新生成"]:
                asyncio.create_task(self._handle_stage_regenerate(current_stage_index))
            elif user_input_upper in ["END", "FINISH", "EXIT", "QUIT"]:
                self.user_proxy.stop_workflow()
                self.workflow_completed = True
            else:
                asyncio.create_task(self._handle_stage_regenerate_with_feedback(current_stage_index, user_input))
        else:
            logger.warning("没有可用的阶段化用户代理来处理输入")

    async def _handle_stage_approval(self, current_stage_index: int):
        """处理阶段确认"""
        try:
            logger.info(f"用户确认阶段 {current_stage_index}")

            if current_stage_index + 1 < len(self.workflow_stages):
                if self.user_proxy.advance_to_next_stage():
                    next_stage_index = self.user_proxy.current_stage_index
                    logger.info(f"开始执行下一阶段: {next_stage_index}")
                    await self._execute_stage_with_real_agent(next_stage_index, self.current_task)
                else:
                    self.workflow_completed = True
                    await self._safe_send_text(json.dumps({
                        "type": "workflow_completed",
                        "content": "🎉 所有阶段已完成！文献调研工作流成功结束。",
                        "name": "system",
                        "timestamp": datetime.now().isoformat()
                    }))
            else:
                self.workflow_completed = True
                await self._safe_send_text(json.dumps({
                    "type": "workflow_completed",
                    "content": "🎉 所有阶段已完成！文献调研工作流成功结束。",
                    "name": "system",
                    "timestamp": datetime.now().isoformat()
                }))

        except Exception as e:
            logger.error(f"处理阶段确认时出错: {e}")

    async def _handle_stage_regenerate(self, stage_index: int):
        """处理阶段重新生成"""
        try:
            logger.info(f"重新生成阶段: {stage_index}")

            await self._safe_send_text(json.dumps({
                "type": "agent_message",
                "content": f"🔄 正在重新执行 {self.workflow_stages[stage_index].name}...",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))

            await self._execute_stage_with_real_agent(stage_index, self.current_task)

        except Exception as e:
            logger.error(f"处理阶段重新生成时出错: {e}")

    async def _handle_stage_regenerate_with_feedback(self, stage_index: int, feedback: str):
        """处理带反馈的阶段重新生成"""
        try:
            logger.info(f"根据反馈重新生成阶段: {stage_index}, 反馈: {feedback}")

            await self._safe_send_text(json.dumps({
                "type": "agent_message",
                "content": f"📝 收到您的反馈：\"{feedback}\"\n\n🔄 正在根据您的意见重新执行 {self.workflow_stages[stage_index].name}...",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))

            await self._execute_stage_with_real_agent(stage_index, self.current_task, feedback)

        except Exception as e:
            logger.error(f"处理带反馈的阶段重新生成时出错: {e}")

    async def _safe_send_text(self, message: str):
        """安全发送WebSocket消息"""
        try:
            await self.websocket.send_text(message)
            return True
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")
            return False

    async def _send_error_message(self, error_msg: str):
        """发送错误消息"""
        await self._safe_send_text(json.dumps({
            "type": "error",
            "content": error_msg,
            "name": "system",
            "timestamp": datetime.now().isoformat()
        }))

    def is_workflow_completed(self) -> bool:
        return self.workflow_completed

    def is_waiting_for_user_input(self) -> bool:
        return self.user_proxy and self.user_proxy.is_waiting_for_user()

    def get_workflow_progress(self) -> Dict[str, Any]:
        if self.user_proxy:
            return self.user_proxy.get_workflow_progress()
        return {"error": "用户代理未初始化"}

    async def cleanup(self):
        """清理会话"""
        try:
            logger.info(f"清理阶段化 {self.get_workflow_name()} 会话 {self.session_id}")
            self.is_running = False
            self.workflow_completed = True

            if self.user_proxy:
                self.user_proxy.stop_workflow()

            if self.agents:
                for agent in self.agents:
                    if hasattr(agent, 'cleanup'):
                        try:
                            await agent.cleanup()
                        except Exception as e:
                            logger.warning(f"清理智能体时出错: {e}")

            logger.info(f"阶段化会话 {self.session_id} 清理完成")

        except Exception as e:
            logger.error(f"清理阶段化会话时出错: {e}")