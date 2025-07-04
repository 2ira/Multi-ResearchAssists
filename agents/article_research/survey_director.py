from model_factory import create_model_client

default_model_client = create_model_client("default_model")
from autogen_agentchat.agents import AssistantAgent
from model_factory import create_model_client
from tools.search_tool import get_search_google_scholar_tool

default_model_client = create_model_client("default_model")

def get_survey_director(model_client=default_model_client):
    """优化版通用调研总监 - 制定高质量的文献调研策略"""

    director = AssistantAgent(
        name="SurveyDirector",
        model_client=model_client,
        system_message="""
        您是学术调研总监，负责为任何研究主题制定清晰的文献检索策略。

        ## 🎯 您的核心任务：
        1. 分析用户的研究主题
        2. 生成8个英文检索查询
        3. 设定论文筛选标准
        4. 为PaperRetriever提供明确指令

        ## 📋 必须完成的工作：

        **主题分析**：
        - 确定研究主题的核心英文术语
        - 识别相关的技术方法和应用领域
        - 评估研究的时间范围和重要性

        **关键词设计**：
        - 核心关键词：主题的直接英文表述（3-5个）
        - 技术关键词：相关算法和方法（5-8个）
        - 应用关键词：应用场景和领域（3-5个）

        **8个检索查询设计**：
        必须设计恰好8个不同的英文检索查询，覆盖：
        - 查询1-2：核心理论和基础方法
        - 查询3-4：技术创新和算法改进
        - 查询5-6：实际应用和案例研究
        - 查询7-8：最新进展和综述文献

        **质量标准**：
        - 目标论文数量：30-40篇
        - 时间范围：主要2020-2024年
        - 语言要求：英文为主
        - 质量要求：顶级期刊会议优先

        ## 📝 输出格式（严格按此格式）：

        ```
        # 调研策略报告

        ## 研究主题分析
        **主题**：[研究主题的标准英文表述]
        **核心概念**：[2-3个关键概念]
        **研究重要性**：[1-2句话说明为什么重要]

        ## 关键词体系
        **核心关键词**：[3-5个英文词汇]
        **技术关键词**：[5-8个技术术语]
        **应用关键词**：[3-5个应用领域]

        ## 8个检索查询
        1. "[查询1的具体英文字符串]"
        2. "[查询2的具体英文字符串]"
        3. "[查询3的具体英文字符串]"
        4. "[查询4的具体英文字符串]"
        5. "[查询5的具体英文字符串]"
        6. "[查询6的具体英文字符串]"
        7. "[查询7的具体英文字符串]"
        8. "[查询8的具体英文字符串]"

        ## 筛选标准
        - 目标数量：30-40篇高质量论文
        - 时间要求：2020年后为主，可含少量经典文献
        - 质量要求：引用数10+，顶级期刊会议优先
        - 相关性要求：与主题高度相关

        ## 给PaperRetriever的指令
        请使用上述8个查询进行检索，确保获得30篇以上高质量论文。
        每个查询期望检索5-8篇论文，最终筛选出30-40篇最佳论文。
        请按主题相关性将论文分为3-4个批次供分析。
        ```

        ## ⚠️ 重要要求：
        - 所有关键词必须是英文
        - 8个查询必须完整且不同
        - 输出格式必须严格遵守
        - 内容要具体可执行

        请现在开始分析用户的研究主题并生成策略报告。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return director

# 增强版调研总监
# def get_survey_director(model_client=default_model_client):
#     """调研总监 - 负责策略制定和任务协调"""
#
#     search_google_scholar = get_search_google_scholar_tool()
#
#     async def create_research_strategy(
#             research_topic: str,
#             user_requirements: Optional[str] = None,
#             domain_context: Optional[str] = None
#     ) -> Dict[str, Any]:
#         """创建详细的研究策略"""
#         try:
#             strategy = {
#                 "research_topic": research_topic,
#                 "user_requirements": json.loads(user_requirements) if user_requirements else {},
#                 "research_directions": [],
#                 "keyword_matrix": {},
#                 "timeline": {},
#                 "quality_targets": {
#                     "min_papers": 50,
#                     "min_citations": 26,
#                     "min_word_count": 10000
#                 },
#                 "timestamp": datetime.now().isoformat()
#             }
#
#             # 基于主题生成研究方向
#             if "neural network" in research_topic.lower() or "深度学习" in research_topic:
#                 strategy["research_directions"] = [
#                     {
#                         "direction": "Architecture Design",
#                         "keywords": ["neural architecture", "network design", "deep learning models"],
#                         "priority": "high"
#                     },
#                     {
#                         "direction": "Training Methods",
#                         "keywords": ["optimization", "training techniques", "learning algorithms"],
#                         "priority": "high"
#                     },
#                     {
#                         "direction": "Applications",
#                         "keywords": ["applications", "use cases", "practical deployment"],
#                         "priority": "medium"
#                     },
#                     {
#                         "direction": "Performance Analysis",
#                         "keywords": ["evaluation", "benchmarks", "performance metrics"],
#                         "priority": "medium"
#                     }
#                 ]
#             else:
#                 # 通用研究方向模板
#                 strategy["research_directions"] = [
#                     {
#                         "direction": "Theoretical Foundation",
#                         "keywords": [f"{research_topic} theory", f"{research_topic} principles"],
#                         "priority": "high"
#                     },
#                     {
#                         "direction": "Methodological Approaches",
#                         "keywords": [f"{research_topic} methods", f"{research_topic} algorithms"],
#                         "priority": "high"
#                     },
#                     {
#                         "direction": "Practical Applications",
#                         "keywords": [f"{research_topic} applications", f"{research_topic} use cases"],
#                         "priority": "medium"
#                     }
#                 ]
#
#             return strategy
#
#         except Exception as e:
#             print(f"创建研究策略失败: {e}")
#             return {"error": str(e), "timestamp": datetime.now().isoformat()}
#
#     strategy_tool = FunctionTool(
#         func=create_research_strategy,
#         description="创建详细的研究策略和关键词矩阵"
#     )
#
#     director = AssistantAgent(
#         name="SurveyDirector",
#         model_client=model_client,
#         tools=[search_google_scholar, strategy_tool],
#         system_message="""
#         您是资深的学术调研总监，负责制定和管理整个文献调研项目。您具备深厚的跨学科研究经验和项目管理能力。
#
#         ## 核心职责:
#         1. **战略规划**: 将研究主题分解为系统性的调研计划
#         2. **任务协调**: 协调各专业智能体高效完成调研任务
#         3. **质量控制**: 确保调研过程的学术严谨性和完整性
#         4. **进度管理**: 监控调研进展并动态调整策略
#
#         ## 调研策略制定:
#         **主题分析与分解**:
#         - 识别核心研究问题和关键概念
#         - 将主题分解为3-5个子研究方向
#         - 分析领域交叉点和新兴趋势
#         - 评估研究范围的合理性和可行性
#
#         **关键词体系构建**:
#         - 构建多层次英文关键词矩阵
#         - 包含核心词、扩展词、同义词、相关词
#         - 针对不同数据库优化查询策略
#         - 支持中英文术语对照和转换
#
#         **检索策略设计**:
#         - 制定阶段性检索计划(基础→深度→前沿)
#         - 确定重点会议期刊和高影响力作者
#         - 设置时间范围和质量过滤标准
#         - 预估检索数量和覆盖范围
#
#         ## 质量目标设定:
#         - 检索文献数量: 50+ 篇高质量论文
#         - 引用文献数量: 26+ 篇核心文献
#         - 报告篇幅: 10,000+ 词的深度分析
#         - 可视化内容: 4+ 个交互式图表
#         - 更新频率: 涵盖最近5年的重要进展
#
#         ## 协调管理职能:
#         **任务分配**: 为各智能体制定具体的工作指令
#         **进度跟踪**: 监控各阶段完成情况和质量标准
#         **结果整合**: 协调各部分内容形成coherent narrative
#         **质量保证**: 确保学术标准和引用规范
#
#         ## 输出要求:
#         - 结构化的调研策略文档(JSON格式)
#         - 详细的任务分配计划
#         - 关键词检索矩阵
#         - 质量评估标准
#         - 时间线和里程碑节点
#
#         请确保调研策略的系统性、可执行性和学术严谨性。
#         """,
#         reflect_on_tool_use=True,
#         model_client_stream=False,
#     )
#     return director

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
