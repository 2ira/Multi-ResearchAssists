from typing import Optional, Dict, Any, Tuple
import arxiv
import requests
import os
import http.client
import json
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
import re
from autogen_core.tools import FunctionTool

def get_arxiv_tool():
    return FunctionTool(
        func=search_arxiv,
        description="Search for papers on arXiv",
        strict=True,
    )
def get_semantic_scholar_tool():
    return FunctionTool(
        func=search_semantic_scholar,
        description="Search for papers on semantic scholar",
        strict=True,
    )
def get_search_google_scholar_tool():
    return FunctionTool(
        func=search_google_scholar,
        description="Search for papers on google",
        strict=True
    )


# arXiv检索工具
load_dotenv()

"""
{
    "name": "工具名称",       // 可选值：search_arxiv
    "parameters": {
        "query": "研究主题关键词", // 必选参数
        "max_results": 5
    }
}
"""


async def search_arxiv(
        query: str,

) -> Dict[str, Any]:
    """
    Search arXiv papers by query.

    Args:
        query: Search query string
        max_results: Maximum number of results to return，default 5.coding format

    Returns:
        Dictionary containing search results
    """
    print(f"📚 调用arXiv工具: query={query}")

    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = []
        for paper in client.results(search):

            results.append({
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "abstract": paper.summary[:500] + "..." if len(paper.summary) > 500 else paper.summary,  # 限制摘要长度
                "year": paper.published.year,
                "citation_count": None,
                "pdf_url": paper.pdf_url,
                "source_url": paper.entry_id,
                "source": "arXiv"
            })

        print(f"✅ arXiv搜索完成，找到 {len(results)} 篇论文")
        return {"source": "arXiv", "papers": results, "total_count": len(results)}

    except Exception as e:
        print(f"❌ arXiv搜索出错: {e}")
        return {"source": "arXiv", "papers": [], "error": str(e)}

# Semantic Scholar检索工具

"""
Sementic Schoolar is Allen Institute for AI 的免费搜索引擎，
结合人工智能以及自然语言处理，提供高质量的学术学术文献检索，如果要使用api，需要申请api key
Academic Graph API
Recommendations API
Datasets API
使用自定义训练排名器，完成论文相关行搜索和论文批量【这个更加不耗费时间】搜索终端节点

我已经提交申请，但是估计通过要等一段时间
"""

"""
{
    "name": "工具名称",       // 可选值：search_semantic_scholar
    "parameters": {
        "query": "研究主题关键词", // 必选参数
        "max_results": 10,        // 可选参数（整数类型）
        "year_range": [2020, 2023] // 可选参数（整数数组）
    }
}
"""
async def search_semantic_scholar(
        query: str,
)->dict:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    max_results = 5
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,abstract,year,citationCount,url,pdfUrls"
    }

    headers = {
        "x-api-key": os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    } if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else {}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    papers = []
    for item in data.get("data", []):
        papers.append({
            "title": item.get("title", ""),
            "authors": [author["name"] for author in item.get("authors", [])],
            "abstract": item.get("abstract", ""),
            "year": item.get("year"),
            "citation_count": item.get("citationCount", 0),
            "pdf_url": item.get("pdfUrls", [""])[0] if item.get("pdfUrls") else "",
            "source_url": item.get("url", ""),
            "source": "Semantic Scholar"
        })
    return {"source": "Semantic Scholar", "papers": papers}


"""
serper是google一个快速响应平台
import http.client
import json

conn = http.client.HTTPSConnection("google.serper.dev")
payload = json.dumps({
  "q": "apple inc"
})
headers = {
  'X-API-KEY': '48b9aa9bf889cd6031dae46b74f9a9930558c35e',
  'Content-Type': 'application/json'
}
conn.request("POST", "/search", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

"""


# Google Scholar检索工具
"""
{
    "name": "工具名称",       // 可选值：search_google_scholar
    "parameters": {
        "query": "需要搜索关键词", // 必选参数
    }
}
"""
async def search_google_scholar(
        query: str,
)->dict:
    serper = GoogleSerperAPIWrapper()
    results = serper.results(query)
    max_results = 5

    papers = []
    for item in results.get("organic", [])[:max_results]:
        # 提取年份信息
        year_match = re.search(r'(\d{4})', item.get("snippet", ""))
        year = int(year_match.group(1)) if year_match else None
        papers.append({
            "title": item.get("title", ""),
            "authors": [],  # Google Scholar不直接提供作者列表
            "abstract": item.get("snippet", ""),
            "year": year,
            "citation_count": None,  # 需要额外解析
            "pdf_url": "",
            "source_url": item.get("link", ""),
            "source": "Google Scholar"
        })
    return {"source": "Google Scholar", "papers": papers}
