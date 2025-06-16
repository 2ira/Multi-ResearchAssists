"""
代码生成/实验工作流实现 - FastAPI适配版
"""

from base_workflow import BaseWorkflowSession
from agents.code_generate.code_director import get_code_director
from agents.code_generate.code_assistant import get_coding_assistant
from agents.code_generate.experiment_runner import get_experiment_runner
from agents.code_generate.data_analyst import get_data_analyst
from typing import List
import logging

logger = logging.getLogger(__name__)


class CodeGenerateWorkflowSession(BaseWorkflowSession):
    """代码生成/实验工作流会话"""

    async def get_agents(self) -> List:
        """获取代码生成/实验工作流所需的智能体"""
        return [
            get_code_director(),
            get_coding_assistant(),
            get_experiment_runner(),
            get_data_analyst()
        ]

    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return "代码生成/实验执行工作流"