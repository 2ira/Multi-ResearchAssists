# 6. 生成分析报告
report_content = f"模型性能总结:\nR²: {R2:.2f}\nRMSE: {RMSE:.2f}\n\n关键发现:\n1. 面积与房价呈正相关。\n2. 模型在测试集上的表现较好。\n\n改进建议:\n1. 收集更多特征以提高模型性能。\n2. 考虑使用其他回归模型进行比较。\n"

with open('./reports/analysis_report.md', 'w') as report_file:
    report_file.write(report_content)

logging.info('分析报告已保存到 ./reports/analysis_report.md')
