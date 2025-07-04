"""
优化版顺序交互文献调研工作流实现 - 高质量prompt版本
Enhanced SurveyDirector → PaperRetriever → PaperAnalyzer → ReportGenerator
与base_workflow.py完全兼容，专注于高质量学术综述生成
"""

from base_workflow import StagedWorkflowSession, WorkflowStage
from typing import List
import logging

logger = logging.getLogger(__name__)


#
# class SurveyWorkflowSession(StagedWorkflowSession):
#     """优化版文献调研工作流会话 - 专注高质量综述生成"""
#
#     def define_workflow_stages(self) -> List[WorkflowStage]:
#         """定义优化的四阶段文献调研工作流"""
#         return [
#             WorkflowStage(
#                 stage_id="stage_1_strategy_planning",
#                 name="🎯 调研策略制定阶段",
#                 agent_name="SurveyDirector",
#                 description="""
#                 核心任务：深度主题分析 + 系统化检索策略制定
#                 - 识别研究主题的核心概念和学科边界
#                 - 构建多层次英文关键词体系(50+关键词)
#                 - 设计8个不同角度的检索查询
#                 - 制定严格的质量控制标准(25-40篇目标)
#                 - 生成标准化的检索指令传递给PaperRetriever
#                 成功标准：策略覆盖面广、关键词科学、查询针对性强
#                 """
#             ),
#             WorkflowStage(
#                 stage_id="stage_2_systematic_retrieval",
#                 name="🔍 系统化论文检索阶段",
#                 agent_name="PaperRetriever",
#                 description="""
#                 核心任务：多轮高质量文献检索 + 智能筛选分类
#                 - 执行8个主查询的arXiv检索(第1轮)
#                 - Google Scholar补充检索(第2轮)
#                 - 优化查询深度检索(第3轮)
#                 - 应用严格质量过滤标准(引用数、期刊等级、相关性)
#                 - 智能分类为4个主题批次供后续分析
#                 成功标准：25-40篇高质量论文，分类合理，信息完整
#                 """
#             ),
#             WorkflowStage(
#                 stage_id="stage_3_deep_analysis",
#                 name="🔬 深度学术分析阶段",
#                 agent_name="PaperAnalyzer",
#                 description="""
#                 核心任务：逐篇深度分析 + 批次综合分析
#                 - 对每篇论文进行8维度深度分析(800+字/篇)
#                 - 技术创新性评分和批判性分析
#                 - 提取适合综述引用的核心内容
#                 - 识别论文间关联关系和发展脉络
#                 - 输出批次综合分析和趋势识别
#                 成功标准：分析深度充分、评估客观准确、引用建议实用
#                 """
#             ),
#             WorkflowStage(
#                 stage_id="stage_4_comprehensive_survey",
#                 name="📝 综述报告生成阶段",
#                 agent_name="ReportGenerator",
#                 description="""
#                 核心任务：生成15,000词顶级期刊标准综述
#                 - 整合所有分析结果为连贯学术叙述
#                 - 12个主要章节的深度技术分析
#                 - 60+篇文献的准确引用管理
#                 - 原创性洞察和前瞻性发展预测
#                 - 专业HTML格式与交互功能
#                 成功标准：达到Nature/Science等顶级期刊发表标准
#                 """
#             )
#         ]
#
#     async def get_agents(self) -> List:
#         """获取优化版智能体列表 - 按执行顺序排列"""
#         try:
#             # 导入优化后的智能体
#             from agents.article_research.survey_director import get_survey_director
#             from agents.article_research.paper_retriever import get_paper_retriever
#             from agents.article_research.paper_analyzer import get_paper_analyzer
#             from agents.article_research.report_generator import get_report_generator
#
#             return [
#                 get_survey_director(),  # 第1阶段：策略制定
#                 get_paper_retriever(),  # 第2阶段：论文检索
#                 get_paper_analyzer(),  # 第3阶段：深度分析
#                 get_report_generator()  # 第4阶段：综述生成
#             ]
#         except Exception as e:
#             logger.warning(f"无法加载优化智能体: {e}, 使用模拟模式")
#             return []  # 返回空列表，使用模拟执行
#
#     def get_workflow_name(self) -> str:
#         """获取工作流名称"""
#         return "高质量文献调研综述工作流 (Enhanced Survey Workflow)"
#
#     def get_workflow_description(self) -> str:
#         """获取工作流详细描述"""
#         return """
#         ## 🎓 高质量学术综述生成工作流
#
#         **目标**: 生成符合顶级期刊标准的15,000词综述报告
#         **特色**: 四阶段系统化流程，每阶段都有明确的质量标准和交付物
#
#         ### 📋 工作流特点:
#         - **系统化**: 科学的文献调研方法论
#         - **高质量**: 严格的论文筛选和分析标准
#         - **深度性**: 每篇论文800+词深度分析
#         - **权威性**: 符合Nature/Science等顶级期刊标准
#         - **前瞻性**: 不仅总结现状，更预测未来发展
#
#         ### 🎯 预期产出:
#         - 完整的调研策略报告
#         - 25-40篇高质量论文清单
#         - 深度技术分析和趋势识别
#         - 15,000词专业HTML综述报告
#         """
#
#     def get_current_stage_context(self) -> str:
#         """获取当前阶段的详细上下文信息"""
#         if not self.user_proxy:
#             return ""
#
#         current_stage = self.user_proxy.get_current_stage()
#         if not current_stage:
#             return ""
#
#         stage_contexts = {
#             "stage_1_strategy_planning": """
# 🎯 **当前阶段**: 调研策略制定 (SurveyDirector)
#
# **正在进行的工作**:
# ✅ 深度分析您提供的研究主题
# ✅ 识别核心概念、学科边界和研究层次
# ✅ 构建50+个英文关键词的多层次体系
# ✅ 设计8个不同角度的检索查询
# ✅ 制定严格的质量控制标准
#
# **预期输出**:
# 📊 结构化的调研策略报告
# 🔍 8个精心设计的检索查询
# 📏 明确的质量标准和筛选条件
# 📋 传递给PaperRetriever的标准化指令
#
# **您的参与**:
# - 确认调研策略是否符合您的研究需求
# - 对关键词体系提供补充建议
# - 确认预期的论文数量和质量要求
#
# **下一阶段预告**: PaperRetriever将使用这些策略进行系统化检索
# """,
#             "stage_2_systematic_retrieval": """
# 🔍 **当前阶段**: 系统化论文检索 (PaperRetriever)
#
# **正在进行的工作**:
# ✅ 第1轮: 使用8个查询进行arXiv主检索
# ✅ 第2轮: Google Scholar补充检索
# ✅ 第3轮: 优化查询的深度检索
# ✅ 应用多重质量过滤标准
# ✅ 智能分类为4个主题批次
#
# **预期输出**:
# 📚 25-40篇高质量论文清单
# 📊 详细的检索统计报告
# 🗂️ 按主题分类的论文批次
# 📋 每篇论文的完整元数据
#
# **您的参与**:
# - 检查检索结果的相关性和质量
# - 确认论文数量是否符合预期
# - 对特定论文或方向提供补充要求
#
# **下一阶段预告**: PaperAnalyzer将对每篇论文进行深度分析
# """,
#             "stage_3_deep_analysis": """
# 🔬 **当前阶段**: 深度学术分析 (PaperAnalyzer)
#
# **正在进行的工作**:
# ✅ 逐篇论文的8维度深度分析
# ✅ 技术创新性和学术价值评估
# ✅ 批判性分析和局限性识别
# ✅ 提取适合综述引用的核心内容
# ✅ 批次综合分析和趋势识别
#
# **预期输出**:
# 📄 每篇论文800+词的详细分析报告
# 📊 多维度评分和排序
# 🔗 论文间关联关系分析
# 📈 技术发展趋势和模式识别
#
# **您的参与**:
# - 审核分析质量和深度
# - 对重点论文的分析重点提供指导
# - 确认评估标准的合理性
#
# **下一阶段预告**: ReportGenerator将整合为完整综述报告
# """,
#             "stage_4_comprehensive_survey": """
# 📝 **当前阶段**: 综述报告生成 (ReportGenerator)
#
# **正在进行的工作**:
# ✅ 整合所有分析结果为连贯叙述
# ✅ 撰写12个主要章节的深度内容
# ✅ 管理40+篇文献的准确引用
# ✅ 提供原创性洞察和发展预测
# ✅ 生成专业HTML格式报告
#
# **预期输出**:
# 📑 15,000词的完整学术综述
# 🎨 专业的HTML格式展示
# 🔗 完整的引用管理系统
# 📊 可视化的技术对比和趋势分析
#
# **您的参与**:
# - 最终质量审核和内容确认
# - 对特定章节内容提供调整建议
# - 确认综述的完整性和学术价值
#
# **完成标志**: 获得符合顶级期刊标准的综述报告
# """
#         }
#
#         return stage_contexts.get(current_stage.stage_id, "当前阶段信息不可用")
#
#     def get_stage_quality_metrics(self) -> dict:
#         """获取各阶段的质量评估指标"""
#         return {
#             "stage_1_strategy_planning": {
#                 "success_criteria": [
#                     "策略覆盖面广且深入",
#                     "关键词体系科学完整(50+词)",
#                     "查询设计针对性强(8个查询)",
#                     "质量标准明确可执行",
#                     "输出格式标准化"
#                 ],
#                 "deliverables": [
#                     "结构化调研策略报告",
#                     "多层次关键词体系",
#                     "8个检索查询",
#                     "质量控制标准",
#                     "后续阶段指令"
#                 ],
#                 "quality_threshold": "策略完整性 ≥ 90%"
#             },
#             "stage_2_systematic_retrieval": {
#                 "success_criteria": [
#                     "论文数量在目标范围(25-40篇)",
#                     "质量标准严格执行",
#                     "分类合理且平衡",
#                     "元数据完整准确",
#                     "去重和筛选有效"
#                 ],
#                 "deliverables": [
#                     "高质量论文清单",
#                     "检索统计报告",
#                     "主题分类批次",
#                     "完整论文元数据",
#                     "质量评估报告"
#                 ],
#                 "quality_threshold": "相关性 ≥ 85%, 引用数 ≥ 10"
#             },
#             "stage_3_deep_analysis": {
#                 "success_criteria": [
#                     "每篇论文分析深度充分(800+词)",
#                     "技术评估客观准确",
#                     "批判性分析有建设性",
#                     "引用建议具体实用",
#                     "趋势识别有洞察力"
#                 ],
#                 "deliverables": [
#                     "逐篇深度分析报告",
#                     "多维度评分矩阵",
#                     "批次综合分析",
#                     "关联关系图谱",
#                     "趋势发展分析"
#                 ],
#                 "quality_threshold": "分析深度 ≥ 8/10, 准确性 ≥ 95%"
#             },
#             "stage_4_comprehensive_survey": {
#                 "success_criteria": [
#                     "篇幅达到15,000词以上",
#                     "引用60+篇高质量文献",
#                     "技术分析深入准确",
#                     "提供原创性洞察",
#                     "格式专业且美观"
#                 ],
#                 "deliverables": [
#                     "完整HTML综述报告",
#                     "结构化引用系统",
#                     "可视化技术对比",
#                     "前瞻性发展预测",
#                     "研究建议和路线图"
#                 ],
#                 "quality_threshold": "期刊标准 ≥ 90%, 原创性 ≥ 85%"
#             }
#         }
#
#     def validate_stage_completion(self, stage_id: str, output_content: str) -> dict:
#         """验证阶段完成质量"""
#         metrics = self.get_stage_quality_metrics()
#         stage_metrics = metrics.get(stage_id, {})
#
#         validation_result = {
#             "stage_id": stage_id,
#             "is_complete": False,
#             "quality_score": 0.0,
#             "missing_elements": [],
#             "quality_assessment": "",
#             "recommendations": []
#         }
#
#         # 根据不同阶段进行特定验证
#         if stage_id == "stage_1_strategy_planning":
#             # 验证策略制定阶段
#             if "8个检索查询" in output_content or "查询" in output_content:
#                 validation_result["quality_score"] += 25
#             if "关键词" in output_content and len(output_content) > 1000:
#                 validation_result["quality_score"] += 25
#             if "质量标准" in output_content or "筛选" in output_content:
#                 validation_result["quality_score"] += 25
#             if "PaperRetriever" in output_content:
#                 validation_result["quality_score"] += 25
#
#         elif stage_id == "stage_2_systematic_retrieval":
#             # 验证检索阶段
#             if "篇" in output_content and ("25" in output_content or "30" in output_content):
#                 validation_result["quality_score"] += 30
#             if "批次" in output_content or "分类" in output_content:
#                 validation_result["quality_score"] += 25
#             if "标题" in output_content and "作者" in output_content:
#                 validation_result["quality_score"] += 25
#             if "PaperAnalyzer" in output_content:
#                 validation_result["quality_score"] += 20
#
#         elif stage_id == "stage_3_deep_analysis":
#             # 验证分析阶段
#             word_count = len(output_content.split())
#             if word_count > 2000:  # 多篇论文分析应该有足够篇幅
#                 validation_result["quality_score"] += 30
#             if "评分" in output_content or "分析" in output_content:
#                 validation_result["quality_score"] += 25
#             if "创新" in output_content and "贡献" in output_content:
#                 validation_result["quality_score"] += 25
#             if "ReportGenerator" in output_content or "综述" in output_content:
#                 validation_result["quality_score"] += 20
#
#         elif stage_id == "stage_4_comprehensive_survey":
#             # 验证综述生成阶段
#             word_count = len(output_content.split())
#             if word_count > 5000:  # HTML综述应该有大量内容
#                 validation_result["quality_score"] += 40
#             if "引用" in output_content and "参考文献" in output_content:
#                 validation_result["quality_score"] += 30
#             if "<html>" in output_content or "HTML" in output_content:
#                 validation_result["quality_score"] += 30
#
#         # 确定完成状态
#         validation_result["is_complete"] = validation_result["quality_score"] >= 75
#
#         # 生成质量评估
#         if validation_result["quality_score"] >= 90:
#             validation_result["quality_assessment"] = "优秀 - 超出预期标准"
#         elif validation_result["quality_score"] >= 80:
#             validation_result["quality_assessment"] = "良好 - 达到标准要求"
#         elif validation_result["quality_score"] >= 70:
#             validation_result["quality_assessment"] = "基本达标 - 需要小幅改进"
#         else:
#             validation_result["quality_assessment"] = "需要改进 - 未达到最低标准"
#
#         return validation_result
#
#     def get_workflow_progress_summary(self) -> str:
#         """获取工作流整体进度摘要"""
#         if not self.user_proxy:
#             return "工作流尚未开始"
#
#         current_stage = self.user_proxy.get_current_stage()
#         completed_stages = len([s for s in self.define_workflow_stages()
#                                 if s.stage_id != current_stage.stage_id]) if current_stage else 0
#         total_stages = len(self.define_workflow_stages())
#
#         progress_percentage = (completed_stages / total_stages) * 100
#
#         return f"""
# ## 📊 工作流进度概览
#
# **整体进度**: {completed_stages}/{total_stages} 阶段已完成 ({progress_percentage:.1f}%)
#
# **当前状态**: {current_stage.name if current_stage else '准备开始'}
#
# **预计完成时间**:
# - 快速模式: {4 - completed_stages} 阶段 × 5分钟 = {(4 - completed_stages) * 5}分钟
# - 深度模式: {4 - completed_stages} 阶段 × 10分钟 = {(4 - completed_stages) * 10}分钟
#
# **最终交付物预览**:
# - ✅ 调研策略报告 (已完成: {'是' if completed_stages > 0 else '否'})
# - ✅ 论文检索清单 (已完成: {'是' if completed_stages > 1 else '否'})
# - ✅ 深度分析报告 (已完成: {'是' if completed_stages > 2 else '否'})
# - ✅ 15,000词综述 (已完成: {'是' if completed_stages > 3 else '否'})
# """
#



"""
顺序交互文献调研工作流实现 - SurveyDirector → PaperRetriever → PaperSummarizer → SurveyAnalyst
修正版本：与新的base_workflow.py完全兼容
"""

from base_workflow import StagedWorkflowSession, WorkflowStage
from typing import List
import logging

logger = logging.getLogger(__name__)

class SurveyWorkflowSession(StagedWorkflowSession):
    """顺序交互文献调研工作流会话 - 完全兼容版本"""

    def define_workflow_stages(self) -> List[WorkflowStage]:
        """定义文献调研工作流的顺序执行阶段"""
        return [
            WorkflowStage(
                stage_id="stage_1_task_assignment",
                name="任务分配阶段",
                agent_name="SurveyDirector",
                description="分析研究主题，制定调研策略，分配具体任务和确定检索关键词"
            ),
            WorkflowStage(
                stage_id="stage_2_paper_retrieval",
                name="论文获取阶段",
                agent_name="PaperRetriever",
                description="根据调研策略检索相关学术论文，获取高质量文献资源"
            ),
            WorkflowStage(
                stage_id="stage_3_paper_analyst",
                name="单篇摘要阶段",
                agent_name="PaperAnalyzer",
                description="逐一分析检索到的论文，每篇论文400-500字分析"
            ),
            WorkflowStage(
                stage_id="stage_4_report_generation",
                name="综述报告阶段",
                agent_name="ReportGenerator",
                description="整合所有论文摘要，生成8000-10000词综述，生成完整的文献综述报告"
            )
        ]

    async def get_agents(self) -> List:
        """获取文献调研工作流所需的智能体 - 按执行顺序排列"""
        try:
            from agents.article_research.survey_director import get_survey_director
            from agents.article_research.paper_retriever import get_paper_retriever
            from agents.article_research.paper_analyzer import get_paper_analyzer
            from agents.article_research.report_generator import get_report_generator

            return [
                get_survey_director(),     # 第1个：论文关键词定位
                get_paper_retriever(),     # 第2个：论文批量检索
                get_paper_analyzer(),      # 第3个：论文分析
                get_report_generator()     # 第4个：生成综述
            ]
        except Exception as e:
            logger.warning(f"无法加载智能体: {e}, 使用模拟模式")
            return []  # 返回空列表，使用模拟执行

    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return "顺序交互文献调研工作流"

    def get_current_stage_context(self) -> str:
        """获取当前阶段的上下文信息"""
        if not self.user_proxy:
            return ""

        current_stage = self.user_proxy.get_current_stage()
        if not current_stage:
            return ""

        stage_contexts = {
            "stage_1_strategy_design": """
            📋 **当前阶段**: 策略制定 (SurveyDirector)

            **核心任务**:
            ✅ 分析您的研究主题
            ✅ 提取核心英文关键词
            ✅ 设计8个不同的检索查询
            ✅ 设定论文筛选标准

            **预期输出**:
            - 结构化的调研策略报告
            - 8个具体的英文检索查询  
            - 明确的质量标准
            - 给PaperRetriever的执行指令

            **您的参与**: 确认策略是否合适，提供调整建议
            """,
            "stage_2_paper_collection": """
            🔍 **当前阶段**: 论文检索 (PaperRetriever)

            **核心任务**:
            ✅ 执行8个检索查询
            ✅ 使用多个数据源检索
            ✅ 筛选30篇以上高质量论文
            ✅ 按主题分为3个批次

            **预期输出**:
            - 完整的论文清单（30+篇）
            - 每篇论文的详细信息
            - 按主题分类的批次
            - 检索统计报告

            **您的参与**: 检查论文相关性和质量
            """,
            "stage_3_content_analysis": """
            🔬 **当前阶段**: 深度分析 (PaperAnalyzer)

            **核心任务**:
            ✅ 逐篇论文深度分析（400-500字/篇）
            ✅ 提取技术方法和关键结果
            ✅ 学术价值评分（1-10分）
            ✅ 生成适合综述的引用要点

            **预期输出**:
            - 每篇论文的结构化分析
            - 批次综合分析报告
            - 技术趋势和发展脉络
            - 为综述写作准备的素材

            **您的参与**: 审核分析质量和深度
            """,
            "stage_4_survey_writing": """
            📝 **当前阶段**: 综述生成 (ReportGenerator)

            **核心任务**:
            ✅ 整合所有分析结果
            ✅ 生成8000-10000词综述
            ✅ 专业HTML格式设计
            ✅ 包含9个主要章节

            **预期输出**:
            - 完整的学术综述报告
            - 专业的HTML格式
            - 目录导航和引用系统
            - 可直接用于研究的内容

            **您的参与**: 最终质量确认
            """
        }

        return stage_contexts.get(current_stage.stage_id, "当前阶段信息不可用")