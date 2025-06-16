"""
编程助手 - FastAPI适配版本
基于原有code_assistant.py，适配FastAPI架构
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
import json
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import tempfile
import os
from pathlib import Path
import logging

default_model_client = create_model_client("default_model")
logger = logging.getLogger(__name__)


async def execute_python_code(
    code: str,
    work_dir: Optional[str] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    执行Python代码

    Args:
        code: Python代码字符串
        work_dir: 工作目录，如果不提供则使用临时目录
        timeout: 执行超时时间（秒）

    Returns:
        代码执行结果
    """
    try:
        from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

        # 确定工作目录
        if not work_dir:
            work_dir = tempfile.mkdtemp()

        # 确保目录存在
        os.makedirs(work_dir, exist_ok=True)
        os.makedirs(f"{work_dir}/output", exist_ok=True)
        os.makedirs(f"{work_dir}/plots", exist_ok=True)
        os.makedirs(f"{work_dir}/reports", exist_ok=True)

        # 创建代码执行器
        executor = LocalCommandLineCodeExecutor(
            work_dir=work_dir,
            timeout=timeout
        )

        # 执行代码
        result = executor.execute_code_blocks([("python", code)])

        return {
            "success": result.exit_code == 0,
            "exit_code": result.exit_code,
            "output": result.output,
            "code": code,
            "work_dir": work_dir,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"代码执行失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "code": code,
            "work_dir": work_dir or "unknown",
            "timestamp": datetime.now().isoformat()
        }


async def generate_code_template(
    task_description: str,
    code_type: str = "script",
    language: str = "python"
) -> Dict[str, Any]:
    """
    生成代码模板

    Args:
        task_description: 任务描述
        code_type: 代码类型 (script, class, function, notebook)
        language: 编程语言

    Returns:
        生成的代码模板
    """
    try:
        templates = {
            "script": f'''#!/usr/bin/env python3
"""
{task_description}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 设置随机种子以保证结果可重现
np.random.seed(42)

# 配置matplotlib
plt.style.use('seaborn-v0_8')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def main():
    """
    主函数：{task_description}
    """
    print("开始执行任务: {task_description}")
    
    # TODO: 在此处实现具体的任务逻辑
    
    print("任务执行完成")

if __name__ == "__main__":
    main()
''',
            "class": f'''"""
{task_description} - 类实现

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TaskProcessor:
    """
    任务处理器类：{task_description}
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化任务处理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {{}}
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """
        初始化处理器
        
        Returns:
            是否初始化成功
        """
        try:
            # TODO: 添加初始化逻辑
            self.is_initialized = True
            logger.info("任务处理器初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化失败: {{e}}")
            return False
    
    def process(self, data: Any) -> Any:
        """
        处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        if not self.is_initialized:
            raise RuntimeError("处理器未初始化")
            
        try:
            # TODO: 添加处理逻辑
            result = data  # 占位符
            return result
        except Exception as e:
            logger.error(f"处理失败: {{e}}")
            raise
''',
            "function": f'''"""
{task_description} - 函数实现

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def process_task(
    input_data: Any,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    执行任务：{task_description}
    
    Args:
        input_data: 输入数据
        config: 配置参数
        **kwargs: 其他参数
        
    Returns:
        处理结果字典
        
    Raises:
        ValueError: 输入数据无效
        RuntimeError: 处理过程出错
    """
    try:
        logger.info("开始执行任务")
        
        # 参数验证
        if input_data is None:
            raise ValueError("输入数据不能为空")
            
        # TODO: 添加任务处理逻辑
        result = {{
            "success": True,
            "data": input_data,  # 占位符
            "message": "任务执行成功",
            "timestamp": "{datetime.now().isoformat()}"
        }}
        
        logger.info("任务执行完成")
        return result
        
    except Exception as e:
        logger.error(f"任务执行失败: {{e}}")
        return {{
            "success": False,
            "error": str(e),
            "timestamp": "{datetime.now().isoformat()}"
        }}
'''
        }

        template_code = templates.get(code_type, templates["script"])

        result = {
            "success": True,
            "task_description": task_description,
            "code_type": code_type,
            "language": language,
            "template_code": template_code,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"代码模板生成完成: {code_type}")
        return result

    except Exception as e:
        logger.error(f"生成代码模板时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_description": task_description,
            "timestamp": datetime.now().isoformat()
        }


async def debug_code_error(
    code: str,
    error_message: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    调试代码错误

    Args:
        code: 有问题的代码
        error_message: 错误信息
        context: 错误上下文

    Returns:
        调试建议和修复方案
    """
    try:
        # 分析错误类型
        error_type = "unknown"
        if "NameError" in error_message:
            error_type = "name_error"
        elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
            error_type = "import_error"
        elif "FileNotFoundError" in error_message:
            error_type = "file_error"
        elif "TypeError" in error_message:
            error_type = "type_error"
        elif "ValueError" in error_message:
            error_type = "value_error"
        elif "IndexError" in error_message:
            error_type = "index_error"
        elif "KeyError" in error_message:
            error_type = "key_error"
        elif "SyntaxError" in error_message:
            error_type = "syntax_error"

        # 根据错误类型提供建议
        suggestions_map = {
            "name_error": [
                "检查变量名是否正确拼写",
                "确认变量已在使用前定义",
                "检查变量的作用域",
                "确认函数或类名是否正确"
            ],
            "import_error": [
                "检查模块名是否正确",
                "确认模块已安装 (pip install module_name)",
                "检查模块路径是否正确",
                "确认Python环境是否正确"
            ],
            "file_error": [
                "检查文件路径是否存在",
                "确认文件权限是否正确",
                "使用绝对路径或相对路径",
                "检查文件是否已被占用"
            ],
            "type_error": [
                "检查变量类型是否匹配",
                "确认函数参数类型正确",
                "添加类型转换 (int(), str(), float())",
                "检查对象是否支持该操作"
            ],
            "value_error": [
                "检查参数值是否在有效范围内",
                "确认输入格式是否正确",
                "添加输入验证",
                "检查数据是否为空"
            ],
            "index_error": [
                "检查列表/数组索引是否越界",
                "确认容器不为空",
                "使用len()检查长度",
                "添加边界检查"
            ],
            "key_error": [
                "检查字典键是否存在",
                "使用dict.get()方法",
                "添加键存在性检查",
                "检查键名拼写"
            ],
            "syntax_error": [
                "检查括号、引号是否匹配",
                "确认缩进是否正确",
                "检查语法是否符合Python规范",
                "使用IDE检查语法错误"
            ]
        }

        specific_suggestions = suggestions_map.get(error_type, [
            "仔细阅读错误信息",
            "检查代码逻辑",
            "参考官方文档",
            "寻求帮助或示例"
        ])

        # 生成调试报告
        debug_report = {
            "error_analysis": {
                "error_type": error_type,
                "error_message": error_message,
                "context": context,
                "severity": "high" if error_type in ["syntax_error", "import_error"] else "medium"
            },
            "suggestions": specific_suggestions,
            "general_debugging_steps": [
                "1. 仔细阅读完整的错误信息",
                "2. 定位错误发生的具体行号",
                "3. 检查该行及相关代码",
                "4. 使用print()语句调试变量值",
                "5. 逐步注释代码找出问题点",
                "6. 查阅相关文档和示例"
            ],
            "code_review_checklist": [
                "变量名拼写正确",
                "所需模块已导入",
                "文件路径存在且可访问",
                "数据类型匹配",
                "数组索引在有效范围内",
                "字典键存在",
                "语法符合Python规范"
            ]
        }

        result = {
            "success": True,
            "original_code": code,
            "error_message": error_message,
            "debug_report": debug_report,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"代码调试分析完成: {error_type}")
        return result

    except Exception as e:
        logger.error(f"调试代码时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "original_error": error_message,
            "timestamp": datetime.now().isoformat()
        }


def get_coding_assistant(model_client=default_model_client):
    """编程助手智能体 - FastAPI适配版"""

    execute_tool = FunctionTool(
        func=execute_python_code,
        description="执行Python代码",
        strict=False
    )

    template_tool = FunctionTool(
        func=generate_code_template,
        description="生成代码模板",
        strict=False
    )

    debug_tool = FunctionTool(
        func=debug_code_error,
        description="调试代码错误",
        strict=False
    )

    coding_assistant = AssistantAgent(
        name="CodingAssistant",
        model_client=model_client,
        tools=[execute_tool, template_tool, debug_tool],
        system_message="""
        您是资深的Python开发工程师，负责实现算法和实验代码。您的职责包括：

        ## 核心职责
        1. 根据技术方案编写高质量的Python代码
        2. 实现机器学习算法和数据处理流程
        3. 编写完整的实验脚本和测试用例
        4. 调试和优化代码性能
        5. 确保代码的可读性和可维护性

        ## 编程标准
        **代码质量要求:**
        - 遵循PEP 8编码规范
        - 编写清晰的注释和文档字符串
        - 包含完整的错误处理机制
        - 使用类型提示提高代码可读性
        - 模块化设计，便于测试和维护

        **实验代码要求:**
        - 实现完整的数据预处理流程
        - 构建可配置的模型训练代码
        - 包含模型评估和验证逻辑
        - 生成可视化结果和性能报告
        - 保存模型和实验结果

        **文件组织规范:**
        - 数据输出保存到 ./output/ 目录
        - 图表保存到 ./plots/ 目录
        - 报告保存到 ./reports/ 目录
        - 模型文件保存到 ./models/ 目录
        - 使用相对路径和标准文件命名

        **最佳实践:**
        - 使用随机种子确保结果可重现
        - 记录实验参数和配置信息
        - 实现进度显示和日志记录
        - 包含内存和性能优化考虑
        - 编写可重用的函数和类

        **安全和稳定性:**
        - 添加输入验证和边界检查
        - 实现优雅的错误处理
        - 避免硬编码路径和参数
        - 考虑大数据集的内存使用
        - 提供清晰的错误消息

        ## 工具调用规则
        1. **执行代码时**: 调用 execute_python_code 工具
        2. **生成代码模板时**: 调用 generate_code_template 工具
        3. **调试错误时**: 调用 debug_code_error 工具
        4. **其他情况**: 直接提供编程指导和代码审查

        ## 协作要求
        - 与CodeDirector保持密切沟通，汇报进度
        - 为ExperimentRunner提供可执行的代码
        - 支持DataAnalyst的数据处理需求
        - 响应人工用户的代码修改请求
        - 在代码完成时明确说明"代码实现完成"

        ## 代码实现流程
        1. **需求分析**: 理解技术方案和具体需求
        2. **架构设计**: 设计代码结构和模块划分
        3. **模板生成**: 创建基础代码框架
        4. **逐步实现**: 分模块实现具体功能
        5. **测试验证**: 执行代码并验证结果
        6. **调试优化**: 修复错误并优化性能
        7. **文档完善**: 添加注释和使用说明

        请确保代码的专业性、可靠性和实用性，能够支持高质量的科研实验需求。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return coding_assistant