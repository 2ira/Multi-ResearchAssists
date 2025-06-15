"""
方案设计工作流实现
"""

from base_workflow import BaseWorkflowSession
from agents.solution_design.solution_design_agents import (
    get_solution_director,
    get_solution_designer,
    get_design_reviewer,
    get_solution_refiner
)
from typing import List
import logging

logger = logging.getLogger(__name__)


class SolutionDesignWorkflowSession(BaseWorkflowSession):
    """方案设计工作流会话"""

    async def get_agents(self) -> List:
        """获取方案设计工作流所需的智能体"""
        return [
            get_solution_director(),
            get_solution_designer(),
            get_design_reviewer(),
            get_solution_refiner()
        ]

    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return "方案设计工作流"