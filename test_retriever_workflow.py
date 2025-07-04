#!/usr/bin/env python3
"""
完整的文献调研工作流测试脚本
展示三个核心角色的协同工作流程
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# 导入AutoGen组件
try:
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.agents import UserProxyAgent
    from autogen_agentchat.conditions import TextMentionTermination
    from autogen_agentchat.ui import Console

    AUTOGEN_IMPORTED = True
    print("✅ 成功导入AutoGen组件")
except ImportError as e:
    print(f"❌ 导入AutoGen组件失败: {e}")
    AUTOGEN_IMPORTED = False

# 导入通用智能体
try:
    from agents.article_research.survey_director import get_survey_director
    from agents.article_research.paper_retriever import get_paper_retriever
    from agents.article_research.paper_analyzer import get_paper_analyzer

    AGENTS_IMPORTED = True
    print("✅ 成功导入通用智能体模块")
except ImportError as e:
    print(f"❌ 导入智能体失败: {e}")
    AGENTS_IMPORTED = False


class CompleteWorkflowTester:
    """完整工作流测试器"""

    def __init__(self):
        self.output_dir = Path("workflow_outputs")
        self.output_dir.mkdir(exist_ok=True)
        self.conversation_history = []
        self.retrieved_papers = []  # 存储检索到的论文
        self.analysis_results = []  # 存储分析结果

    def _auto_input(self):
        """自动输入函数"""
        return "继续"

    async def test_complete_workflow(self, research_topic: str):
        """测试完整的三阶段工作流"""
        print(f"\n🎯 开始完整工作流测试")
        print(f"研究主题: {research_topic}")
        print("=" * 80)

        if not AUTOGEN_IMPORTED or not AGENTS_IMPORTED:
            print("❌ 缺少必要的依赖模块")
            return False

        try:
            # 初始化三个核心智能体
            survey_director = get_survey_director()
            paper_retriever = get_paper_retriever()
            paper_analyzer = get_paper_analyzer()

            print("✅ 智能体初始化完成")

            # 阶段1: 调研策略制定
            print("\n📋 阶段1: 调研策略制定")
            print("-" * 60)

            user_proxy = UserProxyAgent("UserProxy", input_func=input)

            strategy_team = RoundRobinGroupChat(
                [survey_director, user_proxy],
                termination_condition=TextMentionTermination("APPROVE"),
                max_turns=6
            )

            strategy_task = f"""
            请为研究主题"{research_topic}"制定详细的文献调研策略。

            要求：
            1. 分析研究主题的学术内涵和研究范围
            2. 构建多层次的检索关键词体系
            3. 生成8个不同角度的英文检索查询
            4. 制定质量标准和检索计划
            5. 为PaperRetriever提供明确的执行指令

            完成策略制定后，请明确说"策略制定完成"。
            """

            print("🚀 启动策略制定...")
            strategy_stream = strategy_team.run_stream(task=strategy_task)
            strategy_result = await Console(strategy_stream, no_inline_images=True)

            self.conversation_history.append({
                "phase": "strategy",
                "result": str(strategy_result),
                "timestamp": datetime.now().isoformat()
            })

            print("✅ 策略制定阶段完成")

            # 阶段2: 文献检索
            print("\n📚 阶段2: 多轮文献检索")
            print("-" * 60)

            retrieval_team = RoundRobinGroupChat(
                [paper_retriever, user_proxy],
                termination_condition=TextMentionTermination("APPROVE"),
                max_turns=12  # 允许多轮检索
            )

            retrieval_task = f"""
            根据SurveyDirector提供的策略，对研究主题"{research_topic}"进行系统性文献检索。

            执行要求：
            1. 使用策略中提供的8个检索查询
            2. 每个查询调用相应的搜索工具检索5篇论文
            3. 灵活选择arXiv、Semantic Scholar、Google Scholar等数据源
            4. 应用质量过滤标准，确保论文相关性和质量
            5. 最终筛选出25+篇高质量论文
            6. 将论文按主题相似性分成3-4批，每批6-8篇
            7. 为每批提供主题说明，便于后续分析

            请执行多轮检索，直到达到目标论文数量。完成后说"检索完成"。
            """

            print("🔍 启动多轮检索...")
            retrieval_stream = retrieval_team.run_stream(task=retrieval_task)
            retrieval_result = await Console(retrieval_stream, no_inline_images=True)

            self.conversation_history.append({
                "phase": "retrieval",
                "result": str(retrieval_result),
                "timestamp": datetime.now().isoformat()
            })

            print("✅ 文献检索阶段完成")

            # 阶段3: 分批文献分析
            print("\n🔬 阶段3: 分批深度分析")
            print("-" * 60)

            analysis_team = RoundRobinGroupChat(
                [paper_analyzer, user_proxy],
                termination_condition=TextMentionTermination("APPROVE"),
                max_turns=15  # 允许多轮分析
            )

            analysis_task = f"""
            对PaperRetriever检索和分批的论文进行深度分析。

            分析要求：
            1. 按批次接收和处理论文
            2. 对每篇论文进行全面的学术分析，包括：
               - 基本信息和研究背景
               - 研究贡献分析（理论、方法、实证、应用）
               - 方法论深度分析
               - 关键发现总结
               - 创新性和重要性评估
               - 局限性和批判性分析
               - 学术价值和引用指导
            3. 进行批次内的对比分析和综合
            4. 维护跨批次的分析一致性
            5. 生成适合综述写作的详实内容
            6. 根据需要使用搜索工具获取补充信息

            请逐批进行详细分析，确保内容详实、客观、有深度。完成所有批次后说"分析完成"。
            """

            print("📊 启动分批分析...")
            analysis_stream = analysis_team.run_stream(task=analysis_task)
            analysis_result = await Console(analysis_stream, no_inline_images=True)

            self.conversation_history.append({
                "phase": "analysis",
                "result": str(analysis_result),
                "timestamp": datetime.now().isoformat()
            })

            print("✅ 文献分析阶段完成")

            # 保存完整的工作流结果
            workflow_summary = {
                "research_topic": research_topic,
                "completion_time": datetime.now().isoformat(),
                "phases_completed": 3,
                "success": True,
                "conversation_history": self.conversation_history
            }

            self._save_results(workflow_summary)

            print("\n🎉 完整工作流测试成功完成！")
            print(f"📊 完成阶段: 3个核心阶段")
            print(f"📚 目标: 25+篇高质量论文的深度分析")
            print(f"📄 输出: {self.output_dir.absolute()}")

            return True

        except Exception as e:
            print(f"❌ 工作流测试失败: {e}")
            import traceback
            print(f"详细错误:\n{traceback.format_exc()}")
            return False

    async def test_individual_agents(self):
        """单独测试各个智能体"""
        print("\n🧪 单独测试智能体功能")
        print("=" * 60)

        if not AUTOGEN_IMPORTED or not AGENTS_IMPORTED:
            print("❌ 缺少必要的依赖模块")
            return False

        test_topic = "图神经网络在推荐系统中的应用"

        # 测试1: 调研总监
        print("\n1️⃣ 测试通用调研总监")
        try:
            director = get_survey_director()

            user_proxy = UserProxyAgent("UserProxy", input_func=input)
            director_team = RoundRobinGroupChat(
                [director, user_proxy],
                termination_condition=TextMentionTermination("APPROVE"),
                max_turns=4
            )

            director_task = f"""
            为研究主题"{test_topic}"制定调研策略。请调用create_research_strategy工具生成策略，然后说"测试完成"。
            """

            print("测试策略制定功能...")
            director_stream = director_team.run_stream(task=director_task)
            director_result = await Console(director_stream, no_inline_images=True)
            print("✅ 调研总监测试通过")

        except Exception as e:
            print(f"❌ 调研总监测试失败: {e}")

        # 测试2: 文献检索专家
        print("\n2️⃣ 测试通用文献检索专家")
        try:
            retriever = get_paper_retriever()

            retriever_team = RoundRobinGroupChat(
                [retriever, user_proxy],
                termination_condition=TextMentionTermination("APPROVE"),
                max_turns=6
            )

            retriever_task = f"""
            模拟检索任务：使用查询"graph neural networks recommendation systems"进行一次检索测试。
            请调用适当的搜索工具，然后说"测试完成"。
            """

            print("测试文献检索功能...")
            retriever_stream = retriever_team.run_stream(task=retriever_task)
            retriever_result = await Console(retriever_stream, no_inline_images=True)
            print("✅ 文献检索专家测试通过")

        except Exception as e:
            print(f"❌ 文献检索专家测试失败: {e}")

        # 测试3: 文献分析专家
        print("\n3️⃣ 测试通用文献分析专家")
        try:
            analyzer = get_paper_analyzer()
            analyzer_team = RoundRobinGroupChat(
                [analyzer, user_proxy],
                termination_condition=TextMentionTermination("APPROVE"),
                max_turns=4
            )

            sample_paper = {
                "title": "Graph Neural Networks for Recommender Systems: A Survey",
                "authors": ["Wang, X.", "He, X.", "Chua, T.S."],
                "abstract": "This paper presents a comprehensive survey of graph neural networks applied to recommender systems, covering both collaborative filtering and content-based approaches.",
                "year": 2023,
                "citation_count": 156,
                "venue": "ACM Computing Surveys"
            }

            analyzer_task = f"""
            模拟论文分析任务：分析以下论文
            {json.dumps(sample_paper, ensure_ascii=False, indent=2)}

            请按照分析框架进行详细分析，然后说"测试完成"。
            """

            print("测试论文分析功能...")
            analyzer_stream = analyzer_team.run_stream(task=analyzer_task)
            analyzer_result = await Console(analyzer_stream, no_inline_images=True)
            print("✅ 文献分析专家测试通过")

        except Exception as e:
            print(f"❌ 文献分析专家测试失败: {e}")

        print("\n✅ 所有智能体单独测试完成")

    def _save_results(self, results):
        """保存测试结果"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 保存完整结果
            full_filename = f"complete_workflow_{timestamp}.json"
            full_filepath = self.output_dir / full_filename

            with open(full_filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            # 保存可读摘要
            summary_filename = f"workflow_summary_{timestamp}.txt"
            summary_filepath = self.output_dir / summary_filename

            with open(summary_filepath, 'w', encoding='utf-8') as f:
                f.write("文献调研工作流测试报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"研究主题: {results['research_topic']}\n")
                f.write(f"完成时间: {results['completion_time']}\n")
                f.write(f"完成阶段: {results['phases_completed']}\n")
                f.write(f"测试状态: {'成功' if results['success'] else '失败'}\n\n")

                for i, phase in enumerate(results['conversation_history'], 1):
                    f.write(f"=== 阶段{i}: {phase['phase'].upper()} ===\n")
                    f.write(f"时间: {phase['timestamp']}\n")
                    f.write(f"内容预览: {str(phase['result'])[:300]}...\n\n")

            print(f"📄 结果已保存:")
            print(f"   完整结果: {full_filename}")
            print(f"   摘要报告: {summary_filename}")

        except Exception as e:
            print(f"❌ 保存结果失败: {e}")


async def main():
    """主函数"""
    print("🚀 通用文献调研工作流测试系统")
    print("=" * 80)

    tester = CompleteWorkflowTester()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "agents":
            # 测试单个智能体
            print("🧪 模式: 单独测试智能体")
            await tester.test_individual_agents()

        elif command == "workflow":
            # 测试完整工作流
            research_topic = sys.argv[2] if len(sys.argv) > 2 else "深度学习在计算机视觉中的应用"
            print(f"🔄 模式: 完整工作流测试")
            await tester.test_complete_workflow(research_topic)

        else:
            print("❌ 未知命令。使用方式:")
            print("   python script.py agents        # 测试单个智能体")
            print("   python script.py workflow [主题] # 测试完整工作流")
    else:
        # 交互式选择
        print("请选择测试模式:")
        print("1. 测试单个智能体")
        print("2. 测试完整工作流")

        choice = input("\n请输入选择 (1/2): ").strip()

        if choice == "1":
            await tester.test_individual_agents()
        elif choice == "2":
            topic = input("请输入研究主题 (默认: 机器学习在数据挖掘中的应用): ").strip()
            if not topic:
                topic = "机器学习在数据挖掘中的应用"
            await tester.test_complete_workflow(topic)
        else:
            print("❌ 无效选择")


if __name__ == "__main__":
    print("🧪 通用文献调研工作流测试准备就绪...")
    asyncio.run(main())