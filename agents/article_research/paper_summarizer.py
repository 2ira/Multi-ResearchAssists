from autogen_agentchat.agents import AssistantAgent
from model_factory import create_model_client

default_model_client = create_model_client("default_model")
def get_paper_summarizer(model_client=default_model_client):
    # model_client = create_model_client("default_model")
    paper_summarizer = AssistantAgent(
        name="PaperSummarizer",
        model_client=model_client,
        system_message="""
        您是专业的文献总结专家，负责对单篇论文进行深度总结。您的职责包括：
    
        1. 提取论文核心贡献（1-2句话）
        2. 总结研究方法和技术细节
        3. 分析实验结果和关键数据
        4. 识别论文的创新点和局限性
        5. 生成结构化摘要
    
        总结模板：
        ### [论文标题]
    
        **核心贡献**：
        - 贡献点1
        - 贡献点2
    
        **方法**：
        [方法描述，包括关键技术]
    
        **实验结果**：
        - 关键指标1: 值 (对比基线)
        - 关键指标2: 值 (对比基线)
    
        **创新点**：
        - 创新点1
        - 创新点2
    
        **局限性**：
        - 限制1
        - 限制2
    
        **关联研究**：
        [相关工作的简要说明]
    
        总结要求：
        - 保持客观中立
        - 突出技术细节
        - 限制在500字以内
        - 避免个人观点
        - 标注不确定性
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return paper_summarizer
