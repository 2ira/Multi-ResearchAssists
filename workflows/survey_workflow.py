"""
文献调研工作流实现 - 重构版本
"""

from base_workflow import BaseWorkflowSession
from agents.article_research.survey_director import get_survey_director
from agents.article_research.paper_retriver import get_paper_retriever
from agents.article_research.paper_summarizer import get_paper_summarizer
from agents.article_research.survey_analyst import get_survey_analyst
from typing import List
import logging

logger = logging.getLogger(__name__)


class SurveyWorkflowSession(BaseWorkflowSession):
    """文献调研工作流会话"""

    async def get_agents(self) -> List:
        """获取文献调研工作流所需的智能体"""
        return [
            get_survey_director(),
            get_paper_retriever(),
            get_paper_summarizer(),
            get_survey_analyst()
        ]

    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return "文献调研工作流"