"""
优化版顺序交互文献调研工作流实现 - 高质量prompt版本
Enhanced SurveyDirector → PaperRetriever → PaperAnalyzer → ReportGenerator
与base_workflow.py完全兼容，专注于高质量学术综述生成
"""
from base_workflow import StagedWorkflowSession, WorkflowStage
from typing import List
import logging

logger = logging.getLogger(__name__)

class SurveyWorkflowSession(StagedWorkflowSession):
    """顺序交互文献调研工作流会话 - 完全兼容版本"""

    def define_workflow_stages(self) -> List[WorkflowStage]:
        """定义文献调研工作流的顺序执行阶段"""
        return [
            WorkflowStage(
                stage_id="stage_1_task_assignment",
                name="任务分配阶段",
                agent_name="SurveyDirector",
                description="分析研究主题，制定调研策略，分配具体任务和确定检索关键词"
            ),
            WorkflowStage(
                stage_id="stage_2_paper_retrieval",
                name="论文获取阶段",
                agent_name="PaperRetriever",
                description="根据调研策略检索相关学术论文，获取高质量文献资源"
            ),
            WorkflowStage(
                stage_id="stage_3_paper_analyst",
                name="单篇摘要阶段",
                agent_name="PaperAnalyzer",
                description="逐一分析检索到的论文，每篇论文400-500字分析"
            ),
            WorkflowStage(
                stage_id="stage_4_report_generation",
                name="综述报告阶段",
                agent_name="ReportGenerator",
                description="整合所有论文摘要，生成8000-10000词综述，生成完整的文献综述报告"
            )
        ]

    async def get_agents(self) -> List:
        """获取文献调研工作流所需的智能体 - 按执行顺序排列"""
        try:
            from agents.article_research.survey_director import get_survey_director
            from agents.article_research.paper_retriever import get_paper_retriever
            from agents.article_research.paper_analyzer import get_paper_analyzer
            from agents.article_research.report_generator import get_report_generator

            return [
                get_survey_director(),     # 第1个：论文关键词定位
                get_paper_retriever(),     # 第2个：论文批量检索
                get_paper_analyzer(),      # 第3个：论文分析
                get_report_generator()     # 第4个：生成综述
            ]
        except Exception as e:
            logger.warning(f"无法加载智能体: {e}, 使用模拟模式")
            return []  # 返回空列表，使用模拟执行

    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return "顺序交互文献调研工作流"

    def get_current_stage_context(self) -> str:
        """获取当前阶段的上下文信息"""
        if not self.user_proxy:
            return ""

        current_stage = self.user_proxy.get_current_stage()
        if not current_stage:
            return ""

        stage_contexts = {
            "stage_1_strategy_design": """
            📋 **当前阶段**: 策略制定 (SurveyDirector)

            **核心任务**:
            ✅ 分析您的研究主题
            ✅ 提取核心英文关键词
            ✅ 设计8个不同的检索查询
            ✅ 设定论文筛选标准

            **预期输出**:
            - 结构化的调研策略报告
            - 8个具体的英文检索查询  
            - 明确的质量标准
            - 给PaperRetriever的执行指令

            **您的参与**: 确认策略是否合适，提供调整建议
            """,
            "stage_2_paper_collection": """
            🔍 **当前阶段**: 论文检索 (PaperRetriever)

            **核心任务**:
            ✅ 执行8个检索查询
            ✅ 使用多个数据源检索
            ✅ 筛选30篇以上高质量论文
            ✅ 按主题分为3个批次

            **预期输出**:
            - 完整的论文清单（30+篇）
            - 每篇论文的详细信息
            - 按主题分类的批次
            - 检索统计报告

            **您的参与**: 检查论文相关性和质量
            """,
            "stage_3_content_analysis": """
            🔬 **当前阶段**: 深度分析 (PaperAnalyzer)

            **核心任务**:
            ✅ 逐篇论文深度分析（400-500字/篇）
            ✅ 提取技术方法和关键结果
            ✅ 学术价值评分（1-10分）
            ✅ 生成适合综述的引用要点

            **预期输出**:
            - 每篇论文的结构化分析
            - 批次综合分析报告
            - 技术趋势和发展脉络
            - 为综述写作准备的素材

            **您的参与**: 审核分析质量和深度
            """,
            "stage_4_survey_writing": """
            📝 **当前阶段**: 综述生成 (ReportGenerator)

            **核心任务**:
            ✅ 整合所有分析结果
            ✅ 生成8000-10000词综述
            ✅ 专业HTML格式设计
            ✅ 包含9个主要章节

            **预期输出**:
            - 完整的学术综述报告
            - 专业的HTML格式
            - 目录导航和引用系统
            - 可直接用于研究的内容

            **您的参与**: 最终质量确认
            """
        }

        return stage_contexts.get(current_stage.stage_id, "当前阶段信息不可用")