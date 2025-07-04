#!/usr/bin/env python3
"""
AutoGen工作流测试脚本
基于真实的AutoGen团队工作流模式进行测试
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
sys.path.append(str(current_dir.parent))

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

# 导入智能体
try:
    from agents.article_research.survey_director import get_survey_director
    from agents.article_research.paper_retriever import get_paper_retriever
    from agents.article_research.paper_analyzer import get_paper_analyzer
    from agents.article_research.knowledge_synthesizer import get_knowledge_synthesizer
    from agents.article_research.visualization_specialist import get_visualization_specialist
    from agents.article_research.report_generator import get_report_generator

    AGENTS_IMPORTED = True
    print("✅ 成功导入所有智能体模块")
except ImportError as e:
    print(f"❌ 导入智能体失败: {e}")
    AGENTS_IMPORTED = False


class AutoGenWorkflowTester:
    """AutoGen工作流测试器"""

    def __init__(self):
        self.test_results = {}
        self.output_dir = Path("test_outputs")
        self.output_dir.mkdir(exist_ok=True)

    async def test_single_agent(self, agent_name: str, agent_factory, test_task: str):
        """测试单个智能体"""
        print(f"\n🧪 测试 {agent_name}...")
        print("-" * 60)

        try:
            if not AUTOGEN_IMPORTED or not AGENTS_IMPORTED:
                raise Exception("缺少必要的依赖模块")

            print("开始智能体初始化...")

            # 创建智能体实例
            agent = agent_factory()
            print(f"✅ {agent_name} 实例创建成功")
            print(f"   Agent名称: {agent.name}")
            print(f"   工具数量: {len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0}")

            # 显示工具信息
            if hasattr(agent, 'tools') and agent.tools:
                for i, tool in enumerate(agent.tools):
                    tool_name = getattr(tool, 'name', f'Tool_{i}')
                    print(f"   工具{i + 1}: {tool_name}")

            # 创建自动用户代理（避免交互）
            user_proxy = UserProxyAgent(
                "UserProxy",
                input_func=input
            )

            # 创建终止条件
            termination_condition = TextMentionTermination("APPROVE")

            print("团队创建完成，开始运行流...")

            # 创建团队
            team = RoundRobinGroupChat(
                [agent, user_proxy],
                termination_condition=termination_condition,
                max_turns=3,  # 限制轮次避免无限循环
                emit_team_events=True
            )

            # 记录开始时间
            start_time = datetime.now()

            # 启动消息流
            print(f"📝 发送测试任务: {test_task[:100]}...")
            message_stream = team.run_stream(task=test_task)

            print("消息流启动，等待控制台输出...")

            # 使用Console处理消息流
            result = await Console(
                message_stream,
                no_inline_images=True,
                output_stats=True
            )

            # 记录结束时间
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 提取结果内容
            result_content = str(result) if result else "No result"

            # 记录测试结果
            self.test_results[agent_name] = {
                "status": "✅ 通过",
                "response_length": len(result_content),
                "execution_time": execution_time,
                "tools_count": len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0,
                "response_preview": result_content[:200] + "..." if len(result_content) > 200 else result_content,
                "test_time": datetime.now().isoformat()
            }

            # 保存完整响应
            self.save_agent_response(agent_name, test_task, result_content)

            print(f"✅ 测试成功完成")
            print(f"   响应长度: {len(result_content)} 字符")
            print(f"   执行时间: {execution_time:.2f} 秒")
            print(f"   响应预览: {result_content[:100]}...")

            return True

        except Exception as e:
            self.test_results[agent_name] = {
                "status": "❌ 失败",
                "error": str(e),
                "test_time": datetime.now().isoformat()
            }
            print(f"❌ 测试失败: {e}")
            return False

    async def test_survey_director(self):
        """测试调研总监"""
        test_task = """
        请为研究主题"图神经网络在推荐系统中的应用"制定详细的文献调研策略。

        要求包括：
        1. 分解为3-5个子研究方向
        2. 为每个方向生成英文检索关键词
        3. 制定检索优先级和时间范围
        4. 预估需要检索的文献数量

        请提供结构化的策略规划。
        """

        return await self.test_single_agent(
            "SurveyDirector",
            get_survey_director,
            test_task
        )

    async def test_paper_retriever(self):
        """测试文献检索专家"""
        test_task = """
        请检索关于"Graph Neural Networks recommendation systems"的相关学术论文。

        检索要求：
        1. 使用arXiv等学术数据库
        2. 重点关注最近3年的高质量文献
        3. 返回论文的详细元数据
        4. 按相关性和引用数排序

        请调用适当的工具进行检索，并提供结构化的结果。
        """

        return await self.test_single_agent(
            "PaperRetriever",
            get_paper_retriever,
            test_task
        )

    async def test_paper_analyzer(self):
        """测试文献分析专家"""
        test_paper = {
            "title": "Graph Neural Networks for Recommender Systems: A Survey",
            "authors": ["Wang, X.", "He, X.", "Wang, M.", "Feng, F.", "Chua, T.S."],
            "abstract": "Graph Neural Networks (GNNs) have emerged as a powerful technique for modeling graph-structured data in recommender systems. This survey provides a comprehensive overview of GNN-based recommendation approaches, categorizing them into spectral-based and spatial-based methods.",
            "year": 2023,
            "citation_count": 445,
            "venue": "ACM Computing Surveys"
        }

        test_task = f"""
        请对以下论文进行深度分析：

        论文信息：
        {json.dumps(test_paper, ensure_ascii=False, indent=2)}

        分析要求：
        1. 提取核心贡献和创新点
        2. 分析使用的方法和技术
        3. 评估论文质量和影响力
        4. 识别与其他工作的关系
        5. 提取可引用的关键观点

        请调用分析工具提供结构化的分析结果。
        """

        return await self.test_single_agent(
            "PaperAnalyzer",
            get_paper_analyzer,
            test_task
        )

    async def test_knowledge_synthesizer(self):
        """测试知识综合专家"""
        test_analyses = [
            {
                "paper_title": "Graph Neural Networks for Recommendation",
                "analysis": "本文提出了基于图神经网络的推荐系统框架，通过学习用户-物品交互图的表示来提升推荐性能。"
            },
            {
                "paper_title": "Neural Collaborative Filtering",
                "analysis": "该研究将深度学习应用于协同过滤，通过神经网络学习用户和物品的非线性交互。"
            }
        ]

        test_task = f"""
        请基于以下文献分析结果进行知识综合：

        分析数据：
        {json.dumps(test_analyses, ensure_ascii=False, indent=2)}

        综合要求：
        1. 构建该领域的技术分类体系
        2. 识别主要研究方法和技术路线
        3. 总结关键发现和共识
        4. 识别争议点和不同观点
        5. 发现研究空白和未来方向

        请调用知识综合工具生成结构化结果。
        """

        return await self.test_single_agent(
            "KnowledgeSynthesizer",
            get_knowledge_synthesizer,
            test_task
        )

    async def test_visualization_specialist(self):
        """测试可视化专家"""
        viz_data = {
            "research_topic": "图神经网络推荐系统",
            "timeline_data": {
                "2018": "Graph Convolutional Networks for Web-Scale Recommender Systems",
                "2019": "Neural Graph Collaborative Filtering",
                "2020": "LightGCN: Simplifying and Powering Graph Convolution Network"
            }
        }

        test_task = f"""
        请基于以下数据创建交互式可视化：

        数据内容：
        {json.dumps(viz_data, ensure_ascii=False, indent=2)}

        可视化要求：
        1. 创建研究发展时间线图
        2. 包含交互式功能
        3. 生成完整的HTML代码

        请调用可视化工具生成可嵌入报告的HTML内容。
        """

        return await self.test_single_agent(
            "VisualizationSpecialist",
            get_visualization_specialist,
            test_task
        )

    async def test_report_generator(self):
        """测试报告生成专家"""
        test_data = {
            "research_topic": "图神经网络在推荐系统中的应用",
            "strategy": {"research_directions": ["GNN架构", "推荐算法", "性能评估"]},
            "retrieved_papers": [
                {"title": "Graph Neural Networks for Recommendation", "authors": ["Wang et al."]},
                {"title": "Neural Collaborative Filtering", "authors": ["He et al."]}
            ],
            "analyzed_papers": [
                {"analysis": "GNN在推荐系统中的应用分析..."},
                {"analysis": "协同过滤的深度学习方法..."}
            ]
        }

        test_task = f"""
        请基于以下研究数据生成完整的综述报告：

        研究数据：
        {json.dumps(test_data, ensure_ascii=False, indent=2)}

        报告要求：
        1. 生成详细的学术报告
        2. 包含多个引用
        3. 使用HTML格式
        4. 包含内嵌式引用和链接
        5. 专业的学术写作风格

        请调用报告生成工具创建HTML格式综述报告。
        """

        return await self.test_single_agent(
            "ReportGenerator",
            get_report_generator,
            test_task
        )

    async def test_collaborative_workflow(self):
        """测试协同工作流"""
        print("\n🔄 测试智能体协同工作流...")
        print("=" * 80)

        try:
            if not AUTOGEN_IMPORTED or not AGENTS_IMPORTED:
                raise Exception("缺少必要的依赖模块")

            research_topic = "Transformer架构在多模态学习中的应用"
            print(f"🎯 研究主题: {research_topic}")

            print("开始工作流初始化...")

            # 创建所有智能体
            survey_director = get_survey_director()
            paper_retriever = get_paper_retriever()
            paper_analyzer = get_paper_analyzer()
            knowledge_synthesizer = get_knowledge_synthesizer()
            report_generator = get_report_generator()

            print("代理初始化完成")

            # 创建终止条件
            termination_condition = TextMentionTermination("APPROVE")

            print("团队创建完成，开始运行流...")

            user_proxy = UserProxyAgent(
                "UserProxy",
                input_func=input
            )

            # 创建团队（包含所有智能体）
            team = RoundRobinGroupChat(
                [survey_director, paper_retriever, paper_analyzer, knowledge_synthesizer, report_generator,
                 user_proxy],
                termination_condition=termination_condition,
                max_turns=10,  # 限制最大轮次
                emit_team_events=True
            )

            # 记录开始时间
            start_time = datetime.now()

            # 构建协同任务
            collaborative_task = f"""
            请各位智能体协同完成关于"{research_topic}"的文献调研工作流：

            1. SurveyDirector: 制定调研策略和关键词
            2. PaperRetriever: 根据策略检索相关文献
            3. PaperAnalyzer: 分析检索到的重要文献
            4. KnowledgeSynthesizer: 综合分析结果构建知识体系
            5. ReportGenerator: 生成最终的综述报告

            请按顺序协作完成，每个智能体完成自己的任务后传递给下一个。
            最后说"工作流完成"以结束流程。
            """

            # 启动协同工作流
            print("启动协同消息流...")
            message_stream = team.run_stream(task=collaborative_task)

            print("消息流启动，等待协同工作完成...")

            # 处理消息流
            result = await Console(
                message_stream,
                no_inline_images=True,
                output_stats=True
            )

            # 记录结束时间
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 保存协同工作流结果
            workflow_result = {
                "success": True,
                "research_topic": research_topic,
                "execution_time": execution_time,
                "result_content": str(result) if result else "No result",
                "agents_involved": ["SurveyDirector", "PaperRetriever", "PaperAnalyzer", "KnowledgeSynthesizer",
                                    "ReportGenerator"],
                "completion_time": datetime.now().isoformat()
            }

            # 保存结果
            self.save_workflow_result(workflow_result)

            print(f"✅ 协同工作流测试成功完成")
            print(f"   执行时间: {execution_time:.2f} 秒")
            print(f"   涉及智能体: {len(workflow_result['agents_involved'])} 个")

            return True

        except Exception as e:
            print(f"❌ 协同工作流测试失败: {e}")
            return False

    def save_agent_response(self, agent_name: str, task: str, response: str):
        """保存agent响应到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{agent_name}_response_{timestamp}.txt"
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Agent: {agent_name}\n")
                f.write(f"Task: {task[:200]}...\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Response Length: {len(response)} characters\n")
                f.write("-" * 80 + "\n")
                f.write(response)

            print(f"   📄 响应已保存: {filepath.name}")

        except Exception as e:
            print(f"   ❌ 保存响应失败: {e}")

    def save_workflow_result(self, result: dict):
        """保存工作流结果"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"collaborative_workflow_result_{timestamp}.json"
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"   📄 工作流结果已保存: {filepath.name}")

        except Exception as e:
            print(f"   ❌ 保存工作流结果失败: {e}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始AutoGen工作流全面测试...")
        print("=" * 100)

        # 检查依赖
        if not AUTOGEN_IMPORTED:
            print("❌ AutoGen组件未正确导入，无法进行测试")
            return False

        if not AGENTS_IMPORTED:
            print("❌ 智能体模块未正确导入，无法进行测试")
            return False

        # 单个智能体测试
        test_methods = [
            ("SurveyDirector", self.test_survey_director),
            ("PaperRetriever", self.test_paper_retriever),
            ("PaperAnalyzer", self.test_paper_analyzer),
            ("KnowledgeSynthesizer", self.test_knowledge_synthesizer),
            ("VisualizationSpecialist", self.test_visualization_specialist),
            ("ReportGenerator", self.test_report_generator)
        ]

        success_count = 0
        total_count = len(test_methods)

        # 逐个测试智能体
        for agent_name, test_method in test_methods:
            try:
                success = await test_method()
                if success:
                    success_count += 1
            except Exception as e:
                print(f"   ❌ {agent_name} 测试执行出错: {e}")
                self.test_results[agent_name] = {
                    "status": "❌ 执行错误",
                    "error": str(e),
                    "test_time": datetime.now().isoformat()
                }

        # 协同工作流测试
        workflow_success = await self.test_collaborative_workflow()

        # 输出测试总结
        self.print_test_summary(success_count, total_count, workflow_success)

        return success_count == total_count and workflow_success

    def print_test_summary(self, success_count: int, total_count: int, workflow_success: bool):
        """打印测试总结"""
        print("\n" + "=" * 100)
        print("📊 AutoGen工作流测试总结")
        print("=" * 100)

        for agent_name, result in self.test_results.items():
            status = result["status"]
            print(f"{status} {agent_name}")

            if "✅" in status:
                print(f"     📝 响应长度: {result.get('response_length', 0):,} 字符")
                print(f"     ⏱️  执行时间: {result.get('execution_time', 0):.2f} 秒")
                print(f"     🔧 工具数量: {result.get('tools_count', 0)}")
            else:
                if "error" in result:
                    print(f"     ❌ 错误: {result['error']}")

            print(f"     🕒 测试时间: {result['test_time']}")
            print()

        print(f"智能体测试: {success_count}/{total_count} 通过")
        print(f"协同工作流: {'✅ 通过' if workflow_success else '❌ 失败'}")
        print(f"整体成功率: {((success_count + (1 if workflow_success else 0)) / (total_count + 1) * 100):.1f}%")
        print(f"📁 输出目录: {self.output_dir.absolute()}")

        if success_count == total_count and workflow_success:
            print("\n🎉 所有测试均通过！AutoGen工作流系统运行正常。")
        elif success_count == total_count:
            print("\n⚠️  智能体单独测试通过，但协同工作流存在问题。")
        else:
            print("\n⚠️  部分智能体测试失败，请检查配置和依赖。")


# 单独测试函数
async def test_individual_agent(agent_name: str):
    """测试单个智能体"""
    tester = AutoGenWorkflowTester()

    agent_tests = {
        "director": tester.test_survey_director,
        "retriever": tester.test_paper_retriever,
        "analyzer": tester.test_paper_analyzer,
        "synthesizer": tester.test_knowledge_synthesizer,
        "visualizer": tester.test_visualization_specialist,
        "generator": tester.test_report_generator
    }

    if agent_name.lower() in agent_tests:
        print(f"🧪 测试单个智能体: {agent_name}")
        success = await agent_tests[agent_name.lower()]()
        tester.print_test_summary(1 if success else 0, 1, False)
        return success
    else:
        print(f"❌ 未知的智能体名称: {agent_name}")
        print("可用的智能体: director, retriever, analyzer, synthesizer, visualizer, generator")
        return False


async def test_workflow_only():
    """只测试协同工作流"""
    tester = AutoGenWorkflowTester()
    print("🔄 运行协同工作流测试...")
    success = await tester.test_collaborative_workflow()
    return success


# 主函数
async def main():
    """主测试函数"""
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "workflow":
            # 只测试工作流
            await test_workflow_only()
        else:
            # 测试单个智能体
            agent_name = sys.argv[1]
            await test_individual_agent(agent_name)
    else:
        # 运行全面测试
        tester = AutoGenWorkflowTester()
        await tester.run_all_tests()


if __name__ == "__main__":
    print("🧪 AutoGen工作流测试启动...")
    asyncio.run(main())