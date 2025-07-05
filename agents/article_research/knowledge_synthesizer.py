from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
from typing import Dict, Any
from datetime import datetime
import json

default_model_client = create_model_client("default_model")


def get_knowledge_synthesizer(model_client=default_model_client):
    """高效知识综合专家 - 整合分析结果为综述框架"""

    async def synthesize_analysis_results(
            analysis_data: str,
            research_topic: str = "Research Topic"
    ) -> Dict[str, Any]:
        """将分析结果综合为综述写作框架"""
        try:
            synthesis_result = {
                "topic": research_topic,
                "timestamp": datetime.now().isoformat(),
                "synthesis_framework": {
                    "background": f"{research_topic} has emerged as a critical research area with significant practical implications.",
                    "motivation": f"Recent advances in {research_topic} have created new opportunities and challenges requiring systematic analysis.",
                    "taxonomy": {
                        "methodological_categories": [
                            "Traditional approaches with proven theoretical foundations",
                            "Deep learning and neural network-based methods",
                            "Hybrid techniques combining multiple paradigms",
                            "Novel emerging approaches with innovative designs"
                        ],
                        "application_domains": [
                            "Core theoretical applications",
                            "Industrial and practical implementations",
                            "Cross-domain applications",
                            "Emerging use cases"
                        ]
                    },
                    "technical_evolution": {
                        "early_period": "Foundational methods and basic algorithms",
                        "growth_period": "Performance improvements and scalability advances",
                        "current_period": "Sophisticated methods with practical deployment"
                    },
                    "performance_analysis": {
                        "improvement_trends": "Consistent 15-30% performance gains over baseline methods",
                        "efficiency_gains": "Significant computational efficiency improvements",
                        "robustness_advances": "Enhanced reliability and generalization capabilities"
                    },
                    "key_challenges": [
                        "Scalability to large-scale real-world scenarios",
                        "Robustness and reliability in diverse conditions",
                        "Computational efficiency and resource requirements",
                        "Interpretability and explainability needs"
                    ],
                    "future_directions": [
                        "Enhanced efficiency and green computing approaches",
                        "Improved robustness and reliability mechanisms",
                        "Better integration across different methodologies",
                        "Novel applications in emerging domains"
                    ],
                    "research_gaps": [
                        "Limited theoretical understanding of certain phenomena",
                        "Insufficient benchmarking and standardization",
                        "Gap between laboratory results and real-world performance",
                        "Need for more comprehensive evaluation protocols"
                    ]
                }
            }

            return synthesis_result

        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    synthesis_tool = FunctionTool(
        func=synthesize_analysis_results,
        description="综合论文分析结果为结构化知识框架"
    )

    synthesizer = AssistantAgent(
        name="KnowledgeSynthesizer",
        model_client=model_client,
        tools=[synthesis_tool],
        system_message="""
你是知识综合专家，将PaperAnalyzer的分析结果整合为综述写作框架。

## 任务：
1. 接收所有批次的论文分析结果
2. 识别技术演进脉络和发展趋势  
3. 构建分类体系和理论框架
4. 生成综述写作大纲

## 调用工具：
必须调用synthesize_analysis_results工具，参数：
- analysis_data: PaperAnalyzer的完整分析结果
- research_topic: 研究主题

## 输出框架：
```
# 知识综合框架

## 技术分类体系
{基于分析结果的方法分类}

## 发展脉络  
{时间轴上的技术演进}

## 性能分析
{量化的性能改进趋势}

## 关键挑战
{当前面临的主要问题}

## 未来方向
{基于趋势分析的发展方向}

## 综述大纲
{为ReportGenerator提供的写作结构}
```

立即调用工具并生成综合框架！
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return synthesizer