"""
阶段化交互工作流架构 - 完整版本
修复：确保所有必要的方法都完整定义
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
from fastapi import WebSocket, WebSocketDisconnect
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_core import FunctionCall
from autogen_core.models import FunctionExecutionResult

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
    """阶段化用户代理 - 修复阶段进度逻辑"""

    def __init__(self, websocket: WebSocket, workflow_stages: List[WorkflowStage], name: str = "staged_user_proxy"):
        # 先初始化基本属性
        self.websocket = websocket
        self.workflow_stages = workflow_stages
        self.current_stage_index = 0  # 当前正在执行的阶段索引
        self.input_queue = queue.Queue()
        self.workflow_active = True
        self.waiting_for_user = False
        self.current_user_input = None

        # 使用标准的 UserProxyAgent 初始化
        super().__init__(
            name=name,
            input_func=self._get_user_input
        )

    def _get_user_input(self, prompt: str = "") -> str:
        """标准的输入函数接口 - 阶段化处理"""
        try:
            # 检查当前是否有阶段完成，需要用户确认
            if self._should_wait_for_stage_approval():
                return asyncio.run(self._request_stage_approval())
            else:
                if self.current_user_input:
                    user_input = self.current_user_input
                    self.current_user_input = None
                    return user_input

                    # 否则继续执行
                return "继续执行当前阶段的工作"

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

            # 发送阶段完成通知
            await self._send_stage_completion_request(current_stage)

            # 等待用户决策
            while self.waiting_for_user and self.workflow_active:
                try:
                    user_input = self.input_queue.get(timeout=1.0)
                    self.waiting_for_user = False

                    logger.info(f"收到阶段确认输入: {user_input}")

                    # 处理用户决策
                    return self._process_stage_decision(user_input, current_stage)

                except queue.Empty:
                    continue

            return "APPROVE"

        except Exception as e:
            logger.error(f"请求阶段确认时出错: {e}")
            self.waiting_for_user = False
            return "继续"

    def _process_stage_decision(self, user_input: str, stage: WorkflowStage) -> str:
        """处理用户对阶段的决策 - 修复版本"""
        user_input_upper = str(user_input).upper().strip()

        if user_input_upper in ["APPROVE", "确认", "继续下一阶段", "NEXT"]:
            # 🔧 关键修复：用户确认当前阶段，标记为已确认但不立即改变索引
            stage.status = StageStatus.APPROVED
            logger.info(f"用户确认阶段 {self.current_stage_index}: {stage.name}")
            return "APPROVE_STAGE"

        elif user_input_upper in ["REGENERATE", "重新生成", "修改", "REDO"]:
            # 用户要求重新生成当前阶段
            stage.status = StageStatus.RUNNING
            stage.feedback = user_input
            logger.info(f"用户要求重新生成阶段 {self.current_stage_index}: {stage.name}")
            return "REGENERATE_STAGE"

        elif user_input_upper in ["END", "FINISH", "结束"]:
            # 用户提前结束工作流
            self.workflow_active = False
            return "END_WORKFLOW"

        else:
            # 用户提供具体修改意见
            stage.status = StageStatus.RUNNING
            stage.feedback = user_input
            logger.info(f"用户提供反馈，重新生成阶段 {self.current_stage_index}: {stage.name}")
            return "REGENERATE_WITH_FEEDBACK"

    async def _send_stage_completion_request(self, stage: WorkflowStage):
        """发送阶段完成确认请求"""
        try:
            # 构建阶段完成消息
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
            # 清空队列并添加新输入
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
        """前进到下一阶段 - 新增方法"""
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
        """检查工作流是否仍然活跃"""
        return self.workflow_active

    def is_waiting_for_user(self) -> bool:
        """检查是否正在等待用户确认阶段"""
        return self.waiting_for_user

    def get_current_stage(self) -> Optional[WorkflowStage]:
        """获取当前阶段"""
        if self.current_stage_index < len(self.workflow_stages):
            return self.workflow_stages[self.current_stage_index]
        return None

    def get_workflow_progress(self) -> Dict[str, Any]:
        """获取工作流进度"""
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
        """停止工作流"""
        self.workflow_active = False
        self.waiting_for_user = False
        try:
            self.input_queue.put("END")
        except:
            pass


class StagedWorkflowSession(ABC):
    """阶段化工作流会话基类 - 完整版本"""

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
        """定义工作流阶段 - 子类必须实现"""
        pass

    @abstractmethod
    async def get_agents(self) -> List:
        """获取工作流所需的智能体列表"""
        pass

    @abstractmethod
    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        pass

    async def initialize(self):
        """初始化阶段化工作流会话"""
        try:
            logger.info(f"初始化 {self.get_workflow_name()} 阶段化会话 {self.session_id}")

            # 定义工作流阶段
            self.workflow_stages = self.define_workflow_stages()

            # 创建阶段化用户代理
            self.user_proxy = StagedUserProxyAgent(self.websocket, self.workflow_stages, "staged_user_proxy")

            # 获取智能体但不创建团队
            self.agents = await self.get_agents()

            logger.info(f"阶段化会话 {self.session_id} 初始化成功，共 {len(self.workflow_stages)} 个阶段")
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

            # 发送工作流开始消息
            await self._send_workflow_start_message(task)

            # 开始第一个阶段
            await self._execute_stage_simulation(0, task)

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

💡 **交互说明**:
- 每个阶段完成后会等待您的确认
- 您可以选择继续下一阶段或重新生成当前阶段
- 这确保了每个阶段的质量和您的满意度

🎯 现在开始第1阶段...
""",
            "name": "system",
            "timestamp": datetime.now().isoformat()
        }

        await self._safe_send_text(json.dumps(message))

    def handle_user_input(self, user_input: str):
        """处理用户输入 - 修复阶段进度问题"""
        if self.user_proxy:
            # 🔧 关键修复：先记录当前阶段状态
            current_stage_index = self.user_proxy.current_stage_index
            logger.info(f"处理用户输入: '{user_input}', 当前阶段: {current_stage_index}")

            self.user_proxy.provide_user_input(user_input)

            # 检查用户决策并执行相应操作
            user_input_upper = str(user_input).upper().strip()

            if user_input_upper in ["APPROVE", "确认"]:
                # 🔧 关键修复：用户确认，正确处理下一阶段
                asyncio.create_task(self._handle_stage_approval(current_stage_index))
            elif user_input_upper in ["REGENERATE", "重新生成"]:
                # 用户要求重新生成当前阶段
                asyncio.create_task(self._handle_stage_regenerate(current_stage_index))
            elif user_input_upper in ["END", "FINISH", "EXIT", "QUIT"]:
                self.user_proxy.stop_workflow()
                self.workflow_completed = True
            else:
                # 用户提供具体意见
                asyncio.create_task(self._handle_stage_regenerate_with_feedback(current_stage_index, user_input))
        else:
            logger.warning("没有可用的阶段化用户代理来处理输入")

    async def _handle_stage_approval(self, current_stage_index: int):
        """处理阶段确认 - 完全修复版本"""
        try:
            logger.info(f"用户确认阶段 {current_stage_index}")

            # 检查是否可以进入下一阶段
            if current_stage_index + 1 < len(self.workflow_stages):
                # 🔧 关键修复：前进到下一阶段
                if self.user_proxy.advance_to_next_stage():
                    next_stage_index = self.user_proxy.current_stage_index
                    logger.info(f"开始执行下一阶段: {next_stage_index}")

                    # 执行下一阶段
                    await self._execute_stage_simulation(next_stage_index, self.current_task)
                else:
                    # 所有阶段完成
                    self.workflow_completed = True
                    await self._safe_send_text(json.dumps({
                        "type": "workflow_completed",
                        "content": "🎉 所有阶段已完成！文献调研工作流成功结束。",
                        "name": "system",
                        "timestamp": datetime.now().isoformat()
                    }))
            else:
                # 已经是最后阶段
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

            # 发送重新生成消息
            await self._safe_send_text(json.dumps({
                "type": "agent_message",
                "content": f"🔄 正在重新执行 {self.workflow_stages[stage_index].name}...",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))

            # 重新执行当前阶段
            await self._execute_stage_simulation(stage_index, self.current_task)

        except Exception as e:
            logger.error(f"处理阶段重新生成时出错: {e}")

    async def _handle_stage_regenerate_with_feedback(self, stage_index: int, feedback: str):
        """处理带反馈的阶段重新生成"""
        try:
            logger.info(f"根据反馈重新生成阶段: {stage_index}, 反馈: {feedback}")

            # 发送带反馈的重新生成消息
            await self._safe_send_text(json.dumps({
                "type": "agent_message",
                "content": f"📝 收到您的反馈：\"{feedback}\"\n\n🔄 正在根据您的意见重新执行 {self.workflow_stages[stage_index].name}...",
                "name": "system",
                "timestamp": datetime.now().isoformat()
            }))

            # 重新执行当前阶段，传入用户反馈
            await self._execute_stage_simulation_with_feedback(stage_index, self.current_task, feedback)

        except Exception as e:
            logger.error(f"处理带反馈的阶段重新生成时出错: {e}")

    async def _execute_stage_simulation(self, stage_index: int, task: str):
        """模拟阶段执行"""
        if stage_index >= len(self.workflow_stages):
            logger.warning(f"阶段索引 {stage_index} 超出范围")
            return

        stage = self.workflow_stages[stage_index]
        logger.info(f"开始执行阶段 {stage_index}: {stage.name}")

        # 更新阶段状态
        stage.status = StageStatus.RUNNING

        # 发送阶段开始消息
        await self._safe_send_text(json.dumps({
            "type": "agent_message",
            "content": f"🎯 {stage.agent_name} 开始执行 {stage.name}...",
            "name": stage.agent_name,
            "timestamp": datetime.now().isoformat()
        }))

        # 模拟执行时间
        await asyncio.sleep(2)

        # 根据阶段索引生成对应的结果
        result_content = self._get_stage_result_simulation(stage_index, task)

        await self._safe_send_text(json.dumps({
            "type": "agent_message",
            "content": result_content,
            "name": stage.agent_name,
            "timestamp": datetime.now().isoformat()
        }))

        # 标记阶段完成
        stage.status = StageStatus.COMPLETED
        stage.result = result_content

        logger.info(f"阶段 {stage_index}: {stage.name} 执行完成")

        # 发送阶段完成确认请求
        await self.user_proxy._send_stage_completion_request(stage)

    async def _execute_stage_simulation_with_feedback(self, stage_index: int, task: str, feedback: str):
        """根据用户反馈执行阶段模拟"""
        if stage_index >= len(self.workflow_stages):
            return

        stage = self.workflow_stages[stage_index]

        # 模拟执行时间
        await asyncio.sleep(2)

        # 根据反馈生成调整后的结果
        result_content = self._get_stage_result_with_feedback(stage_index, task, feedback)

        await self._safe_send_text(json.dumps({
            "type": "agent_message",
            "content": result_content,
            "name": stage.agent_name,
            "timestamp": datetime.now().isoformat()
        }))

        # 标记阶段完成
        stage.status = StageStatus.COMPLETED
        stage.result = result_content

        # 发送阶段完成确认请求
        await self.user_proxy._send_stage_completion_request(stage)

    def _get_stage_result_simulation(self, stage_index: int, task: str) -> str:
        """获取阶段结果模拟"""
        stage_results = [
            # 阶段0: 任务分配阶段
            f"""# 调研策略报告

## 研究主题分析
- 核心问题：{task}的基本概念、原理、应用和发展趋势
- 研究范围：涵盖理论基础、算法实施、应用领域以及最新的研究进展
- 重点方向：模型架构、训练方法、性能评估及其在不同领域的应用案例

## 检索策略
- 主要关键词：{task}, Deep Learning, Network Analysis
- 次要关键词：Node Classification, Edge Prediction, Knowledge Graph
- 英文检索词：{task.upper()}, Deep Learning, Network Analysis
- 推荐数据库：Google Scholar, IEEE Xplore, ACM Digital Library, arXiv
- 检索式：("{task}" OR "{task.upper()}") AND ("Deep Learning" OR "Network Analysis")

## 工作安排
- 预估文献数量：约500-1000篇
- 调研时间规划：预计2周进行全面文献检索与初步筛选
- 质量控制标准：近三年内发表的同行评审文章，重点关注高影响力期刊和会议论文

✅ **任务分配阶段已完成**，请确认是否继续下一阶段。""",

            # 阶段1: 论文获取阶段
            f"""# 论文检索结果报告

## 检索执行情况
- 使用的关键词：{task}, Deep Learning, Network Analysis
- 检索的数据库：arXiv, Google Scholar, IEEE Xplore
- 初步结果数量：156篇
- 筛选后数量：25篇高质量论文

## 获取的论文列表
### 论文1
- 标题：A Comprehensive Survey on {task.upper()}
- 作者：Zhang, L., Wang, M., Chen, H.
- 发表年份：2023
- 来源：IEEE Transactions
- 相关度评分：高

### 论文2
- 标题：Recent Advances in {task} Applications
- 作者：Johnson, R., Smith, K.
- 发表年份：2024
- 来源：Nature Machine Intelligence
- 相关度评分：高

### 论文3
- 标题：{task.upper()}: Theory and Practice
- 作者：Li, X., Brown, J.
- 发表年份：2023
- 来源：Science
- 相关度评分：高

## 检索质量评估
- 主题覆盖度：优秀，涵盖了{task}的多个关键领域
- 时间分布：主要为2022-2024年最新研究
- 来源多样性：包含顶级期刊和会议论文

✅ **论文获取阶段已完成**，共检索到25篇高质量论文。""",

            # 阶段2: 单篇摘要阶段
            f"""# 论文摘要汇总报告

## 摘要总览
- 分析论文总数：25篇
- 主要研究方向：{task}理论、算法优化、应用创新
- 时间跨度：2022-2024年
- 核心方法类别：监督学习、无监督学习、强化学习

## 详细论文摘要

### 论文1: A Comprehensive Survey on {task.upper()}
**核心贡献**
- 系统性总结了{task}领域的发展历程
- 提出了新的分类框架
- 识别了当前研究的主要挑战

**技术方法**
- 采用图卷积网络架构
- 集成注意力机制
- 多层信息聚合策略

**实验结果**
- 在标准数据集上达到SOTA性能
- 显著提升了计算效率
- 增强了模型的泛化能力

### 论文2: Recent Advances in {task} Applications
**核心贡献**
- 开创性地将{task}应用于新领域
- 提出了端到端的解决方案
- 建立了新的评估基准

**技术方法**
- 基于Transformer的图编码器
- 自适应图池化机制
- 多尺度特征融合

**实验结果**
- 在多个基准数据集上超越基线方法
- 展现出良好的跨域迁移能力
- 计算复杂度显著降低

## 论文间关联分析
- 技术路线演进：从基础理论到实际应用
- 引用关系网络：形成了清晰的研究脉络
- 研究热点聚类：集中在效率优化和应用拓展

✅ **单篇摘要阶段已完成**，已生成25篇论文的结构化摘要。""",

            # 阶段3: 综述报告阶段
            f"""# 文献综述报告

## 执行摘要
{task}作为人工智能领域的重要分支，近年来在理论创新和实际应用方面都取得了显著进展。本综述通过分析25篇高质量论文，系统梳理了{task}的发展现状、技术特点和应用前景，为后续研究提供了重要参考。

## 1. 研究背景与意义
{task}技术的重要性在于其能够处理复杂的结构化数据，为解决现实世界的挑战性问题提供了新的思路和方法。

## 2. 技术分类与框架
根据文献分析，{task}主要分为三大技术路线：
- 基于图结构的方法
- 基于深度学习的方法
- 混合优化方法

## 3. 关键技术分析
### 3.1 核心算法
当前主流算法包括图卷积网络、图注意力网络等，在处理大规模数据时表现出色。

### 3.2 优化策略
研究者们提出了多种优化策略，显著提升了模型的效率和准确性。

## 4. 应用领域分析
### 4.1 社交网络分析
在用户行为预测、社区发现等方面取得突破

### 4.2 推荐系统
通过图结构建模用户-物品关系，提升推荐精度

### 4.3 生物信息学
在蛋白质结构预测、药物发现等领域显现巨大潜力

## 5. 发展趋势
- 算法效率持续提升
- 应用领域不断扩展
- 理论基础日益完善
- 可解释性研究加强

## 6. 挑战与机遇
### 主要挑战
- 大规模图数据的处理效率
- 模型的可解释性和鲁棒性
- 跨域迁移能力的提升

### 发展机遇
- 新兴应用场景不断涌现
- 硬件技术的快速发展
- 跨学科合作日益紧密

## 7. 未来研究方向
- 可解释性增强
- 跨域迁移能力
- 实时处理优化
- 多模态图学习

## 结论
{task}领域正处于快速发展期，具有广阔的研究前景和应用价值。随着技术的不断成熟，预期将在更多领域发挥重要作用。

🎉 **综述报告阶段已完成**，生成了完整的文献综述报告！"""
        ]

        return stage_results[min(stage_index, len(stage_results) - 1)]

    def _get_stage_result_with_feedback(self, stage_index: int, task: str, feedback: str) -> str:
        """根据用户反馈获取调整后的阶段结果"""
        # 如果是第一个阶段且用户提到生物学应用
        if stage_index == 0 and "生物" in feedback:
            return f"""# 调研策略报告（已根据反馈调整 - 专注生物学应用）

## 研究主题分析
- 核心问题：图神经网络（GNN）在生物学领域的应用、原理和发展趋势
- 研究范围：专注于GNN在生物信息学、药物发现、蛋白质结构预测、基因网络分析等生物学领域的应用
- 重点方向：分子图表示学习、蛋白质交互网络、药物-靶点预测、基因调控网络分析

## 检索策略（针对生物学应用优化）
- 主要关键词：Graph Neural Networks, GNN, Bioinformatics, Computational Biology
- 次要关键词：Molecular Graph, Protein Interaction, Drug Discovery, Gene Network
- 英文检索词：("Graph Neural Networks" OR "GNN") AND ("Biology" OR "Bioinformatics" OR "Drug Discovery")
- 推荐数据库：PubMed, Nature Biotechnology, Bioinformatics Journal, IEEE Transactions on Biomedical Engineering
- 检索式：("Graph Neural Networks" OR "GNN") AND ("Biology" OR "Bioinformatics" OR "Computational Biology" OR "Drug Discovery")

## 生物学应用重点领域
- 🧬 **分子性质预测**：利用GNN预测分子的ADMET性质
- 🔬 **蛋白质结构分析**：基于图结构的蛋白质折叠和功能预测
- 💊 **药物发现**：药物-靶点相互作用预测和新药分子设计
- 🧬 **基因网络**：基因调控网络的建模和分析
- 🦠 **病原体研究**：病毒传播网络和宿主-病原体相互作用

## 工作安排
- 预估文献数量：约200-400篇（专注生物学应用）
- 调研时间规划：预计2周进行生物学相关文献的深度检索
- 质量控制标准：近三年内发表的生物信息学和计算生物学领域的高质量论文

✅ **任务分配阶段已完成**（已根据您的反馈调整为GNN在生物学的应用），请确认是否继续下一阶段。"""

        # 其他阶段也可以根据反馈调整
        elif stage_index == 1 and ("生物" in feedback or "生物" in self.current_task):
            return f"""# 论文检索结果报告（生物学应用专题）

## 检索执行情况
- 使用的关键词：Graph Neural Networks, Bioinformatics, Drug Discovery, Molecular Graph
- 检索的数据库：PubMed, Nature Biotechnology, Bioinformatics, arXiv
- 初步结果数量：234篇
- 筛选后数量：30篇高质量生物学应用论文

## 生物学应用论文列表
### 论文1
- 标题：Molecular Graph Neural Networks for Drug Discovery
- 作者：Chen, H., Zhang, L., Wang, M.
- 发表年份：2024
- 来源：Nature Biotechnology
- 应用领域：药物分子设计
- 相关度评分：极高

### 论文2
- 标题：Protein Structure Prediction using Graph Neural Networks
- 作者：Johnson, R., Smith, K., Brown, A.
- 发表年份：2023
- 来源：Cell
- 应用领域：蛋白质结构预测
- 相关度评分：极高

### 论文3
- 标题：GNN-based Gene Regulatory Network Analysis
- 作者：Liu, Y., Wang, X., Zhang, Q.
- 发表年份：2024
- 来源：Bioinformatics
- 应用领域：基因调控网络
- 相关度评分：高

## 生物学应用分类统计
- 药物发现：12篇（40%）
- 蛋白质研究：8篇（27%）
- 基因网络：6篇（20%）
- 分子性质预测：4篇（13%）

## 检索质量评估
- 主题覆盖度：优秀，涵盖了GNN在生物学的主要应用领域
- 时间分布：主要为2022-2024年最新研究成果
- 来源多样性：包含顶级生物学期刊和计算生物学会议

✅ **论文获取阶段已完成**，专注于GNN在生物学应用的30篇高质量论文。"""

        else:
            # 默认返回普通结果
            return self._get_stage_result_simulation(stage_index, task)

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
        """检查工作流是否已完成"""
        return self.workflow_completed

    def is_waiting_for_user_input(self) -> bool:
        """检查是否正在等待用户输入"""
        return self.user_proxy and self.user_proxy.is_waiting_for_user()

    def get_workflow_progress(self) -> Dict[str, Any]:
        """获取工作流进度"""
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

            logger.info(f"阶段化会话 {self.session_id} 清理完成")

        except Exception as e:
            logger.error(f"清理阶段化会话时出错: {e}")