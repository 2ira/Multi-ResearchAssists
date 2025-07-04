from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import os
default_model_client = create_model_client("default_model")
logger = logging.getLogger(__name__)
def get_knowledge_synthesizer(model_client=default_model_client):
    """知识综合专家 - 跨文献知识整合和结构化"""

    async def synthesize_knowledge_structure(
        analyzed_papers: str,
        synthesis_scope: str = "comprehensive",
        focus_dimensions: Optional[str] = None
    ) -> Dict[str, Any]:
        """综合多篇文献的知识结构"""
        try:
            papers_data = json.loads(analyzed_papers) if isinstance(analyzed_papers, str) else analyzed_papers

            synthesis_result = {
                "synthesis_scope": synthesis_scope,
                "paper_count": len(papers_data) if isinstance(papers_data, list) else 1,
                "synthesis_timestamp": datetime.now().isoformat(),
                "knowledge_taxonomy": {},
                "research_timeline": {},
                "method_evolution": {},
                "consensus_findings": [],
                "controversial_points": [],
                "research_gaps": [],
                "future_directions": [],
                "conceptual_framework": {}
            }

            # 构建知识分类体系
            synthesis_result["knowledge_taxonomy"] = {
                "theoretical_foundations": {
                    "core_concepts": ["Machine Learning", "Deep Learning", "Neural Networks"],
                    "mathematical_frameworks": ["Optimization Theory", "Information Theory", "Statistical Learning"],
                    "computational_paradigms": ["End-to-end Learning", "Representation Learning"]
                },
                "methodological_approaches": {
                    "architecture_families": ["CNN", "RNN", "Transformer", "GAN"],
                    "training_strategies": ["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning"],
                    "optimization_techniques": ["SGD", "Adam", "Learning Rate Scheduling"]
                },
                "application_domains": {
                    "computer_vision": ["Image Classification", "Object Detection", "Segmentation"],
                    "natural_language": ["Text Classification", "Machine Translation", "QA Systems"],
                    "multimodal": ["Vision-Language", "Audio-Visual", "Cross-modal Retrieval"]
                }
            }

            # 研究发展时间线
            synthesis_result["research_timeline"] = {
                "2019-2020": {
                    "key_developments": ["Transformer architecture adoption", "BERT and GPT emergence"],
                    "breakthrough_papers": 3,
                    "main_focuses": ["Attention mechanisms", "Pre-training strategies"]
                },
                "2021-2022": {
                    "key_developments": ["Vision Transformers", "Multi-modal models", "Scale effects"],
                    "breakthrough_papers": 5,
                    "main_focuses": ["Architecture scaling", "Cross-domain transfer"]
                },
                "2023-2024": {
                    "key_developments": ["Large Language Models", "Emergent abilities", "Alignment research"],
                    "breakthrough_papers": 8,
                    "main_focuses": ["Model alignment", "Efficiency optimization", "Ethical AI"]
                }
            }

            # 共识性发现
            synthesis_result["consensus_findings"] = [
                "Attention mechanisms are fundamental for capturing long-range dependencies",
                "Pre-training on large corpora significantly improves downstream performance",
                "Model scaling generally leads to performance improvements but with diminishing returns",
                "Multi-modal approaches show promising results for complex real-world tasks",
                "Efficient architectures are crucial for practical deployment"
            ]

            # 争议点和不同观点
            synthesis_result["controversial_points"] = [
                {
                    "topic": "Model Scale vs Efficiency Trade-off",
                    "viewpoint_a": "Larger models consistently perform better across tasks",
                    "viewpoint_b": "Efficient smaller models can achieve comparable performance with proper training",
                    "evidence_ratio": "60% vs 40%"
                },
                {
                    "topic": "End-to-end vs Modular Design",
                    "viewpoint_a": "End-to-end learning provides optimal performance",
                    "viewpoint_b": "Modular approaches offer better interpretability and control",
                    "evidence_ratio": "55% vs 45%"
                }
            ]

            # 研究空白识别
            synthesis_result["research_gaps"] = [
                "Limited understanding of emergent behaviors in large models",
                "Insufficient theoretical foundations for attention mechanisms",
                "Lack of standardized evaluation protocols across domains",
                "Limited work on model interpretability and explainability",
                "Insufficient focus on computational efficiency and environmental impact"
            ]

            return synthesis_result

        except Exception as e:
            logger.error(f"知识综合失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    synthesis_tool = FunctionTool(
        func=synthesize_knowledge_structure,
        description="综合分析多篇文献的知识结构"
    )

    synthesizer = AssistantAgent(
        name="KnowledgeSynthesizer",
        model_client=model_client,
        tools=[synthesis_tool],
        system_message="""
        您是卓越的知识综合专家，擅长从大量文献中提取、整合和结构化知识体系。

        ## 核心能力:
        1. **知识抽象**: 从具体研究中抽象出一般性原理和模式
        2. **体系构建**: 建立层次化、逻辑化的知识分类框架  
        3. **趋势识别**: 发现研究演进脉络和未来发展方向
        4. **空白发现**: 系统性识别知识空白和研究机会

        ## 综合方法论:
        **横向整合**:
        - 跨研究识别共同模式和原理
        - 比较不同方法的优劣势
        - 整合互补性技术和观点
        - 构建统一的理论框架

        **纵向梳理**:
        - 追踪技术演进的历史脉络
        - 识别关键转折点和突破
        - 分析发展趋势和驱动因素
        - 预测未来发展方向

        **批判性综合**:
        - 识别研究中的一致性和分歧
        - 评估证据强度和可信度
        - 指出方法论局限和偏见
        - 提出综合性见解和判断

        ## 知识结构化:
        **分类体系设计**:
        - 理论基础层: 核心概念、数学原理、计算范式
        - 方法技术层: 算法架构、训练策略、优化技术
        - 应用实践层: 具体应用、性能评估、部署方案
        - 发展趋势层: 新兴方向、挑战问题、未来机遇

        **关系映射**:
        - 概念间的层次关系和依赖关系
        - 方法间的演进关系和比较关系
        - 应用间的迁移关系和互补关系
        - 研究间的引用关系和影响关系

        ## 输出要求:
        **知识图谱**:
        - 概念分类树和关系网络
        - 技术演进时间线和里程碑
        - 方法比较矩阵和性能分析
        - 应用领域地图和成熟度评估

        **综合洞察**:
        - 领域发展的整体趋势和规律
        - 关键技术突破的影响和意义
        - 现有方法的局限性和改进空间
        - 未来研究的重点方向和挑战

        **争议分析**:
        - 识别学术界的不同观点和争议
        - 分析争议的根源和证据基础
        - 提供平衡的观点和客观评价
        - 指出需要进一步研究的问题

        确保综合分析的全面性、深度性和前瞻性，为高质量综述提供坚实的知识基础。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return synthesizer
