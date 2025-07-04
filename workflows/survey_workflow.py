"""
顺序交互文献调研工作流实现 - SurveyDirector → PaperRetriever → PaperSummarizer → SurveyAnalyst
修正版本：与新的base_workflow.py完全兼容
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
                stage_id="stage_3_paper_summarization",
                name="单篇摘要阶段",
                agent_name="PaperSummarizer",
                description="逐一分析检索到的论文，生成每篇论文的结构化摘要"
            ),
            WorkflowStage(
                stage_id="stage_4_survey_analysis",
                name="综述报告阶段",
                agent_name="SurveyAnalyst",
                description="整合所有论文摘要，生成完整的文献综述报告和研究建议"
            )
        ]

    async def get_agents(self) -> List:
        """获取文献调研工作流所需的智能体 - 按执行顺序排列"""
        try:
            from agents.article_research.survey_director import get_survey_director
            from agents.article_research.paper_retriver import get_paper_retriever
            from agents.article_research.paper_summarizer import get_paper_summarizer
            from agents.article_research.survey_analyst import get_survey_analyst

            return [
                get_survey_director(),     # 第1个：任务分配
                get_paper_retriever(),     # 第2个：论文获取
                get_paper_summarizer(),    # 第3个：单篇摘要
                get_survey_analyst()       # 第4个：综述报告
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
            "stage_1_task_assignment": """
当前阶段：任务分配阶段 (SurveyDirector)
工作内容：
- 分析您提供的研究主题
- 确定调研范围和重点方向  
- 制定文献检索策略
- 生成检索关键词和数据库选择
- 预估调研工作量和时间安排

等待您确认调研策略是否合适，或提供调整意见。
""",
            "stage_2_paper_retrieval": """
当前阶段：论文获取阶段 (PaperRetriever)  
工作内容：
- 使用制定的检索策略搜索论文
- 从多个学术数据库获取文献
- 筛选高质量和相关性强的论文
- 去除重复和低质量文献
- 整理论文基本信息和下载链接

等待您确认检索结果是否满足需求，或需要调整检索策略。
""",
            "stage_3_paper_summarization": """
当前阶段：单篇摘要阶段 (PaperSummarizer)
工作内容：
- 逐一分析每篇检索到的论文
- 提取论文的核心贡献和方法
- 生成结构化的论文摘要
- 识别论文间的关联关系
- 标记重要发现和创新点

等待您确认摘要质量是否达标，或需要调整摘要重点。
""",
            "stage_4_survey_analysis": """
当前阶段：综述报告阶段 (SurveyAnalyst)
工作内容：
- 整合所有论文摘要信息
- 分析研究领域的发展趋势
- 识别研究空白和机会点
- 生成完整的文献综述报告
- 提供未来研究方向建议

等待您对最终综述报告进行人工审核确认。
"""
        }

        return stage_contexts.get(current_stage.stage_id, "当前阶段信息不可用")