"""
实验执行器 - FastAPI适配版本
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
import json
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import os
from pathlib import Path
import logging

default_model_client = create_model_client("default_model")
logger = logging.getLogger(__name__)


async def setup_experiment_environment(
    experiment_name: str,
    requirements: Optional[str] = None
) -> Dict[str, Any]:
    """
    设置实验环境

    Args:
        experiment_name: 实验名称
        requirements: 需要安装的包列表（可选）

    Returns:
        环境设置结果
    """
    try:
        # 创建实验目录
        experiment_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        work_dir = f"experiments/{experiment_name}_{timestamp}_{experiment_id}"

        # 创建目录结构
        directories = [
            work_dir,
            f"{work_dir}/code",
            f"{work_dir}/data",
            f"{work_dir}/output",
            f"{work_dir}/plots",
            f"{work_dir}/reports",
            f"{work_dir}/models"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        # 处理依赖包
        if requirements:
            try:
                if requirements.startswith('[') or requirements.startswith('{'):
                    parsed_requirements = json.loads(requirements)
                else:
                    parsed_requirements = [req.strip() for req in requirements.split(',')]
            except json.JSONDecodeError:
                parsed_requirements = [req.strip() for req in requirements.split(',')]
        else:
            parsed_requirements = [
                "numpy>=1.24.0",
                "pandas>=2.0.0",
                "matplotlib>=3.7.0",
                "seaborn>=0.12.0",
                "scikit-learn>=1.3.0",
                "scipy>=1.10.0"
            ]

        # 创建requirements.txt
        requirements_file = os.path.join(work_dir, "requirements.txt")
        with open(requirements_file, 'w') as f:
            for package in parsed_requirements:
                f.write(f"{package}\n")

        # 创建实验配置文件
        config_file = os.path.join(work_dir, "experiment_config.json")
        config = {
            "experiment_id": experiment_id,
            "experiment_name": experiment_name,
            "created_at": datetime.now().isoformat(),
            "work_dir": work_dir,
            "requirements": parsed_requirements,
            "status": "initialized",
            "directories": directories
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        result = {
            "success": True,
            "experiment_id": experiment_id,
            "experiment_name": experiment_name,
            "work_dir": work_dir,
            "directories_created": directories,
            "requirements": parsed_requirements,
            "config_file": config_file,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"实验环境设置完成: {experiment_name} (ID: {experiment_id})")
        return result

    except Exception as e:
        logger.error(f"设置实验环境时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "experiment_name": experiment_name,
            "timestamp": datetime.now().isoformat()
        }


async def run_experiment_script(
    experiment_id: str,
    script_content: str,
    script_name: str = "main_experiment.py"
) -> Dict[str, Any]:
    """
    运行实验脚本

    Args:
        experiment_id: 实验ID
        script_content: 脚本内容
        script_name: 脚本文件名

    Returns:
        实验运行结果
    """
    try:
        # 查找实验目录
        experiments_dir = "experiments"
        experiment_dir = None

        if os.path.exists(experiments_dir):
            for dir_name in os.listdir(experiments_dir):
                if experiment_id in dir_name:
                    experiment_dir = os.path.join(experiments_dir, dir_name)
                    break

        if not experiment_dir:
            return {
                "success": False,
                "error": f"未找到实验目录 (ID: {experiment_id})",
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat()
            }

        # 保存脚本文件
        script_path = os.path.join(experiment_dir, "code", script_name)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 执行脚本
        from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

        executor = LocalCommandLineCodeExecutor(
            work_dir=experiment_dir,
            timeout=600  # 10分钟超时
        )

        result = executor.execute_code_blocks([("python", script_content)])

        # 收集生成的文件
        artifacts = []
        for subdir in ["output", "plots", "reports", "models"]:
            subdir_path = Path(experiment_dir) / subdir
            if subdir_path.exists():
                for file_path in subdir_path.rglob("*"):
                    if file_path.is_file():
                        artifacts.append(str(file_path.relative_to(experiment_dir)))

        # 更新实验状态
        config_file = os.path.join(experiment_dir, "experiment_config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            config["status"] = "completed" if result.exit_code == 0 else "failed"
            config["completed_at"] = datetime.now().isoformat()
            config["artifacts"] = artifacts

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        execution_result = {
            "success": result.exit_code == 0,
            "experiment_id": experiment_id,
            "script_name": script_name,
            "script_path": script_path,
            "exit_code": result.exit_code,
            "output": result.output,
            "work_dir": experiment_dir,
            "artifacts": artifacts,
            "artifact_count": len(artifacts),
            "timestamp": datetime.now().isoformat()
        }

        status = "成功" if result.exit_code == 0 else "失败"
        logger.info(f"实验脚本执行{status}: {experiment_id}, 生成 {len(artifacts)} 个文件")
        return execution_result

    except Exception as e:
        logger.error(f"运行实验脚本时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "experiment_id": experiment_id,
            "script_name": script_name,
            "timestamp": datetime.now().isoformat()
        }


async def monitor_experiment_progress(
    experiment_id: str,
    stage: str,
    progress_percentage: float,
    description: str = ""
) -> Dict[str, Any]:
    """
    监控实验进度

    Args:
        experiment_id: 实验ID
        stage: 当前阶段
        progress_percentage: 进度百分比 (0-100)
        description: 进度描述

    Returns:
        进度记录结果
    """
    try:
        # 限制进度值在0-100之间
        progress = max(0, min(100, progress_percentage))

        progress_record = {
            "experiment_id": experiment_id,
            "stage": stage,
            "progress": progress,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }

        # 创建进度日志目录
        log_dir = "experiments/logs"
        os.makedirs(log_dir, exist_ok=True)

        # 记录进度到日志文件
        log_file = os.path.join(log_dir, f"{experiment_id}_progress.jsonl")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(progress_record, ensure_ascii=False) + '\n')

        logger.info(f"实验 {experiment_id} 进度更新: {stage} - {progress}% - {description}")
        return progress_record

    except Exception as e:
        logger.error(f"监控实验进度时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "experiment_id": experiment_id,
            "timestamp": datetime.now().isoformat()
        }


async def collect_experiment_results(
    experiment_id: str
) -> Dict[str, Any]:
    """
    收集实验结果

    Args:
        experiment_id: 实验ID

    Returns:
        实验结果收集
    """
    try:
        # 查找实验目录
        experiments_dir = "experiments"
        experiment_dir = None

        if os.path.exists(experiments_dir):
            for dir_name in os.listdir(experiments_dir):
                if experiment_id in dir_name:
                    experiment_dir = os.path.join(experiments_dir, dir_name)
                    break

        if not experiment_dir:
            return {
                "success": False,
                "error": f"未找到实验目录 (ID: {experiment_id})",
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat()
            }

        # 读取实验配置
        config_file = os.path.join(experiment_dir, "experiment_config.json")
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # 收集各类文件
        results = {
            "experiment_id": experiment_id,
            "experiment_name": config.get("experiment_name", "unknown"),
            "work_dir": experiment_dir,
            "status": config.get("status", "unknown"),
            "files": {
                "code": [],
                "data": [],
                "output": [],
                "plots": [],
                "reports": [],
                "models": []
            },
            "summary": {
                "total_files": 0,
                "file_types": {},
                "largest_file": None,
                "latest_file": None
            }
        }

        # 扫描各个目录
        for category in results["files"].keys():
            category_path = Path(experiment_dir) / category
            if category_path.exists():
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        file_info = {
                            "name": file_path.name,
                            "path": str(file_path.relative_to(experiment_dir)),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                        results["files"][category].append(file_info)
                        results["summary"]["total_files"] += 1

        # 统计文件类型
        for category, files in results["files"].items():
            if files:
                results["summary"]["file_types"][category] = len(files)

        # 找到最大和最新的文件
        all_files = []
        for files in results["files"].values():
            all_files.extend(files)

        if all_files:
            largest = max(all_files, key=lambda x: x["size"])
            latest = max(all_files, key=lambda x: x["modified"])
            results["summary"]["largest_file"] = largest
            results["summary"]["latest_file"] = latest

        results["success"] = True
        results["timestamp"] = datetime.now().isoformat()

        logger.info(f"实验结果收集完成: {experiment_id}, 共 {results['summary']['total_files']} 个文件")
        return results

    except Exception as e:
        logger.error(f"收集实验结果时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "experiment_id": experiment_id,
            "timestamp": datetime.now().isoformat()
        }


def get_experiment_runner(model_client=default_model_client):
    """实验执行器智能体"""

    setup_tool = FunctionTool(
        func=setup_experiment_environment,
        description="设置实验环境和目录结构",
        strict=False
    )

    run_tool = FunctionTool(
        func=run_experiment_script,
        description="运行实验脚本",
        strict=False
    )

    monitor_tool = FunctionTool(
        func=monitor_experiment_progress,
        description="监控实验进度",
        strict=False
    )

    collect_tool = FunctionTool(
        func=collect_experiment_results,
        description="收集实验结果",
        strict=False
    )

    experiment_runner = AssistantAgent(
        name="ExperimentRunner",
        model_client=model_client,
        tools=[setup_tool, run_tool, monitor_tool, collect_tool],
        system_message="""
        您是专业的实验执行专家，负责管理和运行科学实验。您的职责包括：

        ## 核心职责
        1. 设计和执行完整的实验工作流程
        2. 管理实验环境和资源配置
        3. 监控实验进度和资源使用情况
        4. 处理实验中的异常和错误
        5. 整理和归档实验结果

        ## 实验管理标准
        **实验环境管理:**
        - 创建独立的实验目录结构
        - 配置必要的依赖包和工具
        - 确保实验环境的隔离性
        - 维护清晰的文件组织结构

        **实验执行监控:**
        - 实时跟踪实验执行状态
        - 记录关键阶段的进度信息
        - 监控资源使用情况
        - 及时发现和报告异常

        **结果管理:**
        - 自动保存实验数据和模型
        - 生成结构化的结果报告
        - 备份重要的实验文件
        - 标记实验版本和配置信息

        **质量控制:**
        - 验证实验结果的合理性
        - 检查数据完整性和一致性
        - 识别异常值和潜在问题
        - 提供实验改进建议

        ## 实验工作流程
        **阶段1: 环境准备**
        - 创建实验目录和子目录
        - 安装和配置必要的依赖包
        - 设置实验参数和配置文件
        - 验证环境配置的正确性

        **阶段2: 实验执行**
        - 运行实验脚本和代码
        - 监控执行进度和状态
        - 处理运行时错误和异常
        - 记录中间结果和日志

        **阶段3: 结果收集**
        - 收集所有实验输出文件
        - 整理数据、图表和报告
        - 验证结果的完整性
        - 生成实验摘要信息

        **阶段4: 质量评估**
        - 检查实验结果的合理性
        - 对比预期结果和实际结果
        - 识别潜在的问题和改进点
        - 为后续分析提供建议

        ## 工具调用规则
        1. **设置环境时**: 调用 setup_experiment_environment
        2. **运行实验时**: 调用 run_experiment_script
        3. **监控进度时**: 调用 monitor_experiment_progress
        4. **收集结果时**: 调用 collect_experiment_results

        ## 协作要求
        - 与CodeDirector协调实验计划和执行策略
        - 接收CodingAssistant提供的可执行代码
        - 为DataAnalyst提供完整的实验数据
        - 响应人工用户的实验参数调整需求
        - 在实验完成时明确说明"实验执行完成"

        ## 错误处理策略
        - 预先检查实验环境和依赖
        - 为常见错误提供自动重试机制
        - 详细记录错误信息和上下文
        - 提供清晰的错误解决建议
        - 在必要时请求人工干预

        ## 性能优化
        - 合理分配计算资源
        - 优化大数据集的处理流程
        - 实现增量式的结果保存
        - 提供实验进度的可视化反馈

        请确保实验的科学性、可重现性和结果的可靠性。在实验过程中，要保持与团队的密切沟通，及时汇报重要进展和遇到的问题。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return experiment_runner