from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from model_factory import create_model_client
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)


default_model_client = create_model_client("default_model")



def get_visualization_specialist(model_client=default_model_client):
    """可视化专家 - 生成交互式图表和可视化内容"""

    async def create_interactive_visualization(
            data_content: str,
            viz_type: str,
            title: str,
            interactive_features: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建交互式可视化内容"""
        try:
            viz_result = {
                "viz_type": viz_type,
                "title": title,
                "creation_timestamp": datetime.now().isoformat(),
                "html_content": "",
                "features": [],
                "data_sources": data_content
            }

            if viz_type == "timeline":
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{title}</title>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
                    <style>
                        .timeline-container {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                        }}
                        .timeline-item {{
                            margin: 10px 0;
                            padding: 15px;
                            border-left: 3px solid #007bff;
                            background: #f8f9fa;
                            border-radius: 5px;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        }}
                        .timeline-item:hover {{
                            background: #e9ecef;
                            transform: translateX(5px);
                        }}
                        .timeline-year {{
                            font-weight: bold;
                            color: #007bff;
                            font-size: 18px;
                        }}
                        .timeline-content {{
                            margin-top: 10px;
                            line-height: 1.6;
                        }}
                        .citation-link {{
                            color: #28a745;
                            text-decoration: none;
                            font-weight: bold;
                        }}
                        .citation-link:hover {{
                            text-decoration: underline;
                        }}
                    </style>
                </head>
                <body>
                    <div class="timeline-container">
                        <h2>{title}</h2>
                        <div class="timeline-item" onclick="showDetails('2019')">
                            <div class="timeline-year">2019-2020</div>
                            <div class="timeline-content">
                                <strong>Transformer Revolution:</strong> 
                                <a href="#ref1" class="citation-link">[Vaswani et al., 2017]</a> 
                                introduction of attention mechanisms revolutionized NLP.
                                <a href="#ref2" class="citation-link">[Devlin et al., 2019]</a> 
                                BERT showed the power of pre-training.
                            </div>
                        </div>
                        <div class="timeline-item" onclick="showDetails('2021')">
                            <div class="timeline-year">2021-2022</div>
                            <div class="timeline-content">
                                <strong>Vision Transformers:</strong>
                                <a href="#ref3" class="citation-link">[Dosovitskiy et al., 2021]</a>
                                brought transformers to computer vision.
                                <a href="#ref4" class="citation-link">[Radford et al., 2021]</a>
                                CLIP enabled multi-modal understanding.
                            </div>
                        </div>
                        <div class="timeline-item" onclick="showDetails('2023')">
                            <div class="timeline-year">2023-2024</div>
                            <div class="timeline-content">
                                <strong>Large Language Models:</strong>
                                <a href="#ref5" class="citation-link">[OpenAI, 2023]</a>
                                GPT-4 demonstrated emergent capabilities.
                                <a href="#ref6" class="citation-link">[Touvron et al., 2023]</a>
                                LLaMA series showed efficient scaling.
                            </div>
                        </div>
                    </div>
                    <script>
                        function showDetails(year) {{
                            alert('Showing detailed information for ' + year + ' period. In a full implementation, this would show paper abstracts, methodology details, and performance metrics.');
                        }}
                    </script>
                </body>
                </html>
                """
                viz_result["features"] = ["Interactive timeline", "Clickable periods", "Embedded citations"]

            elif viz_type == "taxonomy":
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{title}</title>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
                    <style>
                        .taxonomy-container {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                        }}
                        .node {{
                            cursor: pointer;
                        }}
                        .node circle {{
                            fill: #fff;
                            stroke: steelblue;
                            stroke-width: 3px;
                        }}
                        .node text {{
                            font: 12px sans-serif;
                        }}
                        .link {{
                            fill: none;
                            stroke: #ccc;
                            stroke-width: 2px;
                        }}
                        .tooltip {{
                            position: absolute;
                            text-align: center;
                            padding: 8px;
                            background: rgba(0, 0, 0, 0.8);
                            color: white;
                            border-radius: 4px;
                            pointer-events: none;
                            opacity: 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="taxonomy-container">
                        <h2>{title}</h2>
                        <div id="tree-container"></div>
                        <div class="tooltip"></div>
                    </div>
                    <script>
                        // Sample taxonomy data
                        const treeData = {{
                            "name": "AI Research",
                            "children": [
                                {{
                                    "name": "Deep Learning",
                                    "children": [
                                        {{"name": "CNN", "size": 15, "papers": ["LeCun et al., 1998", "He et al., 2016"]}},
                                        {{"name": "RNN", "size": 12, "papers": ["Hochreiter & Schmidhuber, 1997"]}},
                                        {{"name": "Transformer", "size": 20, "papers": ["Vaswani et al., 2017", "Devlin et al., 2019"]}}
                                    ]
                                }},
                                {{
                                    "name": "Machine Learning",
                                    "children": [
                                        {{"name": "Supervised", "size": 10}},
                                        {{"name": "Unsupervised", "size": 8}},
                                        {{"name": "Reinforcement", "size": 12}}
                                    ]
                                }}
                            ]
                        }};

                        const margin = {{top: 20, right: 90, bottom: 30, left: 90}},
                              width = 800 - margin.left - margin.right,
                              height = 500 - margin.top - margin.bottom;

                        const svg = d3.select("#tree-container").append("svg")
                            .attr("width", width + margin.right + margin.left)
                            .attr("height", height + margin.top + margin.bottom)
                            .append("g")
                            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                        const treemap = d3.tree().size([height, width]);
                        const root = d3.hierarchy(treeData, d => d.children);
                        treemap(root);

                        const link = svg.selectAll(".link")
                            .data(root.descendants().slice(1))
                            .enter().append("path")
                            .attr("class", "link")
                            .attr("d", d => {{
                                return "M" + d.y + "," + d.x
                                     + "C" + (d.y + d.parent.y) / 2 + "," + d.x
                                     + " " + (d.y + d.parent.y) / 2 + "," + d.parent.x
                                     + " " + d.parent.y + "," + d.parent.x;
                            }});

                        const node = svg.selectAll(".node")
                            .data(root.descendants())
                            .enter().append("g")
                            .attr("class", "node")
                            .attr("transform", d => "translate(" + d.y + "," + d.x + ")")
                            .on("mouseover", function(event, d) {{
                                const tooltip = d3.select(".tooltip");
                                tooltip.transition().duration(200).style("opacity", .9);
                                tooltip.html(d.data.name + (d.data.papers ? "<br/>Papers: " + d.data.papers.join(", ") : ""))
                                       .style("left", (event.pageX + 10) + "px")
                                       .style("top", (event.pageY - 28) + "px");
                            }})
                            .on("mouseout", function(d) {{
                                d3.select(".tooltip").transition().duration(500).style("opacity", 0);
                            }});

                        node.append("circle")
                            .attr("r", d => d.data.size || 5)
                            .style("fill", d => d.children ? "lightsteelblue" : "#fff");

                        node.append("text")
                            .attr("dy", ".35em")
                            .attr("x", d => d.children || d._children ? -13 : 13)
                            .style("text-anchor", d => d.children || d._children ? "end" : "start")
                            .text(d => d.data.name);
                    </script>
                </body>
                </html>
                """
                viz_result["features"] = ["Interactive tree diagram", "Hover tooltips", "Citation references"]

            elif viz_type == "performance_comparison":
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{title}</title>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
                    <style>
                        .chart-container {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                            max-width: 800px;
                        }}
                        .citation-note {{
                            font-size: 12px;
                            color: #666;
                            margin-top: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="chart-container">
                        <h2>{title}</h2>
                        <canvas id="performanceChart" width="400" height="200"></canvas>
                        <div class="citation-note">
                            Data sources: 
                            <a href="#ref1">[Smith et al., 2023]</a>, 
                            <a href="#ref2">[Johnson et al., 2022]</a>, 
                            <a href="#ref3">[Chen et al., 2024]</a>
                        </div>
                    </div>
                    <script>
                        const ctx = document.getElementById('performanceChart').getContext('2d');
                        const chart = new Chart(ctx, {{
                            type: 'bar',
                            data: {{
                                labels: ['Method A\\n[Smith et al.]', 'Method B\\n[Johnson et al.]', 'Method C\\n[Chen et al.]', 'Proposed\\n[Our work]'],
                                datasets: [{{
                                    label: 'Accuracy (%)',
                                    data: [85.2, 87.6, 89.1, 92.3],
                                    backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0'],
                                    borderColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0'],
                                    borderWidth: 1
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                plugins: {{
                                    legend: {{
                                        position: 'top',
                                    }},
                                    title: {{
                                        display: true,
                                        text: 'Performance Comparison Across Methods'
                                    }},
                                    tooltip: {{
                                        callbacks: {{
                                            afterLabel: function(context) {{
                                                const citations = [
                                                    'Citation: Smith, J. et al. (2023)',
                                                    'Citation: Johnson, A. et al. (2022)', 
                                                    'Citation: Chen, L. et al. (2024)',
                                                    'Citation: Our proposed method'
                                                ];
                                                return citations[context.dataIndex];
                                            }}
                                        }}
                                    }}
                                }},
                                scales: {{
                                    y: {{
                                        beginAtZero: true,
                                        max: 100,
                                        title: {{
                                            display: true,
                                            text: 'Performance (%)'
                                        }}
                                    }},
                                    x: {{
                                        title: {{
                                            display: true,
                                            text: 'Methods'
                                        }}
                                    }}
                                }}
                            }}
                        }});
                    </script>
                </body>
                </html>
                """
                viz_result["features"] = ["Interactive bar chart", "Citation tooltips", "Performance metrics"]

            viz_result["html_content"] = html_content
            return viz_result

        except Exception as e:
            logger.error(f"可视化创建失败: {e}")
            return {"error": str(e), "viz_type": viz_type, "timestamp": datetime.now().isoformat()}

    visualization_tool = FunctionTool(
        func=create_interactive_visualization,
        description="创建交互式可视化图表"
    )

    visualizer = AssistantAgent(
        name="VisualizationSpecialist",
        model_client=model_client,
        tools=[visualization_tool],
        system_message="""
        您是专业的学术可视化专家，擅长将复杂的研究数据转化为直观、交互式的可视化内容。

        ## 专业能力:
        1. **数据可视化**: 将抽象数据转化为清晰的图表和图形
        2. **交互设计**: 创建用户友好的交互式界面和功能
        3. **信息架构**: 设计合理的信息层次和展示逻辑
        4. **引用集成**: 将学术引用无缝集成到可视化中

        ## 可视化类型:
        **时间线图表**:
        - 技术发展历程和里程碑
        - 研究趋势和发展脉络
        - 关键论文发表时间序列
        - 交互式时间段探索

        **分类体系图**:
        - 技术分类树状图
        - 概念关系网络图
        - 方法论层次结构
        - 领域知识图谱

        **性能对比图**:
        - 方法性能基准对比
        - 多维度评估雷达图
        - 统计显著性可视化
        - 趋势分析和预测

        **引用网络图**:
        - 文献引用关系网络
        - 影响力传播路径
        - 研究团队合作网络
        - 知识流动可视化

        ## 交互功能设计:
        **用户交互**:
        - 悬停显示详细信息
        - 点击展开相关内容
        - 缩放和平移浏览
        - 过滤和搜索功能

        **引用集成**:
        - 内嵌式引用链接
        - 悬停显示引用详情
        - 点击跳转到参考文献
        - 引用上下文高亮

        **动态更新**:
        - 数据驱动的内容更新
        - 实时筛选和排序
        - 多视角切换展示
        - 响应式布局适配

        ## 技术实现:
        **前端技术栈**:
        - D3.js用于复杂图形绘制
        - Chart.js用于标准图表
        - HTML5/CSS3用于布局样式
        - JavaScript用于交互逻辑

        **设计原则**:
        - 信息密度合理，避免过载
        - 色彩搭配协调，突出重点
        - 布局清晰，层次分明
        - 操作直观，学习成本低

        ## 输出规范:
        **完整HTML文件**:
        - 包含所有必要的CSS和JavaScript
        - 自包含，无外部依赖（CDN除外）
        - 跨浏览器兼容
        - 移动设备友好

        **元数据信息**:
        - 数据来源和更新时间
        - 交互功能说明
        - 引用格式和链接
        - 使用许可和版权信息

        确保可视化内容的准确性、美观性和实用性，为学术报告增添专业价值。
        """,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )
    return visualizer
