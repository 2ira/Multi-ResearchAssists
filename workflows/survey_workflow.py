"""
修改版顺序交互文献调研工作流实现 - 7阶段版本
真正集成autogen智能体执行 - 移除模拟结果
"""
from base_workflow import StagedWorkflowSession, WorkflowStage, StageStatus
from typing import List
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

class SurveyWorkflowSession(StagedWorkflowSession):
    """5阶段文献调研工作流会话 - 真正的autogen集成版本"""

    def define_workflow_stages(self) -> List[WorkflowStage]:
        """定义7阶段文献调研工作流"""
        return [
            WorkflowStage(
                stage_id="stage_1_strategy_planning",
                name="🎯 调研策略制定",
                agent_name="SurveyDirector",
                description="深度分析研究主题，制定系统化检索策略和关键词体系"
            ),
            WorkflowStage(
                stage_id="stage_2_paper_retrieval",
                name="🔍 论文检索获取",
                agent_name="PaperRetriever",
                description="多轮系统化检索，获取25-40篇高质量学术论文"
            ),
            WorkflowStage(
                stage_id="stage_3_paper_analysis",
                name="📊 深度论文分析",
                agent_name="PaperAnalyzer",
                description="逐篇深度分析，提取核心贡献和技术方法"
            ),
            WorkflowStage(
                stage_id="stage_4_knowledge_synthesis",
                name="🔗 知识综合整合",
                agent_name="KnowledgeSynthesizer",
                description="跨文献知识整合，构建统一理论框架"
            ),
            WorkflowStage(
                stage_id="stage_5_report_generation",
                name="📝 综述报告生成",
                agent_name="ReportGenerator",
                description="生成8000-10000词完整学术综述报告"
            ),
        ]

    async def get_agents(self) -> List:
        """获取真正的autogen智能体列表"""
        try:
            from agents.article_research.survey_director import get_survey_director
            from agents.article_research.paper_retriever import get_paper_retriever
            from agents.article_research.paper_analyzer import get_paper_analyzer
            from agents.article_research.knowledge_synthesizer import get_knowledge_synthesizer
            from agents.article_research.report_generator import get_report_generator


            agents = [
                get_survey_director(),         # 阶段1：策略制定
                get_paper_retriever(),         # 阶段2：论文检索
                get_paper_analyzer(),          # 阶段3：深度分析
                get_knowledge_synthesizer(),   # 阶段4：知识综合
                get_report_generator(),        # 阶段5：报告生成
            ]

            logger.info(f"✅ 成功加载 {len(agents)} 个autogen智能体")
            for i, agent in enumerate(agents):
                logger.info(f"  - 阶段{i+1}: {agent.name if hasattr(agent, 'name') else 'Unknown'}")

            return agents

        except Exception as e:
            logger.error(f"❌ 无法加载autogen智能体: {e}")
            raise e
    def get_workflow_name(self) -> str:
        """获取工作流名称"""
        return "5阶段高质量文献调研工作流"

    def get_workflow_description(self) -> str:
        """获取工作流详细描述"""
        return """
        ## 🎓 5阶段高质量学术综述生成工作流

        **目标**: 生成符合顶级期刊标准的8000-10000词综述报告
        **特色**: 5阶段系统化流程，每阶段都有专门的autogen智能体负责

        ### 📋 工作流特点:
        - **系统化**: 科学的7阶段文献调研方法论
        - **专业化**: 每个阶段都有专门的autogen智能体执行
        - **高质量**: 严格的论文筛选和分析标准
        - **可视化**: 包含交互式图表和时间线
        - **智能化**: 真正的autogen智能体协作

        ### 🎯 5阶段流程:
        1. 🎯 调研策略制定 (SurveyDirector)
        2. 🔍 论文检索获取 (PaperRetriever)  
        3. 📊 深度论文分析 (PaperAnalyzer)
        4. 🔗 知识综合整合 (KnowledgeSynthesizer)
        5. 📝 综述报告生成 (ReportGenerator)
        """

    def get_current_stage_context(self) -> str:
        """获取当前阶段的详细上下文信息"""
        if not self.user_proxy:
            return ""

        current_stage = self.user_proxy.get_current_stage()
        if not current_stage:
            return ""

        stage_contexts = {
            "stage_1_strategy_planning": """
            🎯 **当前阶段**: 调研策略制定 (SurveyDirector)
            
            **正在进行的工作**:
            ✅ 深度分析您提供的研究主题
            ✅ 识别核心概念、学科边界和研究层次
            ✅ 构建多层次英文关键词体系
            ✅ 设计8个不同角度的检索查询
            ✅ 制定严格的质量控制标准
            
            **预期输出**:
            📊 结构化的调研策略报告
            🔍 8个精心设计的检索查询
            📏 明确的质量标准和筛选条件
            
            **下一阶段**: PaperRetriever将执行系统化检索
            """,

            "stage_2_paper_retrieval": """
            🔍 **当前阶段**: 论文检索获取 (PaperRetriever)
            
            **正在进行的工作**:
            ✅ 执行8个主查询的多源检索
            ✅ 应用质量过滤标准
            ✅ 智能去重和筛选
            ✅ 按主题分类为批次
            
            **预期输出**:
            📚 25-40篇高质量论文清单
            📊 详细的检索统计报告
            🗂️ 按主题分类的论文批次
            
            **下一阶段**: PaperAnalyzer将进行深度分析
            """,

            "stage_3_paper_analysis": """
            📊 **当前阶段**: 深度论文分析 (PaperAnalyzer)
            
            **正在进行的工作**:
            ✅ 逐篇论文的多维度深度分析
            ✅ 技术创新性和学术价值评估
            ✅ 提取适合综述引用的核心内容
            ✅ 识别论文间关联关系
            
            **预期输出**:
            📄 每篇论文的详细分析报告
            📊 多维度评分和排序
            🔗 论文间关联关系分析
            
            **下一阶段**: KnowledgeSynthesizer将整合知识
            """,

            "stage_4_knowledge_synthesis": """
            🔗 **当前阶段**: 知识综合整合 (KnowledgeSynthesizer)
            
            **正在进行的工作**:
            ✅ 跨文献知识抽象和整合
            ✅ 构建统一的理论框架
            ✅ 识别技术发展趋势和模式
            ✅ 发现研究空白和机遇
            
            **预期输出**:
            🏗️ 统一的知识分类体系
            📈 技术发展脉络和趋势
            🎯 研究空白和未来方向
            
            **下一阶段**: ReportGenerator将生成最终报告
            """,

            "stage_5_report_generation": """
            📝 **当前阶段**: 综述报告生成 (ReportGenerator)
            
            **正在进行的工作**:
            ✅ 整合所有前期分析结果
            ✅ 撰写8000-10000词完整综述
            ✅ 集成可视化内容和引用
            ✅ 生成专业HTML格式报告
            
            **预期输出**:
            📑 完整的学术综述报告
            🎨 专业的HTML格式
            📊 集成的可视化展示
            
            **完成标志**: 获得高质量学术综述认证
            """
        }

        return stage_contexts.get(current_stage.stage_id, "当前阶段信息不可用")