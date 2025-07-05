from model_factory import create_model_client
import logging
logger = logging.getLogger(__name__)
default_model_client = create_model_client("default_model")
from autogen_agentchat.agents import AssistantAgent
from model_factory import create_model_client
from tools.search_tool import get_search_google_scholar_tool, get_arxiv_tool

default_model_client = create_model_client("default_model")

def get_paper_analyzer(model_client=default_model_client):
    """高效论文分析专家 - 提取核心内容用于综述"""

    search_google_scholar = get_search_google_scholar_tool()
    search_arxiv = get_arxiv_tool()

    analyzer = AssistantAgent(
        name="PaperAnalyzer",
        model_client=model_client,
        tools=[search_google_scholar, search_arxiv],
        system_message="""
你是论文分析专家。接收论文批次，提取核心信息用于综述写作。
你需要将上一轮检索得到的25篇文章每一个都完成分析，并且按照下面格式严格规范输出
论文 1：{标题}
问题：{核心科学问题，2-4句}
方法：{核心技术 / 模型架构 / 实验设计，3-5 句内}
实验与结果：{数据集、关键指标（如准确率提升 X%）、对比结论，2 句内}
贡献与局限：{2-3 个创新点 + 1 个主要局限，分点}
论文 2：{标题}
[同上格式]
plaintext
论文 3:

## 要求
1. 每篇分析尽量控制在600字内，用领域术语
2. 数据优先：突出量化结果（如F1=92.3%，超基线5.7%）
3. 工具仅用于补充缺失的关键数据（如数据集规模）
4. 避免重复，凸显每篇独特性

如果缺少相关论文信息可以调用工具search_google_scholar或者search_arxiv获得额外信息。
每一轮尽可能多给出论文分析，最好超过10篇文章分析结果输出，如果一次性无法输出25篇内容可以先生成一半内容，提示用户论文未分析完毕，并且当用户说“继续”的时候分析另外一半内容。

开始分析！
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return analyzer
