import pandas as pd
import json
import os

# 读取EDA结果
eda_results_path = os.path.join('./output/', 'eda_results.json')

try:
    with open(eda_results_path, 'r') as f:
        eda_results = json.load(f)
        print('EDA结果读取成功。')
except FileNotFoundError:
    print(f'错误: 文件未找到 {eda_results_path}')
except json.JSONDecodeError:
    print('错误: JSON解码失败。')

# 读取分析报告
report_path = os.path.join('./reports/', 'analysis_report.json')
try:
    with open(report_path, 'r') as f:
        report = json.load(f)
        print('分析报告读取成功。')
except FileNotFoundError:
    print(f'错误: 文件未找到 {report_path}')
except json.JSONDecodeError:
    print('错误: JSON解码失败。')

# 输出模型性能
print('模型性能:')
print(f