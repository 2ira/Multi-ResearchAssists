import asyncio
import tempfile
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_core import CancellationToken
from model_factory import create_model_client

from agents.code_generate.code_assistant import SmartCodeAssistant, EnhancedCodeExecutor, ExperimentConfig
from agents.code_generate.data_analyst import SmartDataAnalyst

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('autogen_core.events').setLevel(logging.ERROR)


@dataclass
class ExperimentResult:
    """Results from experiment execution"""
    success: bool
    outputs: List[str]
    artifacts: List[str]
    analysis: str
    errors: List[str]
    execution_time: float


default_model_client = create_model_client("default_model")


## use console pattern


class SimpleLogger:
    """简化的日志记录器"""

    @staticmethod
    def info(msg: str):
        print(f"✓ {msg}")

    @staticmethod
    def error(msg: str):
        print(f"✗ 错误: {msg}")

    @staticmethod
    def warning(msg: str):
        print(f"⚠ 警告: {msg}")


class ExperimentCoordinator:
    """协调多智能体实验工作流程"""

    def __init__(self, config: ExperimentConfig, model_client):
        self.config = config
        self.model_client = model_client
        self.logger = SimpleLogger()

        try:
            self.executor = EnhancedCodeExecutor(config)

            # 初始化智能体
            self.code_assistant = SmartCodeAssistant(self.executor, model_client)
            self.data_analyst = SmartDataAnalyst(Path(config.work_dir), model_client)

            # 创建用户代理
            self.user_proxy = UserProxyAgent(
                "UserProxy",
                input_func=input if not config.auto_approve else lambda _: "APPROVE"
            )

            # 设置终止条件 - 使用APPROVE确保可靠终止
            self.termination = TextMentionTermination("APPROVE")

            # 创建团队
            self.team = RoundRobinGroupChat(
                [self.code_assistant.agent, self.data_analyst.agent, self.user_proxy],
                termination_condition=self.termination,
                max_turns=config.max_iterations * 3  # 3个智能体 * 最大迭代次数
            )

        except Exception as e:
            logger.error(f"初始化ExperimentCoordinator时出错: {e}")
            raise

    async def run_experiment(self, task: str) -> ExperimentResult:
        """运行完整的实验工作流程"""
        start_time = datetime.now()
        outputs = []
        artifacts = []
        errors = []

        try:
            logger.info(f"开始实验: {task}")

            # Enhanced task prompt
            enhanced_task = f"""
            实验任务: {task}
            
            工作流程要求：
            1. 智能编程师: 生成并执行代码来解决任务
            2. 数据分析师: 分析结果并提供见解
            3. 两个智能体: 协作改进和完善解决方案
            
            成功标准：
            - 代码无错误执行
            - 结果正确保存到指定目录
            - 分析提供有意义的见解
            - 所有输出都有良好的文档
            
            交付物：
            - 带有适当错误处理的工作代码
            - 数据输出保存到 ./output/
            - 可视化保存到 ./plots/
            - 分析报告保存到 ./reports/
            
            请协作实现这些目标。当对结果满意时输入关键词。
            """.strip()

            results = []
            async for message in self.team.run_stream(task=enhanced_task):
                if hasattr(message, 'content'):
                    # 只显示关键信息
                    if message.source in ['CodeAssistant', 'DataAnalyst']:
                        content = str(message.content)
                        if len(content) > 200:
                            content = content[:200] + "..."
                        print(f"\n[{message.source}]: {content}")
                    results.append(str(message.content))

            # 收集生成的文件
            artifacts = self._collect_artifacts()
            execution_time = (datetime.now() - start_time).total_seconds()

            self.logger.info(f"实验完成，耗时 {execution_time:.1f} 秒")
            self.logger.info(f"生成了 {len(artifacts)} 个文件")

            return ExperimentResult(
                success=True,
                outputs=outputs,
                artifacts=artifacts,
                analysis="实验成功完成",
                errors=errors,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"实验失败: {e}")
            errors.append(str(e))

            execution_time = (datetime.now() - start_time).total_seconds()

            return ExperimentResult(
                success=False,
                outputs=outputs,
                artifacts=artifacts,
                analysis=f"实验失败: {str(e)}",
                errors=errors,
                execution_time=execution_time
            )

    def _collect_artifacts(self) -> List[str]:
        """Collect all generated artifacts"""
        artifacts = []

        for directory in ["output", "plots", "reports"]:
            dir_path = Path(self.config.work_dir) / directory
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        artifacts.append(str(file_path))

        return artifacts

    async def cleanup(self):
        """Cleanup resources"""
        await self.model_client.close()


# Main execution function
async def run_enhanced_experiment(task: str, **kwargs):
    """Run an enhanced multi-agent experiment"""

    current_dir = Path.cwd()
    work_dir = current_dir / "experiment_output"

    # Create configuration
    config = ExperimentConfig(
        work_dir=str(work_dir),
        max_iterations=kwargs.get('max_iterations', 5),
        timeout=kwargs.get('timeout', 300),
        use_docker=kwargs.get('use_docker', True),
        auto_approve=kwargs.get('auto_approve', False)
    )

    # Create model client
    model_client = create_model_client("default_model")

    # Initialize coordinator
    coordinator = ExperimentCoordinator(config, model_client)

    try:
        # Run experiment
        result = await coordinator.run_experiment(task)

        # Print results
        print(f"\n{'=' * 50}")
        print(f"实验结果")
        print(f"{'=' * 50}")
        print(f"成功: {result.success}")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"生成的文件数量: {len(result.artifacts)}")

        if result.artifacts:
            print(f"\n生成的文件:")
            for artifact in result.artifacts:
                print(f"  - {artifact}")

        if result.errors:
            print(f"\n错误:")
            for error in result.errors:
                print(f"  - {error}")

        print(f"\n工作目录: {config.work_dir}")

        return result

    finally:
        await coordinator.cleanup()


# Example usage
# 主函数
async def main():
    """主函数测试"""
    task = """
设计并实现一个实验来预测房屋面积和房价之间的线性关系。

具体要求：
1. 生成模拟的房屋数据（面积、房价、其他特征）
   - 至少1000个样本
   - 面积范围：50-300平方米
   - 合理的价格范围和噪声

2. 进行探索性数据分析（EDA）
   - 数据基本统计信息
   - 相关性分析
   - 数据分布可视化

3. 建立线性回归模型
   - 使用面积预测房价
   - 可以包含其他特征
   - 模型训练和验证

4. 评估模型性能
   - R²分数
   - RMSE指标
   - 残差分析

5. 创建可视化图表
   - 散点图显示面积与房价关系
   - 回归线拟合
   - 残差图
   - 特征重要性图

6. 生成分析报告
   - 模型性能总结
   - 关键发现
   - 改进建议

请确保所有代码可以完整运行，结果保存到相应的目录中。
    """

    try:
        result = await run_enhanced_experiment(
            task=task,
            max_iterations=15,
            use_docker=False,  # 如果有Docker可用则设置为True
            auto_approve=False  # 设置为True可自动执行
        )
        return result
    except Exception as e:
        print(f"运行实验时出错: {e}")
        return None


if __name__ == "__main__":
    print("启动AutoGen多智能体房价预测实验...")
    print("提示：在对话中输入 'APPROVE' 来结束实验")
    print("注意: 文件将保存到当前目录的 experiment_output 文件夹中")
    print("=" * 50)

    # 运行主函数
    asyncio.run(main())
