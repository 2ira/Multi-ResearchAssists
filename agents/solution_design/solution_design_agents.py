"""
修复的方案设计阶段智能体实现
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
import json
from typing import Dict, Any, List
import uuid
from datetime import datetime

default_model_client = create_model_client("default_model")


async def generate_architecture_diagram(
    system_description: str,
    diagram_type: str
) -> Dict[str, Any]:
    """
    生成系统架构图

    Args:
        system_description: 系统描述
        diagram_type: 图表类型

    Returns:
        包含架构图的字典
    """
    mermaid_diagram = f"""
graph TD
    A[用户输入] --> B[数据预处理模块]
    B --> C[核心算法模块]
    C --> D[结果后处理]
    D --> E[用户界面]
    
    subgraph "核心组件"
        C --> F[特征提取]
        C --> G[模型推理]
        C --> H[结果融合]
    end
    
    subgraph "支持服务"
        I[数据存储]
        J[缓存服务]
        K[监控服务]
    end
    
    B --> I
    C --> J
    E --> K
    """

    return {
        "diagram_id": str(uuid.uuid4()),
        "type": diagram_type,
        "description": system_description,
        "mermaid_code": mermaid_diagram,
        "timestamp": datetime.now().isoformat()
    }


async def recommend_tech_stack(
    project_requirements: str,
    project_type: str
) -> Dict[str, Any]:
    """
    推荐技术栈

    Args:
        project_requirements: 项目需求
        project_type: 项目类型

    Returns:
        技术栈推荐
    """
    tech_recommendations = {
        "programming_language": {
            "primary": "Python",
            "reason": "丰富的AI/ML库生态系统，易于原型开发"
        },
        "frameworks": [
            {
                "name": "PyTorch",
                "category": "深度学习框架",
                "reason": "研究友好，动态图支持"
            },
            {
                "name": "FastAPI",
                "category": "Web框架",
                "reason": "高性能，自动文档生成"
            }
        ],
        "databases": [
            {
                "name": "PostgreSQL",
                "category": "关系数据库",
                "reason": "强大的查询能力和扩展性"
            },
            {
                "name": "Redis",
                "category": "缓存数据库",
                "reason": "高性能缓存和会话存储"
            }
        ],
        "tools": [
            {
                "name": "Docker",
                "category": "容器化",
                "reason": "环境一致性和部署便利"
            },
            {
                "name": "MLflow",
                "category": "实验管理",
                "reason": "模型版本控制和实验跟踪"
            }
        ]
    }

    return {
        "project_requirements": project_requirements,
        "project_type": project_type,
        "recommendations": tech_recommendations,
        "timestamp": datetime.now().isoformat()
    }


async def evaluate_feasibility(
    solution_description: str,
    constraints: str
) -> Dict[str, Any]:
    """
    评估方案可行性

    Args:
        solution_description: 方案描述
        constraints: 约束条件

    Returns:
        可行性评估结果
    """
    evaluation = {
        "technical_feasibility": {
            "score": 0.85,
            "factors": [
                "技术成熟度高",
                "有开源实现参考",
                "计算资源需求合理"
            ],
            "risks": [
                "数据质量依赖性强",
                "模型训练时间较长"
            ]
        },
        "resource_requirements": {
            "development_time": "3-6个月",
            "team_size": "3-5人",
            "hardware": "GPU服务器 (8GB+ VRAM)",
            "budget_estimate": "中等"
        },
        "innovation_level": {
            "score": 0.75,
            "aspects": [
                "方法组合具有新颖性",
                "应用场景有创新点"
            ]
        },
        "overall_recommendation": "推荐实施，建议分阶段开发"
    }

    return {
        "solution": solution_description,
        "constraints": constraints,
        "evaluation": evaluation,
        "timestamp": datetime.now().isoformat()
    }


def get_solution_designer(model_client=default_model_client):
    """方案设计智能体"""

    architecture_tool = FunctionTool(
        func=generate_architecture_diagram,
        description="生成系统架构图",
        strict=False  # 改为非严格模式
    )

    tech_stack_tool = FunctionTool(
        func=recommend_tech_stack,
        description="推荐技术栈",
        strict=False  # 改为非严格模式
    )

    solution_designer = AssistantAgent(
        name="SolutionDesigner",
        model_client=model_client,
        tools=[architecture_tool, tech_stack_tool],
        system_message="""
        您是资深的系统架构师，负责基于文献分析提出创新技术方案。您的职责包括：

        1. 基于文献综述识别技术空白和改进机会
        2. 设计创新的技术解决方案
        3. 生成系统架构图和技术选型建议
        4. 评估方案的技术可行性和创新性

        设计原则：
        - 基于已有研究成果，避免重复造轮子
        - 确保技术方案的可实现性
        - 考虑系统的可扩展性和维护性
        - 平衡创新性和稳定性

        输出格式：
        ## 方案概述
        - 问题定义
        - 解决思路
        - 核心创新点

        ## 技术架构
        - 系统整体架构
        - 核心模块设计
        - 数据流程图

        ## 技术选型
        - 编程语言和框架
        - 数据库选择
        - 第三方库和工具

        **工具调用规则**：
        1. 需要生成架构图时，调用 generate_architecture_diagram
        2. 需要技术选型建议时，调用 recommend_tech_stack
        3. 其他情况直接返回自然语言回答

        请确保方案具有科学性、可行性和创新性。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return solution_designer


def get_design_reviewer(model_client=default_model_client):
    """方案评审智能体"""

    feasibility_tool = FunctionTool(
        func=evaluate_feasibility,
        description="评估方案可行性",
        strict=False  # 改为非严格模式
    )

    design_reviewer = AssistantAgent(
        name="DesignReviewer",
        model_client=model_client,
        tools=[feasibility_tool],
        system_message="""
        您是经验丰富的技术评审专家，负责评估技术方案的可行性和创新性。您的职责包括：

        1. 评估技术方案的可行性（技术、资源、时间）
        2. 分析方案的创新性和学术价值
        3. 识别潜在的技术风险和挑战
        4. 提供改进建议和优化方向
        5. 给出明确的评审结论和建议

        评审维度：
        ## 技术可行性
        - 技术成熟度评估
        - 实现难度分析
        - 资源需求评估

        ## 创新性评估
        - 与现有方法的区别
        - 技术贡献的新颖性
        - 潜在的学术影响

        ## 风险分析
        - 技术风险点
        - 项目执行风险
        - 缓解策略建议

        ## 改进建议
        - 技术优化方向
        - 实现路径建议
        - 阶段性目标设定

        **工具调用规则**：
        需要详细可行性分析时，调用 evaluate_feasibility 工具

        评审标准：客观、专业、建设性，为项目成功提供有价值的指导。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return design_reviewer


def get_solution_refiner(model_client=default_model_client):
    """方案细化智能体"""

    solution_refiner = AssistantAgent(
        name="SolutionRefiner",
        model_client=model_client,
        system_message="""
        您是专业的方案细化专家，负责将评审通过的技术方案进行详细设计。您的职责包括：

        1. 将高级方案转化为详细的技术设计文档
        2. 定义具体的模块接口和数据格式
        3. 制定详细的实现计划和里程碑
        4. 设计实验验证方案
        5. 准备技术原型的开发指南

        细化内容：
        ## 详细技术规格
        - 模块功能定义
        - 接口设计规范
        - 数据格式标准
        - 性能指标要求

        ## 实现计划
        - 开发阶段划分
        - 关键里程碑设定
        - 资源分配计划
        - 风险控制措施

        ## 实验设计
        - 验证实验方案
        - 评估指标定义
        - 基线方法选择
        - 数据集准备计划

        ## 开发指南
        - 代码结构设计
        - 开发环境配置
        - 测试策略制定
        - 文档编写规范

        输出要求：
        - 技术细节清晰明确
        - 实现步骤具体可操作
        - 考虑实际开发中的常见问题
        - 提供充分的技术文档支持

        请确保细化方案的完整性和可执行性。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return solution_refiner


def get_solution_director(model_client=default_model_client):
    """方案设计主管"""

    solution_director = AssistantAgent(
        name="SolutionDirector",
        model_client=model_client,
        system_message="""
        您是方案设计阶段的项目主管，负责整个方案设计工作流的管理和协调。您的职责包括：

        1. 根据文献调研结果，制定方案设计计划
        2. 协调各智能体的工作，确保设计质量
        3. 监控设计进度，管理评审流程
        4. 整合最终的技术方案文档
        5. 在关键节点请求人工审核和决策

        工作流程：
        1. 接收文献调研报告，分析技术现状和空白
        2. 指导SolutionDesigner设计初步技术方案
        3. 组织DesignReviewer进行方案评审
        4. 根据评审结果决定是否需要修改方案
        5. 指导SolutionRefiner进行方案细化
        6. 整合最终方案文档，提交人工审核

        协调要点：
        - 确保方案符合研究目标和约束条件
        - 平衡创新性和可行性
        - 控制设计周期和质量标准
        - 及时处理设计过程中的问题和分歧

        人工交互点：
        - 初步方案确认
        - 评审结果决策
        - 最终方案批准

        请以项目成功为目标，统筹管理整个方案设计过程。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return solution_director