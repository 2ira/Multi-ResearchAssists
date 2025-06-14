import unittest
from dotenv import load_dotenv
import os
# 加载环境变量
load_dotenv()
# 假设这些函数定义在search_tools.py中
from search_tool import search_arxiv, search_semantic_scholar, search_google_scholar
import asyncio
class TestSearchTools(unittest.TestCase):

    def setUp(self):
        self.query = "machine learning"
        self.max_results = 5
        self.year_range = (2020, 2023)

    def test_arxiv_search(self):
        ## 同步调用异步函数

        results = asyncio.run(search_arxiv(query="machine learning"))
        print("Enter arxiv...")
        print(results)
        self.assertEqual(results["source"], "arXiv")
        papers = results["papers"]

        # 验证返回字段和年份范围
        for paper in papers:
            self.assertIn("title", paper)
            self.assertIn("year", paper)
            self.assertGreaterEqual(paper["year"], self.year_range[0])
            self.assertLessEqual(paper["year"], self.year_range[1])

    # 这里的semantic api还没有得到
    @unittest.skipIf(os.getenv("SEMANTIC_SCHOLAR_API_KEY") is None, "Semantic Scholar API key not set")
    def test_semantic_scholar_search(self):
        results = search_semantic_scholar(self.query)
        self.assertEqual(results["source"], "Semantic Scholar")
        papers = results["papers"]
        print("Enter semantic scholar...")
        print(results)

        # valid return name
        self.assertLessEqual(len(papers), self.max_results)

        # valid segment
        for paper in papers:
            self.assertIn("title", paper)
            self.assertIn("year", paper)
            self.assertIn("citation_count", paper)
            if paper["year"] is not None:
                self.assertGreaterEqual(paper["year"], self.year_range[0])
                self.assertLessEqual(paper["year"], self.year_range[1])

    @unittest.skipIf(os.getenv("SERPER_API_KEY") is None, "Serper API key not set")
    def test_google_scholar_search(self):
        results = asyncio.run(search_google_scholar(self.query))
        print("Enter serper...")
        print(results)
        self.assertEqual(results["source"], "Google Scholar")
        papers = results["papers"]

        # 验证返回数量
        self.assertLessEqual(len(papers), self.max_results)

        # 验证返回字段
        for paper in papers:
            self.assertIn("title", paper)
            self.assertIn("year", paper)
            # 由于年份提取不可靠，这里不验证年份范围


if __name__ == '__main__':
    unittest.main()