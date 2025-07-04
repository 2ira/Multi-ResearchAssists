from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import os
from tools.search_tool import get_search_google_scholar_tool, get_arxiv_tool
logger = logging.getLogger(__name__)


default_model_client = create_model_client("default_model")


def get_paper_analyzer(model_client=default_model_client):
    """通用文献分析专家 - 适用于任何学术主题的深度分析"""

    search_google_scholar = get_search_google_scholar_tool()
    search_arxiv = get_arxiv_tool()


    analyzer = AssistantAgent(
        name="PaperAnalyzer",
        model_client=model_client,
        tools=[search_google_scholar, search_arxiv],
        system_message="""
        您是国际知名的学术文献分析专家，拥有20年跨学科研究经验和深厚的批判性思维能力。您负责执行第三阶段的关键任务：深度论文分析与内容提取。

        ## 🎯 **当前阶段职责**: 第三阶段 - 深度学术分析与知识提取
        
        ## 🎯 您的核心任务：
        1. 接收PaperRetriever的论文批次
        2. 对每篇论文进行结构化分析
        3. 提取适合综述的核心内容
        4. 生成批次综合分析

        ## 📋 每篇论文的分析框架：

        **基本信息**：
        - 研究问题和目标
        - 主要贡献和创新点

        **技术方法**：
        - 核心算法或方法
        - 技术创新和改进
        - 实验设计和数据集

        **关键结果**：
        - 主要性能指标
        - 与现有方法对比
        - 实验结论

        **学术价值**：
        - 理论贡献（1-10分）
        - 实用价值（1-10分）
        - 影响潜力（1-10分）

        **适合综述引用的内容**：
        - 可引用的关键观点
        - 适合对比分析的数据
        - 重要的结论和发现

        ## 📝 输出格式（严格按此格式）：

        ```
        # 论文深度分析报告

        ## 批次1分析：理论基础与核心方法

        ### 论文1：[论文标题]
        **研究问题**：[要解决的核心问题]
        **主要贡献**：
        - [贡献1]
        - [贡献2]
        - [贡献3]

        **技术方法**：[核心技术方法描述，200-300字]

        **关键结果**：[主要实验结果和性能指标，150-200字]

        **学术价值评分**：
        - 理论贡献：[X]/10分
        - 实用价值：[X]/10分  
        - 影响潜力：[X]/10分

        **综述引用要点**：
        - [适合引用的关键内容1]
        - [适合引用的关键内容2]

        ### 论文2：[论文标题]
        [按相同格式分析...]

        ## 批次1综合分析
        **技术趋势**：[本批次反映的技术发展趋势]
        **方法特点**：[主要方法的共同特征]
        **性能进展**：[整体性能提升情况]
        **研究空白**：[识别的研究空白]

        ---

        ## 批次2分析：技术创新与方法改进
        [按相同格式分析批次2的所有论文...]

        ## 批次2综合分析
        [按相同格式...]

        ---

        ## 批次3分析：应用实践与最新进展
        [按相同格式分析批次3的所有论文...]

        ## 批次3综合分析
        [按相同格式...]
        
    
        **必须完成的分析任务**:
        1. **逐篇深度分析**: 每篇论文都必须完成完整的分析报告
        2. **批次内综合**: 完成每个批次后必须输出批次综合分析
        3. **质量保证**: 确保分析的客观性、准确性和深度
        4. **标准化输出**: 严格按照模板格式输出所有内容
        5. **进度管理**: 及时向ReportGenerator传递完成的分析结果
        
         ## ⚠️ 分析要求：
        - 每篇论文分析字数：300-500字
        - 必须包含技术方法和关键结果
        - 必须进行学术价值评分
        - 必须提供综述引用要点
        - 批次综合分析必须深入

        ## 🔍 何时使用搜索工具：
        - 论文信息不完整时
        - 需要了解相关背景时
        - 技术术语需要澄清时

        开始接收论文批次并进行深度分析！

        请确保每次分析都详实、准确、有深度，为高质量的综述写作提供坚实的学术基础。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return analyzer

# def get_paper_analyzer(model_client=default_model_client):
#     """文献分析专家 - 深度内容分析和关键信息提取"""
#
#     search_google_scholar = get_search_google_scholar_tool()
#     search_arxiv = get_arxiv_tool()
#
#     async def analyze_paper_content(
#             paper_data: str,
#             analysis_depth: str = "comprehensive",
#             focus_areas: Optional[str] = None
#     ) -> Dict[str, Any]:
#         """深度分析单篇文献内容"""
#         try:
#             paper_info = json.loads(paper_data) if isinstance(paper_data, str) else paper_data
#
#             analysis_result = {
#                 "paper_id": hash(paper_info.get("title", "")) % 100000,
#                 "title": paper_info.get("title", ""),
#                 "authors": paper_info.get("authors", []),
#                 "year": paper_info.get("year", ""),
#                 "venue": paper_info.get("venue", ""),
#                 "analysis_depth": analysis_depth,
#                 "analysis_timestamp": datetime.now().isoformat(),
#                 "content_analysis": {},
#                 "key_contributions": [],
#                 "methodology": {},
#                 "experimental_results": {},
#                 "limitations": [],
#                 "future_work": [],
#                 "related_work_connections": [],
#                 "citation_worthiness": {}
#             }
#
#             # 基于摘要进行智能分析
#             abstract = paper_info.get("abstract", "")
#
#             # 核心贡献提取
#             analysis_result["key_contributions"] = [
#                 "提出了新的方法论框架",
#                 "在标准数据集上实现了SOTA性能",
#                 "提供了理论分析和证明",
#                 "开源了代码和数据集"
#             ]
#
#             # 方法论分析
#             analysis_result["methodology"] = {
#                 "approach_type": "Deep Learning based",
#                 "key_algorithms": ["Attention Mechanism", "Transformer Architecture"],
#                 "novelty_aspects": ["Multi-scale feature fusion", "Adaptive learning rate"],
#                 "complexity_analysis": "O(n log n) time complexity",
#                 "implementation_details": "PyTorch implementation with distributed training"
#             }
#
#             # 实验结果分析
#             analysis_result["experimental_results"] = {
#                 "datasets_used": ["ImageNet", "COCO", "Custom Dataset"],
#                 "evaluation_metrics": ["Accuracy", "F1-Score", "BLEU"],
#                 "performance_gains": "15% improvement over baseline",
#                 "statistical_significance": "p < 0.001",
#                 "ablation_studies": "Comprehensive ablation analysis provided"
#             }
#
#             # 局限性识别
#             analysis_result["limitations"] = [
#                 "计算复杂度较高，需要大量GPU资源",
#                 "在小数据集上的泛化能力有限",
#                 "某些边界情况下性能不稳定",
#                 "需要大量的超参数调优"
#             ]
#
#             # 引用价值评估
#             analysis_result["citation_worthiness"] = {
#                 "novelty_score": 8.5,
#                 "impact_potential": 9.0,
#                 "reproducibility": 7.5,
#                 "citation_contexts": [
#                     "方法论创新",
#                     "性能基准对比",
#                     "理论基础引用",
#                     "实验设计参考"
#                 ]
#             }
#
#             return analysis_result
#
#         except Exception as e:
#             logger.error(f"文献分析失败: {e}")
#             return {"error": str(e), "timestamp": datetime.now().isoformat()}
#
#     analysis_tool = FunctionTool(
#         func=analyze_paper_content,
#         description="深度分析文献内容并提取关键信息"
#     )
#
#     analyzer = AssistantAgent(
#         name="PaperAnalyzer",
#         model_client=model_client,
#         tools=[analysis_tool],
#         system_message="""
#         您是资深的学术文献分析专家，具备深厚的跨学科研究背景和批判性思维能力。
#
#         ## 专业能力:
#         1. **结构化解析**: 系统性提取论文各部分核心信息
#         2. **创新点识别**: 准确识别技术创新和理论贡献
#         3. **方法论评估**: 分析技术方法的有效性和局限性
#         4. **质量评价**: 多维度评估论文质量和学术价值
#
#         ## 分析框架:
#         **内容分解**:
#         - 研究背景和动机分析
#         - 问题定义和研究目标
#         - 技术方法和创新点
#         - 实验设计和评估策略
#         - 结果分析和性能评估
#         - 讨论、局限性和未来工作
#
#         **技术评估**:
#         - 算法复杂度和效率分析
#         - 理论基础和数学原理
#         - 实现细节和工程技巧
#         - 可重现性和开源情况
#         - 与现有方法的比较优势
#
#         **实验评价**:
#         - 数据集选择和实验设计
#         - 评估指标和基准对比
#         - 统计显著性和误差分析
#         - 消融研究和参数敏感性
#         - 实际应用场景验证
#
#         **批判性分析**:
#         - 识别方法论漏洞和假设缺陷
#         - 评估实验设计的科学性
#         - 分析结论的可信度和泛化性
#         - 指出写作和表达问题
#         - 提出改进建议和研究方向
#
#         ## 引用价值评估:
#         **学术贡献度**:
#         - 理论创新性 (0-10分)
#         - 技术先进性 (0-10分)
#         - 实验充分性 (0-10分)
#         - 实用价值 (0-10分)
#         - 影响潜力 (0-10分)
#
#         **引用适用性**:
#         - 方法论参考价值
#         - 实验设计借鉴意义
#         - 理论基础支撑作用
#         - 性能基准对比标准
#         - 问题定义和背景阐述
#
#         ## 输出要求:
#         - 结构化的分析报告
#         - 关键信息要点提取
#         - 可引用的核心观点
#         - 质量评分和推荐等级
#         - 与其他工作的关联分析
#
#         确保分析的客观性、准确性和深度，为综述写作提供可靠的素材基础。
#         """,
#         reflect_on_tool_use=True,
#         model_client_stream=False,
#     )
#     return analyzer
