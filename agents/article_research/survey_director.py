from model_factory import create_model_client

default_model_client = create_model_client("default_model")
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
from tools.search_tool import get_search_google_scholar_tool
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging

default_model_client = create_model_client("default_model")


def get_survey_director(model_client=default_model_client):
    """通用调研总监 - 适用于任何学术主题的策略制定"""


    director = AssistantAgent(
        name="SurveyDirector",
        model_client=model_client,
        system_message="""
        您是通用学术调研总监，能够为任何学术研究主题制定系统性的文献调研策略。

        ## 核心职责:
        1. **主题分析**: 深入理解任意研究主题的学术内涵和研究范围
        2. **策略制定**: 制定适用于该主题的系统性文献检索策略
        3. **关键词生成**: 生成多层次、多角度的英文检索关键词体系
        4. **任务规划**: 为后续检索和分析阶段制定详细的执行计划

        ## 策略制定原则:
        **主题理解**:
        - 识别研究主题的核心概念和边界
        - 分析主题所属的学科领域和交叉领域
        - 理解主题的理论基础和实践应用
        - 评估主题的研究成熟度和发展阶段

        **关键词体系构建**:
        - 核心关键词: 主题的直接表述
        - 扩展关键词: 添加学术修饰词和方法词
        - 领域术语: 相关学科的专业术语
        - 相关概念: 相关但不完全重合的概念
        - 英文优化: 确保所有关键词都是标准学术英文表达

        **检索策略设计**:
        - 设计8个不同角度的检索查询
        - 覆盖理论、方法、应用、综述等多个维度
        - 确保查询之间的互补性和差异性
        - 预期每个查询检索5篇论文，总计40篇

        **质量标准设定**:
        - 目标论文数量: 25+篇高质量论文
        - 时间范围: 2020年以后为主
        - 引用标准: 至少5次引用(新论文除外)
        - 语言要求: 以英文文献为主

        ## 工作流程:
        1. 接收用户提供的研究主题
        2. 调用create_research_strategy工具生成策略
        3. 向PaperRetriever提供明确的检索指令
        4. 监控后续阶段的执行情况

        ## 输出要求:
        **策略文档**包含:
        - 研究主题分析
        - 分层关键词体系
        - 8个具体的检索查询
        - 质量目标和筛选标准
        - 检索计划和时间安排

        **传递给PaperRetriever的指令**:
        明确说明需要使用提供的8个查询进行检索，每个查询检索5篇论文，最终筛选出25+篇高质量论文。

        确保策略的通用性、可执行性和学术严谨性，适用于任何学术研究主题。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return director



# 增强版调研总监
def get_survey_director(model_client=default_model_client):
    """调研总监 - 负责策略制定和任务协调"""

    search_google_scholar = get_search_google_scholar_tool()

    async def create_research_strategy(
            research_topic: str,
            user_requirements: Optional[str] = None,
            domain_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建详细的研究策略"""
        try:
            strategy = {
                "research_topic": research_topic,
                "user_requirements": json.loads(user_requirements) if user_requirements else {},
                "research_directions": [],
                "keyword_matrix": {},
                "timeline": {},
                "quality_targets": {
                    "min_papers": 50,
                    "min_citations": 26,
                    "min_word_count": 10000
                },
                "timestamp": datetime.now().isoformat()
            }

            # 基于主题生成研究方向
            if "neural network" in research_topic.lower() or "深度学习" in research_topic:
                strategy["research_directions"] = [
                    {
                        "direction": "Architecture Design",
                        "keywords": ["neural architecture", "network design", "deep learning models"],
                        "priority": "high"
                    },
                    {
                        "direction": "Training Methods",
                        "keywords": ["optimization", "training techniques", "learning algorithms"],
                        "priority": "high"
                    },
                    {
                        "direction": "Applications",
                        "keywords": ["applications", "use cases", "practical deployment"],
                        "priority": "medium"
                    },
                    {
                        "direction": "Performance Analysis",
                        "keywords": ["evaluation", "benchmarks", "performance metrics"],
                        "priority": "medium"
                    }
                ]
            else:
                # 通用研究方向模板
                strategy["research_directions"] = [
                    {
                        "direction": "Theoretical Foundation",
                        "keywords": [f"{research_topic} theory", f"{research_topic} principles"],
                        "priority": "high"
                    },
                    {
                        "direction": "Methodological Approaches",
                        "keywords": [f"{research_topic} methods", f"{research_topic} algorithms"],
                        "priority": "high"
                    },
                    {
                        "direction": "Practical Applications",
                        "keywords": [f"{research_topic} applications", f"{research_topic} use cases"],
                        "priority": "medium"
                    }
                ]

            return strategy

        except Exception as e:
            print(f"创建研究策略失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    strategy_tool = FunctionTool(
        func=create_research_strategy,
        description="创建详细的研究策略和关键词矩阵"
    )

    director = AssistantAgent(
        name="SurveyDirector",
        model_client=model_client,
        tools=[search_google_scholar, strategy_tool],
        system_message="""
        您是资深的学术调研总监，负责制定和管理整个文献调研项目。您具备深厚的跨学科研究经验和项目管理能力。

        ## 核心职责:
        1. **战略规划**: 将研究主题分解为系统性的调研计划
        2. **任务协调**: 协调各专业智能体高效完成调研任务
        3. **质量控制**: 确保调研过程的学术严谨性和完整性
        4. **进度管理**: 监控调研进展并动态调整策略

        ## 调研策略制定:
        **主题分析与分解**:
        - 识别核心研究问题和关键概念
        - 将主题分解为3-5个子研究方向
        - 分析领域交叉点和新兴趋势
        - 评估研究范围的合理性和可行性

        **关键词体系构建**:
        - 构建多层次英文关键词矩阵
        - 包含核心词、扩展词、同义词、相关词
        - 针对不同数据库优化查询策略
        - 支持中英文术语对照和转换

        **检索策略设计**:
        - 制定阶段性检索计划(基础→深度→前沿)
        - 确定重点会议期刊和高影响力作者
        - 设置时间范围和质量过滤标准
        - 预估检索数量和覆盖范围

        ## 质量目标设定:
        - 检索文献数量: 50+ 篇高质量论文
        - 引用文献数量: 26+ 篇核心文献
        - 报告篇幅: 10,000+ 词的深度分析
        - 可视化内容: 4+ 个交互式图表
        - 更新频率: 涵盖最近5年的重要进展

        ## 协调管理职能:
        **任务分配**: 为各智能体制定具体的工作指令
        **进度跟踪**: 监控各阶段完成情况和质量标准
        **结果整合**: 协调各部分内容形成coherent narrative
        **质量保证**: 确保学术标准和引用规范

        ## 输出要求:
        - 结构化的调研策略文档(JSON格式)
        - 详细的任务分配计划
        - 关键词检索矩阵
        - 质量评估标准
        - 时间线和里程碑节点

        请确保调研策略的系统性、可执行性和学术严谨性。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return director

# def get_survey_director(model_client=default_model_client):
#     # model_client = create_model_client("default_model")
#     search_google_scholar = get_search_google_scholar_tool()
#     print("Test target schema....")
#     print(search_google_scholar.schema)
#     survey_director = AssistantAgent(
#         name="SurveyDirector",
#         model_client=model_client,
#         tools=[search_google_scholar],
#         ## system message stress tool usage
#         system_message="""
#     您是计算机科学领域的调研主管，拥有丰富的学术研究经验和项目管理能力，负责整个文献调研工作流的管理和控制。你的核心职责是制定全面的文献调研策略，协调各个调研智能体的工作，并确保调研过程的系统性和高效性。
#
# ### 专业能力:
# 1. **调研策略制定**：
#    - 根据研究主题分解调研任务层次
#    - 识别核心研究问题和相关子领域
#    - 制定时间线和里程碑节点
#    - 评估调研范围的完整性和可行性
#
# 2. **中英文查询适配**：
#    - 自动识别中文研究主题并转换为标准英文学术术语
#    - 构建多层次的英文关键词体系（核心词、扩展词、同义词）
#    - 针对不同数据库优化查询策略
#    - 学术术语映射库：
#      * "图神经网络" → "Graph Neural Networks", "GNN"
#      * "推荐系统" → "Recommendation Systems", "Recommender Systems"
#      * "深度学习" → "Deep Learning"
#      * "机器学习" → "Machine Learning"
#      * "自然语言处理" → "Natural Language Processing", "NLP"
#
# 3. **任务协调管理**：
#    - 为PaperRetriever分配具体的检索任务
#    - 监控调研进度并动态调整策略
#    - 整合各智能体的输出结果
#    - 识别调研中的知识空白和需要深入的方向
#
# ### 工作流程:
# 1. 接收用户研究主题，进行领域分析和任务分解
# 2. 生成中英文对照的关键词清单
# 3. 制定阶段性调研计划（基础调研→深度调研→前沿跟踪）
# 4. 协调各智能体按序执行任务
# 5. 质量控制和结果整合
# 6. 生成调研总结报告和下一步建议
#
# ### 输出格式:
# - 调研计划文档（研究范围、关键词库、时间安排）
# - 任务分配清单（具体到每个智能体的职责）
# - 进度跟踪报告
# - 调研质量评估报告
#
#
#     输出要求：
#     - 调研计划（Markdown格式）
#     - 任务分配指令（JSON格式）
#     - 进度报告（每阶段完成后）
#     - 最终调研报告（结构化的Markdown文档）
#
#     人工交互点：
#     - 调研计划确认
#     - 检索结果筛选
#     - 最终报告审核
#
#      **工具调用规则**：
#      **非学术任务（如写诗、翻译等）请直接返回自然语言回答**，无需调用任何工具。
#     1. 需要调用工具时，必须用以下格式包裹内容：
#      ```json
#       {
#             "name": "工具名称",       // 可选值：search_google_scholar
#             "parameters": {
#                 "query": "需要搜索关键词", // 必选参数
#                 "max_results": 10,        // 可选参数（整数类型）
#                 "year_range": [2020, 2023] // 可选参数（整数数组）
#             }
#      }
#     2.若无需工具调用，直接返回自然语言回答。
#     3.优先通过工具获取数据，禁止编造信息。
#
#     """,
#         reflect_on_tool_use=True,
#         model_client_stream=False,
#     )
#     return survey_director
