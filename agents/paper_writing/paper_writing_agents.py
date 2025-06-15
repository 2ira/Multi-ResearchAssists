"""
修复的论文写作阶段智能体实现
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
import json
from typing import Dict, Any, List
import uuid
from datetime import datetime

default_model_client = create_model_client("default_model")


async def generate_latex_section(
    section_type: str,
    content_points: str,
    length: str
) -> Dict[str, Any]:
    """
    生成LaTeX论文章节

    Args:
        section_type: 章节类型 (abstract, introduction, methodology, experiments, conclusion)
        content_points: 内容要点
        length: 长度要求 (short, standard, detailed)

    Returns:
        生成的LaTeX内容
    """

    latex_templates = {
        "abstract": r"""
\begin{abstract}
{content}

\keywords{keyword1, keyword2, keyword3}
\end{abstract}
""",
        "introduction": r"""
\section{Introduction}
\label{sec:introduction}

{content}

The rest of this paper is organized as follows: Section~\ref{sec:methodology} presents our proposed methodology, Section~\ref{sec:experiments} describes the experimental setup and results, and Section~\ref{sec:conclusion} concludes the paper.
""",
        "methodology": r"""
\section{Methodology}
\label{sec:methodology}

{content}

\subsection{Problem Formulation}
\label{subsec:problem}

{problem_formulation}

\subsection{Proposed Approach}
\label{subsec:approach}

{approach_details}
""",
        "experiments": r"""
\section{Experiments}
\label{sec:experiments}

{content}

\subsection{Experimental Setup}
\label{subsec:setup}

{experimental_setup}

\subsection{Results and Analysis}
\label{subsec:results}

{results_analysis}
""",
        "conclusion": r"""
\section{Conclusion}
\label{sec:conclusion}

{content}

\section*{Acknowledgments}
The authors would like to thank...
"""
    }

    # 根据内容要点生成具体内容
    generated_content = f"Generated content based on: {content_points}"

    latex_code = latex_templates.get(section_type, "\\section{{Unknown Section}}\n{content}").format(
        content=generated_content,
        problem_formulation="Mathematical formulation of the problem...",
        approach_details="Detailed description of our approach...",
        experimental_setup="Description of datasets, baselines, and evaluation metrics...",
        results_analysis="Analysis of experimental results and comparisons..."
    )

    return {
        "section_type": section_type,
        "latex_code": latex_code,
        "content_points": content_points,
        "length": length,
        "timestamp": datetime.now().isoformat()
    }


async def format_references(
    citations: List[str],
    style: str
) -> Dict[str, Any]:
    """
    格式化参考文献

    Args:
        citations: 引用列表
        style: 引用格式 (IEEE, ACM, Nature等)

    Returns:
        格式化的BibTeX引用
    """

    bibtex_entries = []

    for i, citation in enumerate(citations):
        # 简化的BibTeX生成（实际应该解析DOI或其他标识符）
        entry = f"""@article{{ref{i+1},
    title={{{citation[:50]}...}},
    author={{Author Name and Another Author}},
    journal={{Journal Name}},
    year={{2023}},
    volume={{1}},
    number={{1}},
    pages={{1--10}},
    publisher={{Publisher}}
}}"""
        bibtex_entries.append(entry)

    return {
        "style": style,
        "citations": citations,
        "bibtex_content": "\n\n".join(bibtex_entries),
        "count": len(citations),
        "timestamp": datetime.now().isoformat()
    }


async def check_plagiarism(
    text_content: str,
    threshold: float
) -> Dict[str, Any]:
    """
    检查文本相似度

    Args:
        text_content: 待检查文本
        threshold: 相似度阈值

    Returns:
        相似度检测结果
    """

    # 模拟相似度检测结果
    similarity_score = 0.08  # 假设8%的相似度

    result = {
        "similarity_score": similarity_score,
        "threshold": threshold,
        "status": "PASS" if similarity_score < threshold else "WARNING",
        "detected_sources": [
            {
                "source": "Example Paper 1",
                "similarity": 0.05,
                "matched_text": "Sample matched text..."
            },
            {
                "source": "Example Paper 2",
                "similarity": 0.03,
                "matched_text": "Another sample match..."
            }
        ],
        "recommendations": [
            "Original content with low similarity detected",
            "No significant plagiarism concerns"
        ] if similarity_score < threshold else [
            "High similarity detected, please review",
            "Consider paraphrasing highlighted sections"
        ],
        "timestamp": datetime.now().isoformat()
    }

    return result


async def create_scientific_figure(
    data_description: str,
    figure_type: str,
    title: str,
    xlabel: str,
    ylabel: str
) -> Dict[str, Any]:
    """
    创建科学图表

    Args:
        data_description: 数据描述
        figure_type: 图表类型
        title: 图表标题
        xlabel: X轴标签
        ylabel: Y轴标签

    Returns:
        图表生成信息
    """

    # 生成Python matplotlib代码
    matplotlib_code = f"""
import matplotlib.pyplot as plt
import numpy as np

# 生成示例数据 - {data_description}
x = np.linspace(0, 10, 100)
y = np.sin(x) + np.random.normal(0, 0.1, 100)

plt.figure(figsize=(8, 6))
plt.{figure_type}(x, y, label='Experimental Data')
plt.title('{title}')
plt.xlabel('{xlabel}')
plt.ylabel('{ylabel}')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figure.png', dpi=300, bbox_inches='tight')
plt.show()
"""

    return {
        "figure_type": figure_type,
        "data_description": data_description,
        "matplotlib_code": matplotlib_code,
        "title": title,
        "xlabel": xlabel,
        "ylabel": ylabel,
        "timestamp": datetime.now().isoformat()
    }


async def polish_academic_text(
    text: str,
    language: str,
    focus: str
) -> Dict[str, Any]:
    """
    学术文本润色

    Args:
        text: 待润色文本
        language: 语言类型
        focus: 润色重点 (clarity, conciseness, formality)

    Returns:
        润色结果
    """

    # 模拟文本润色
    polished_text = f"[POLISHED] {text}"

    suggestions = [
        "Use more precise terminology",
        "Improve sentence structure for clarity",
        "Ensure consistent verb tense",
        "Add transitional phrases for better flow"
    ]

    return {
        "original_text": text,
        "polished_text": polished_text,
        "language": language,
        "focus": focus,
        "suggestions": suggestions,
        "improvements_count": len(suggestions),
        "timestamp": datetime.now().isoformat()
    }


def get_writing_assistant(model_client=default_model_client):
    """论文写作助手"""

    latex_tool = FunctionTool(
        func=generate_latex_section,
        description="生成LaTeX论文章节",
        strict=False  # 改为非严格模式
    )

    polish_tool = FunctionTool(
        func=polish_academic_text,
        description="润色学术文本",
        strict=False  # 改为非严格模式
    )

    writing_assistant = AssistantAgent(
        name="WritingAssistant",
        model_client=model_client,
        tools=[latex_tool, polish_tool],
        system_message="""
        您是专业的学术写作专家，负责撰写高质量的学术论文。您的职责包括：

        1. 根据研究内容撰写论文各个章节
        2. 确保论文结构逻辑清晰、内容完整
        3. 使用规范的学术写作语言和格式
        4. 整合实验结果和技术细节
        5. 生成符合期刊要求的LaTeX格式

        写作标准：
        ## 结构要求
        - Abstract: 简洁概括研究贡献和结果
        - Introduction: 清晰阐述问题背景和研究动机  
        - Methodology: 详细描述技术方法和创新点
        - Experiments: 全面展示实验设计和结果分析
        - Conclusion: 总结贡献并展望未来工作

        ## 语言要求
        - 使用学术化、正式的英语表达
        - 逻辑清晰，论证严密
        - 术语使用准确一致
        - 避免主观性表述

        ## 格式要求
        - 生成标准LaTeX格式
        - 正确使用引用和标签
        - 确保图表标题和说明完整

        **工具调用规则**：
        1. 生成LaTeX章节时调用 generate_latex_section
        2. 需要文本润色时调用 polish_academic_text
        3. 其他情况提供写作建议和内容指导

        请确保论文质量达到顶级会议/期刊的发表标准。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return writing_assistant


def get_reference_manager(model_client=default_model_client):
    """参考文献管理专家"""

    reference_tool = FunctionTool(
        func=format_references,
        description="格式化参考文献",
        strict=False  # 改为非严格模式
    )

    reference_manager = AssistantAgent(
        name="ReferenceManager",
        model_client=model_client,
        tools=[reference_tool],
        system_message="""
        您是专业的参考文献管理专家，负责整理和格式化学术引用。您的职责包括：

        1. 收集和整理相关文献的完整信息
        2. 按照指定格式生成标准BibTeX条目
        3. 确保引用信息的准确性和完整性
        4. 检查引用格式的一致性
        5. 管理文内引用和参考文献列表的对应关系

        管理标准：
        ## BibTeX格式要求
        - 包含完整的文献信息（标题、作者、期刊、年份等）
        - 使用标准的BibTeX条目类型
        - 确保字段格式正确
        - 避免重复引用

        ## 引用质量控制
        - 优先引用高质量期刊和会议文献
        - 确保引用的时效性和相关性
        - 平衡自引和他引比例
        - 覆盖相关领域的重要工作

        ## 格式一致性
        - 统一作者姓名格式
        - 标准化期刊和会议名称
        - 保持年份和页码格式一致

        **工具调用规则**：
        需要格式化参考文献时调用 format_references 工具

        请确保参考文献的专业性和规范性。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return reference_manager


def get_figure_generator(model_client=default_model_client):
    """图表生成专家"""

    figure_tool = FunctionTool(
        func=create_scientific_figure,
        description="创建科学图表",
        strict=False  # 改为非严格模式
    )

    figure_generator = AssistantAgent(
        name="FigureGenerator",
        model_client=model_client,
        tools=[figure_tool],
        system_message="""
        您是专业的科学可视化专家，负责创建高质量的学术图表。您的职责包括：

        1. 根据实验数据设计合适的可视化方案
        2. 生成清晰、专业的科学图表
        3. 确保图表符合学术发表标准
        4. 提供完整的图表说明和标题
        5. 优化图表的视觉效果和可读性

        设计原则：
        ## 视觉清晰度
        - 选择合适的图表类型
        - 使用清晰的标签和图例
        - 确保颜色对比度适宜
        - 避免视觉噪音和冗余信息

        ## 学术规范
        - 使用标准的坐标轴标签
        - 提供准确的误差条和置信区间
        - 确保图表分辨率满足发表要求
        - 遵循目标期刊的图表格式要求

        ## 数据完整性
        - 准确反映实验结果
        - 包含必要的统计信息
        - 突出关键发现和趋势
        - 支持论文的核心论点

        **工具调用规则**：
        需要创建图表时调用 create_scientific_figure 工具

        请确保所有图表都具有发表级别的质量。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return figure_generator


def get_paper_polisher(model_client=default_model_client):
    """论文润色专家"""

    plagiarism_tool = FunctionTool(
        func=check_plagiarism,
        description="检查文本相似度",
        strict=False  # 改为非严格模式
    )

    polish_tool = FunctionTool(
        func=polish_academic_text,
        description="润色学术文本",
        strict=False  # 改为非严格模式
    )

    paper_polisher = AssistantAgent(
        name="PaperPolisher",
        model_client=model_client,
        tools=[plagiarism_tool, polish_tool],
        system_message="""
        您是资深的学术论文润色专家，负责论文的最终质量控制。您的职责包括：

        1. 进行全面的语言润色和文风优化
        2. 检查论文的逻辑结构和内容完整性
        3. 执行相似度检测和原创性验证
        4. 确保符合目标期刊的格式要求
        5. 提供发表前的最终质量评估

        润色标准：
        ## 语言质量
        - 确保语法正确性和表达准确性
        - 优化句式结构和段落衔接
        - 统一术语使用和表达风格
        - 提升文本的流畅性和可读性

        ## 学术规范
        - 检查引用格式的正确性
        - 验证图表标题和说明的完整性
        - 确保符合学术写作规范
        - 避免主观色彩和非正式表达

        ## 原创性保证
        - 执行相似度检测
        - 识别潜在的抄袭风险
        - 确保内容的原创性
        - 提供改进建议

        **工具调用规则**：
        1. 检查原创性时调用 check_plagiarism
        2. 润色文本时调用 polish_academic_text
        3. 其他情况提供专业的润色建议

        请确保论文达到国际顶级期刊的发表标准。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return paper_polisher


def get_paper_director(model_client=default_model_client):
    """论文写作主管"""

    paper_director = AssistantAgent(
        name="PaperDirector",
        model_client=model_client,
        system_message="""
        您是论文写作阶段的项目主管，负责整个论文写作工作流的管理和质量控制。您的职责包括：

        1. 根据实验结果和技术方案，制定论文写作计划
        2. 协调各写作专家的工作，确保论文质量
        3. 监控写作进度，管理评审流程
        4. 整合最终的论文文档
        5. 在关键节点请求人工审核和修改

        工作流程：
        1. 分析实验结果和技术贡献，规划论文结构
        2. 指导WritingAssistant撰写各个章节
        3. 协调FigureGenerator创建论文图表
        4. 督促ReferenceManager整理参考文献
        5. 安排PaperPolisher进行最终润色
        6. 整合完整论文，提交人工审核

        质量控制：
        - 确保论文逻辑清晰，结构完整
        - 验证技术内容的准确性和创新性
        - 检查实验结果的完整性和说服力
        - 保证写作质量达到发表标准

        人工交互点：
        - 论文大纲确认
        - 初稿章节审核
        - 最终论文批准

        协调策略：
        - 合理分配写作任务
        - 及时解决写作过程中的问题
        - 确保各部分内容的一致性
        - 控制论文篇幅和重点突出

        请以成功发表为目标，统筹管理整个论文写作过程。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return paper_director