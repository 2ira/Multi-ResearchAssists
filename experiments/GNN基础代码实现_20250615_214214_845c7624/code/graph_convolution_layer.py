#!/usr/bin/env python3
"""
实现图卷积层，定义图卷积操作并实现相应的代码

生成时间: 2025-06-15 21:42:49
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 设置随机种子以保证结果可重现
np.random.seed(42)

# 配置matplotlib
plt.style.use('seaborn-v0_8')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

class Graph:
    def __init__(self):
        """初始化图的数据结构，包括节点和边的特征"""
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id, features):
        """添加节点及其特征"""
        self.nodes[node_id] = features

    def add_edge(self, node1, node2, weight=1.0):
        """添加边及其权重"""
        if node1 not in self.edges:
            self.edges[node1] = {}
        self.edges[node1][node2] = weight

    def get_neighbors(self, node_id):
        """获取指定节点的邻居节点"""
        return list(self.edges.get(node_id, {}).keys())

class GraphConvolutionLayer:
    def __init__(self, input_dim, output_dim):
        """初始化图卷积层
        
        Args:
            input_dim: 输入特征维度
            output_dim: 输出特征维度
        """
        self.weights = np.random.rand(input_dim, output_dim)
        self.bias = np.random.rand(output_dim)

    def forward(self, graph, node_features):
        """前向传播
        
        Args:
            graph: Graph对象，包含节点和边信息
            node_features: 节点特征矩阵

        Returns:
            更新后的节点特征矩阵
        """
        updated_features = np.zeros((len(graph.nodes), self.weights.shape[1]))

        for node_id in graph.nodes:
            neighbors = graph.get_neighbors(node_id)
            neighbor_features = np.array([node_features[neighbor] for neighbor in neighbors])
            if len(neighbor_features) > 0:
                aggregated_features = np.mean(neighbor_features, axis=0)
            else:
                aggregated_features = np.zeros(node_features.shape[1])
            
            updated_features[node_id] = np.dot(aggregated_features, self.weights) + self.bias
        
        return updated_features

def main():
    """主函数：测试图卷积层"""
    print("开始执行任务: 实现图卷积层，定义图卷积操作并实现相应的代码")
    
    # 创建图实例并添加节点和边
    graph = Graph()
    graph.add_node(0, np.array([1.0, 2.0]))
    graph.add_node(1, np.array([2.0, 3.0]))
    graph.add_edge(0, 1, weight=1.0)

    # 创建图卷积层
    gcn_layer = GraphConvolutionLayer(input_dim=2, output_dim=2)
    
    # 获取节点特征
    node_features = np.array([graph.nodes[i] for i in range(len(graph.nodes))])
    
    # 前向传播
    updated_features = gcn_layer.forward(graph, node_features)
    print("更新后的节点特征矩阵:", updated_features)

if __name__ == "__main__":
    main()