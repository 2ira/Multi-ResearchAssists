from dataclasses import dataclass
from datetime import datetime

from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool
from autogen_core.tools import FunctionTool

from model_factory import create_model_client
import tempfile
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from autogen_agentchat.agents import AssistantAgent
default_model_client = create_model_client("default_model")


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('autogen_core.events').setLevel(logging.ERROR)

@dataclass
class ExperimentConfig:
    """Configuration for experiment execution"""
    work_dir: str
    max_iterations: int = 10
    timeout: int = 300
    use_docker: bool = False
    auto_approve: bool = False


## 这里有更加详细的代码执行配置，包括初始环境、以及初始化目录
class EnhancedCodeExecutor:
    """Enhanced code executor with better error handling and monitoring"""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.work_dir = Path(config.work_dir)
        self.work_dir.mkdir(exist_ok=True)

        # Create output directories
        (self.work_dir / "output").mkdir(exist_ok=True)
        (self.work_dir / "plots").mkdir(exist_ok=True)
        (self.work_dir / "reports").mkdir(exist_ok=True)

        self.executor = self._create_executor()

    def _create_executor(self):
        """Create code executor based on configuration"""
        if self.config.use_docker:
            try:
                return DockerCommandLineCodeExecutor(
                    work_dir=str(self.work_dir),
                    image="python:3.11-slim",
                    timeout=self.config.timeout,
                    auto_remove=True,
                    stop_container=True,
                    init_command="""
                    pip install numpy pandas matplotlib seaborn scikit-learn scipy statsmodels plotly jupyter
                    """.strip(),
                    extra_volumes={
                        str(self.work_dir / "output"): {"bind": "/output", "mode": "rw"},
                        str(self.work_dir / "plots"): {"bind": "/plots", "mode": "rw"},
                        str(self.work_dir / "reports"): {"bind": "/reports", "mode": "rw"}
                    }
                )
            except Exception as e:
                logger.warning(f"Docker setup failed, using local executor: {e}")
                self.config.use_docker = False

        return LocalCommandLineCodeExecutor(
            work_dir=str(self.work_dir),
            timeout=self.config.timeout,
            cleanup_temp_files=False  # Keep files for analysis
        )


class SmartCodeAssistant:
    """Enhanced code assistant with better prompting and error handling"""

    def __init__(self, executor: EnhancedCodeExecutor, model_client):
        self.executor = executor
        self.tool = PythonCodeExecutionTool(executor.executor)

        self.agent = AssistantAgent(
            name="CodeAssistant",
            model_client=model_client,
            system_message="""
            你是一位资深的Python开发工程师和数据科学家。你的职责包括：
            
            编程规范：
            1. 编写清洁、有文档、生产就绪的代码
            2. 包含全面的错误处理（try-except语句块）
            3. 添加日志语句来跟踪执行进度
            4. 为所有函数使用类型提示和文档字符串
            5. 遵循PEP 8编码风格指南
            
            代码执行规则：
            1. 绝对不要使用plt.show() - 始终将图表保存到./plots/目录
            2. 将所有数据输出保存到./output/目录，格式为CSV或JSON
            3. 在./reports/目录生成HTML或markdown格式的报告
            4. 文件操作使用绝对路径
            5. 为长时间运行的操作包含进度指示器
            
            数据科学最佳实践：
            1. 执行数据验证和质量检查
            2. 适当处理缺失值
            3. 使用合适的统计方法
            4. 包含置信区间和显著性检验
            5. 创建带有合适标签的信息性可视化
            
            错误处理：
            1. 预期常见错误（文件未找到、数据类型问题等）
            2. 提供信息丰富的错误消息
            3. 尽可能包含备选策略
            4. 记录所有错误及其上下文信息
            
            协作要求：
            1. 清楚地记录每个代码块的功能
            2. 解释所做的任何假设
            3. 突出需要审查的区域
            4. 建议改进或替代方法
            
            请用中文回复并生成中文注释的代码。
            """.strip(),
            tools=[self.tool],
            reflect_on_tool_use=True,
            model_client_stream=False,
        )