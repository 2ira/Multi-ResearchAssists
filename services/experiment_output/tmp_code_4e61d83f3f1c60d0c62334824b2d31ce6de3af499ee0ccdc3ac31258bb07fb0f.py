# 生成分析报告
report_content = f"模型性能总结:\nR²: {r2}\nRMSE: {rmse}\n\n关键发现:\n1. 房屋面积与房价呈正相关关系。\n2. 模型在测试集上的表现良好。\n\n改进建议:\n1. 可以考虑更多的特征，如地理位置。\n2. 增加数据量以提高模型的准确性。"

with open('./reports/analysis_report.md', 'w') as f:
    f.write(report_content)