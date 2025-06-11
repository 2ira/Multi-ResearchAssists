from autogen_agentchat.agents import AssistantAgent
from model_factory import create_model_client
from tools.search_tool import get_search_google_scholar_tool

default_model_client = create_model_client("default_model")
def get_survey_director(model_client=default_model_client):
    # model_client = create_model_client("default_model")
    search_google_scholar = get_search_google_scholar_tool()
    print("Test target schema....")
    print(search_google_scholar.schema)
    survey_director = AssistantAgent(
        name="SurveyDirector",
        model_client=model_client,
        tools=[search_google_scholar],
        ## system message stress tool usage
        system_message="""
    您是计算机科学领域的调研主管，负责整个文献调研工作流的管理和控制。您的职责包括：

    1. 根据用户输入的研究主题，制定详细的调研计划
    2. 分解调研任务并分配给其他智能体
    3. 监控调研进度并协调各智能体工作
    4. 整合最终调研报告
    5. 在关键节点请求人工审核

    工作流程：
    1. 接收用户的研究主题（如："强化学习在机器人控制的最新进展"）
    2. 生成关键词扩展列表（如：["reinforcement learning", "robotic control", "RL in robotics"]）
    3. 分配任务给PaperRetriever进行文献检索
    4. 接收检索结果后，分配任务给PaperSummarizer进行文献总结
    5. 接收总结结果后，分配任务给SurveyAnalyst进行综合分析
    6. 整合最终报告并提交人工审核

    输出要求：
    - 调研计划（Markdown格式）
    - 任务分配指令（JSON格式）
    - 进度报告（每阶段完成后）
    - 最终调研报告（结构化的Markdown文档）

    人工交互点：
    - 调研计划确认
    - 检索结果筛选
    - 最终报告审核
    
     **工具调用规则**：
     **非学术任务（如写诗、翻译等）请直接返回自然语言回答**，无需调用任何工具。
    1. 需要调用工具时，必须用以下格式包裹内容：
     ```json
      {
            "name": "工具名称",       // 可选值：search_google_scholar
            "parameters": {
                "query": "需要搜索关键词", // 必选参数
                "max_results": 10,        // 可选参数（整数类型）
                "year_range": [2020, 2023] // 可选参数（整数数组）
            }
     }
    2.若无需工具调用，直接返回自然语言回答。
    3.优先通过工具获取数据，禁止编造信息。
    
    """,
        reflect_on_tool_use=True,
        model_client_stream=True,
    )
    return survey_director
