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

## 任务：
对每篇论文提取：问题、方法、结果、贡献四个要素，然后进行批次综合。

## 输出格式：
```
## 批次分析：{批次主题}

### 论文1：{标题}
- **问题**：{要解决的核心问题，1句话}
- **方法**：{核心技术方法，2-3句话}
- **结果**：{主要性能结果，1-2句话}  
- **贡献**：{主要学术贡献，2-3个要点}

### 论文2：{标题}
[同上格式]

## 批次综合：
- **技术趋势**：{共同的技术方向}
- **性能水平**：{整体性能表现}
- **主要局限**：{存在的问题}
- **引用要点**：{适合综述引用的3-5个关键发现}
```

## 要求：
- 每篇论文分析控制在100字内
- 专注提取事实性信息，避免主观评价
- 如论文信息不足可使用搜索工具补充
- 重点关注可量化的结果和具体的技术贡献

开始分析！
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return analyzer
