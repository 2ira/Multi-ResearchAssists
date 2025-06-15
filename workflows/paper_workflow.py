"""
论文写作工作流实现
"""

from base_workflow import BaseWorkflowSession
from agents.paper_writing.paper_writing_agents import (
    get_paper_director,
    get_writing_assistant,
    get_reference_manager,
    get_figure_generator,
    get_paper_polisher
)
from typing import List
import logging

logger = logging.getLogger(__name__)


class PaperWritingWorkflowSession(BaseWorkflowSession):
    """论文写作工作流会话"""

    async def get_agents(self) -> List:
        """获取论文写作工作流所需的智能体"""
        return [
            get_paper_director(),
            get_writing_assistant(),
            get_reference_manager(),
            get_figure_generator(),
            get_paper_polisher()
        ]

    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return "论文写作工作流"