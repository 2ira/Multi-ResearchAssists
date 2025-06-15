from autogen_core.tools import FunctionTool
from typing import Dict, Any, List
import json
import matplotlib.pyplot as plt
import numpy as np
import io
import base64


async def generate_latex_section(
        section_type: str,
        content: str,
        title: str = ""
) -> Dict[str, Any]:
    """
    生成LaTeX格式的论文章节

    Args:
        section_type: 章节类型 (abstract, introduction, methodology, experiments, conclusion)
        content: 章节内容
        title: 章节标题

    Returns:
        LaTeX格式的章节内容
    """
    print(f"📝 生成LaTeX章节: {section_type}")

    # LaTeX模板
    latex_templates = {
        "abstract": """
\\begin{{abstract}}
{content}
\\end{{abstract}}
        """,
        "introduction": """
\\section{{{title}}}
{content}
        """,
        "methodology": """
\\section{{{title}}}
{content}
        """,
        "experiments": """
\\section{{{title}}}
{content}
        """,
        "conclusion": """
\\section{{{title}}}
{content}
        """
    }

    template = latex_templates.get(section_type, "\\section{{{title}}}\n{content}")
    latex_content = template.format(title=title or section_type.title(), content=content)

    result = {
        "section_type": section_type,
        "latex_content": latex_content,
        "word_count": len(content.split()),
        "formatting_tips": [
            "确保数学公式使用正确的LaTeX语法",
            "表格和图片需要合适的标题和标签",
            "引用格式应该使用\\cite{}命令"
        ]
    }

    print(f"✅ LaTeX章节生成完成: {len(content)}字符")
    return result


async def manage_citations(
        papers_list: List[Dict[str, str]],
        citation_style: str = "IEEE"
) -> Dict[str, Any]:
    """
    管理参考文献和生成BibTeX

    Args:
        papers_list: 论文列表，包含title, authors, journal等信息
        citation_style: 引用风格

    Returns:
        BibTeX格式的参考文献
    """
    print(f"📚 管理引用文献: {len(papers_list)}篇论文")

    bibtex_entries = []
    for i, paper in enumerate(papers_list):
        # 生成引用key
        first_author = paper.get('authors', ['Unknown'])[0] if paper.get('authors') else 'Unknown'
        year = paper.get('year', '2023')
        key = f"{first_author.split()[-1].lower()}{year}"

        # 生成BibTeX条目
        if paper.get('journal'):
            entry_type = "article"
            venue_field = f"journal={{{paper['journal']}}}"
        else:
            entry_type = "inproceedings"
            venue_field = f"booktitle={{{paper.get('conference', 'Unknown Conference')}}}"

        bibtex_entry = f"""@{entry_type}{{{key},
    title={{{paper.get('title', 'Unknown Title')}}},
    author={{{' and '.join(paper.get('authors', ['Unknown']))}}},
    {venue_field},
    year={{{year}}},
    pages={{{paper.get('pages', '1--10')}}}
}}"""

        bibtex_entries.append(bibtex_entry)

    result = {
        "bibtex_content": "\n\n".join(bibtex_entries),
        "citation_count": len(papers_list),
        "citation_style": citation_style,
        "latex_packages": [
            "\\usepackage{cite}",
            "\\usepackage{url}",
            "\\usepackage{hyperref}"
        ],
        "usage_example": "使用 \\cite{key} 来引用文献"
    }

    print(f"✅ 引用管理完成: {len(bibtex_entries)}个条目")
    return result


async def create_scientific_plot(
        plot_type: str,
        data: Dict[str, Any],
        title: str = "",
        xlabel: str = "",
        ylabel: str = ""
) -> Dict[str, Any]:
    """
    创建科学图表

    Args:
        plot_type: 图表类型 (bar_chart, line_plot, scatter_plot, heatmap)
        data: 绘图数据
        title: 图表标题
        xlabel: X轴标签
        ylabel: Y轴标签

    Returns:
        图表信息和base64编码的图片
    """
    print(f"📊 创建科学图表: {plot_type}")

    plt.style.use('seaborn-v0_8')  # 使用科学风格
    fig, ax = plt.subplots(figsize=(10, 6))

    if plot_type == "bar_chart":
        methods = data.get('methods', [])
        scores = data.get('scores', [])
        bars = ax.bar(methods, scores, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
        ax.set_ylabel(ylabel or 'Score')
        ax.set_xlabel(xlabel or 'Methods')

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.3f}', ha='center', va='bottom')

    elif plot_type == "line_plot":
        x_data = data.get('x', [])
        y_data = data.get('y', [])
        ax.plot(x_data, y_data, marker='o', linewidth=2, markersize=6)
        ax.set_xlabel(xlabel or 'X')
        ax.set_ylabel(ylabel or 'Y')
        ax.grid(True, alpha=0.3)

    elif plot_type == "scatter_plot":
        x_data = data.get('x', [])
        y_data = data.get('y', [])
        ax.scatter(x_data, y_data, alpha=0.6, s=50)
        ax.set_xlabel(xlabel or 'X')
        ax.set_ylabel(ylabel or 'Y')

    ax.set_title(title, fontsize=14, fontweight='bold')

    # 保存图片为base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    result = {
        "plot_type": plot_type,
        "image_base64": image_base64,
        "title": title,
        "description": f"Generated {plot_type} with {len(data)} data points",
        "latex_code": f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.8\\textwidth]{{figures/{title.lower().replace(' ', '_')}.png}}
\\caption{{{title}}}
\\label{{fig:{title.lower().replace(' ', '_')}}}
\\end{{figure}}
        """,
        "recommendations": [
            "确保图表在黑白打印时仍然清晰",
            "添加适当的图例和标注",
            "保持与论文其他图表的风格一致"
        ]
    }

    print(f"✅ 图表创建完成: {title}")
    return result


def get_latex_generator_tool():
    return FunctionTool(
        func=generate_latex_section,
        description="Generate LaTeX formatted paper sections",
        strict=True,
    )


def get_citation_manager_tool():
    return FunctionTool(
        func=manage_citations,
        description="Manage references and generate BibTeX",
        strict=True,
    )


def get_plot_generator_tool():
    return FunctionTool(
        func=create_scientific_plot,
        description="Create scientific figures and plots",
        strict=True,
    )