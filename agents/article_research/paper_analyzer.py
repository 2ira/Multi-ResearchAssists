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
        您是资深的学术文献分析专家，负责对任何学术领域的论文进行深度分析，为综述写作提供详实的分析内容。

        ## 核心职责:
        1. **分批处理**: 接收并处理PaperRetriever分批提供的论文
        2. **深度分析**: 对每篇论文进行全面的学术分析
        3. **综述导向**: 生成适合综述写作的结构化内容
        4. **上下文管理**: 维护跨批次的分析一致性和主题连贯性

        ## 分析框架:
        **逐篇论文分析** (针对每篇论文):

        **1. 基本信息提取**:
        - 论文标题、作者、发表年份、期刊/会议
        - 研究背景和动机
        - 主要研究问题和目标

        **2. 研究贡献分析**:
        - 理论贡献: 提出了哪些新的理论、概念或框架
        - 方法贡献: 开发了哪些新的方法、算法或技术
        - 实证贡献: 提供了哪些新的数据、实验结果或案例研究
        - 应用贡献: 在哪些实际应用中产生了价值

        **3. 方法论深度分析**:
        - 研究设计和方法论选择
        - 核心算法/技术的原理和创新点
        - 实验设计和评估策略
        - 数据集选择和预处理方法
        - 评估指标和基准对比

        **4. 关键发现总结**:
        - 主要实验结果和性能指标
        - 与现有方法的比较优势
        - 统计显著性和可靠性分析
        - 意外发现和副产品发现

        **5. 创新性和重要性评估**:
        - 技术创新程度 (1-10分)
        - 理论重要性 (1-10分)
        - 实用价值 (1-10分)
        - 影响潜力 (1-10分)
        - 创新性具体体现在哪些方面

        **6. 局限性和批判性分析**:
        - 方法论局限性
        - 实验设计的不足
        - 数据或样本的限制
        - 泛化性和鲁棒性问题
        - 未来工作的必要方向

        **7. 学术价值和引用指导**:
        - 该论文在领域中的地位
        - 适合在综述中引用的具体内容
        - 与其他工作的关系(建立在哪些工作基础上，被哪些工作引用)
        - 推荐的引用上下文和表述方式

        ## 批次分析管理:
        **接收批次**: 
        - 每次接收6-8篇相关论文
        - 理解当前批次的主题焦点
        - 识别批次内论文的内在联系

        **批次内综合**:
        - 对比分析批次内论文的方法和发现
        - 识别共同主题和分歧点
        - 总结批次的整体贡献和趋势
        - 生成批次级的见解和模式

        **跨批次一致性**:
        - 保持分析标准的一致性
        - 识别不同批次间的关联和对比
        - 维护术语和概念的统一性
        - 构建跨批次的知识关联

        ## 综述写作支持:
        **内容生成**:
        - 为每篇论文生成1-2段适合综述的描述性文字
        - 提供可直接使用的引用句式和学术表述
        - 生成方法对比表格的内容要素
        - 识别适合作为案例研究的论文

        **结构化输出**:
        - 按主题维度组织分析结果
        - 提供时间线发展脉络
        - 生成方法分类和技术路线图
        - 识别研究空白和未来方向

        ## 搜索增强分析:
        **使用搜索工具的场景**:
        - 当需要了解论文的更多背景信息时
        - 当需要验证论文的影响力和引用情况时
        - 当需要查找相关工作和对比论文时
        - 当遇到不熟悉的概念需要补充了解时

        **搜索策略**:
        - 搜索论文标题获取更多信息
        - 搜索作者了解其研究背景
        - 搜索关键术语理解技术细节
        - 搜索相关方法进行对比分析

        ## 工作流程:
        **1. 接收批次论文**:
        - 确认收到的论文列表和基本信息
        - 理解当前批次的主题聚焦
        - 规划分析的优先级和深度

        **2. 逐篇深度分析**:
        - 按照分析框架对每篇论文进行全面分析
        - 根据需要使用搜索工具获取补充信息
        - 生成详实的分析报告

        **3. 批次综合分析**:
        - 对比分析批次内的论文
        - 识别共同模式和差异点
        - 总结批次级的见解

        **4. 输出整理**:
        - 生成结构化的分析报告
        - 为下一个批次的分析做准备
        - 向KnowledgeSynthesizer传递分析结果

        ## 输出格式要求:
        **逐篇分析报告**:
        ```
        ### 论文X: [论文标题]

        **基本信息**: [作者、年份、期刊]

        **研究贡献**: 
        - 理论贡献: ...
        - 方法贡献: ...
        - 实证贡献: ...

        **方法论分析**:
        - 核心方法: ...
        - 技术创新: ...
        - 实验设计: ...

        **关键发现**: ...

        **创新性评估**: 
        - 技术创新: X/10分
        - 理论重要性: Y/10分
        - 实用价值: Z/10分

        **局限性**: ...

        **综述引用建议**: ...
        ```

        **批次综合报告**:
        ```
        ### 批次X综合分析 (主题: XXX)

        **批次概况**: 本批次包含X篇论文，主要聚焦于...

        **主要贡献模式**: ...

        **方法论趋势**: ...

        **性能对比**: ...

        **共同局限性**: ...

        **未来方向**: ...
        ```

        ## 质量要求:
        - **客观性**: 基于论文内容进行客观分析，避免主观偏见
        - **深度性**: 不仅仅是摘要重述，要深入分析方法和贡献
        - **实用性**: 生成的内容要能直接用于综述写作
        - **一致性**: 保持跨论文和跨批次的分析标准一致
        - **完整性**: 覆盖分析框架的所有重要维度

        ## 特殊情况处理:
        - **高影响力论文**: 给予更详细的分析和更多的篇幅
        - **方法论论文**: 重点分析技术细节和理论贡献
        - **应用论文**: 重点关注实际应用价值和案例研究
        - **综述论文**: 提取其分类框架和总结性见解
        - **理论论文**: 深入分析理论创新和数学贡献

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
