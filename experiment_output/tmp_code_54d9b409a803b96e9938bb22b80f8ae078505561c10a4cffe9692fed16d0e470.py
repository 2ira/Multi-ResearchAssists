import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import os
import json

# 创建输出和绘图目录
output_dir = './output/'
plots_dir = './plots/'
reports_dir = './reports/'

os.makedirs(output_dir, exist_ok=True)
os.makedirs(plots_dir, exist_ok=True)
os.makedirs(reports_dir, exist_ok=True)

# 生成模拟房屋数据
np.random.seed(0)  # 为可重复性设置随机种子

n_samples = 1000
area = np.random.randint(50, 301, size=n_samples)  # 面积范围 50-300平方米
price = area * 3000 + np.random.normal(0, 15000, size=n_samples)  # 计算价格并添加噪声
other_feature = np.random.rand(n_samples) * 100  # 其他特征

# 创建DataFrame
housing_data = pd.DataFrame({'Area': area, 'Price': price, 'OtherFeature': other_feature})

# 保存生成的数据到CSV文件
housing_data.to_csv(os.path.join(output_dir, 'housing_data.csv'), index=False)

# 探索性数据分析（EDA）
# 1. 数据基本统计信息
stats = housing_data.describe()  # 获取描述性统计

# 2. 相关性分析
correlation = housing_data.corr()

# 3. 数据分布可视化
plt.figure(figsize=(10, 6))
sns.histplot(housing_data['Price'], bins=30)
plt.title('房价分布图')
plt.xlabel('房价')
plt.ylabel('频率')
plt.savefig(os.path.join(plots_dir, 'price_distribution.png'))
plt.close()

# 保存EDA结果
eda_results = {'statistics': stats.to_dict(), 'correlation': correlation.to_dict()}
with open(os.path.join(output_dir, 'eda_results.json'), 'w') as f:
    json.dump(eda_results, f)

# 建立线性回归模型
X = housing_data[['Area', 'OtherFeature']]
y = housing_data['Price']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

model = LinearRegression()
model.fit(X_train, y_train)

# 评估模型性能
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r_squared = r2_score(y_test, y_pred)

# 残差分析
residuals = y_test - y_pred

# 创建可视化图表
# 散点图显示面积与房价关系
plt.figure(figsize=(10, 6))
sns.scatterplot(x=X_test['Area'], y=y_test, color='blue', label='实际房价')
sns.scatterplot(x=X_test['Area'], y=y_pred, color='red', label='预测房价')
plt.title('面积与房价关系图')
plt.xlabel('面积 (平方米)')
plt.ylabel('房价')
plt.legend()
plt.savefig(os.path.join(plots_dir, 'area_vs_price.png'))
plt.close()

# 残差图
plt.figure(figsize=(10, 6))
sns.scatterplot(x=y_pred, y=residuals, color='purple')
plt.hlines(0, min(y_pred), max(y_pred), colors='red', linestyles='--')
plt.title('残差图')
plt.xlabel('预测房价')
plt.ylabel('残差')
plt.savefig(os.path.join(plots_dir, 'residuals_plot.png'))
plt.close()

# 特征重要性图
importance = model.coef_
features = X.columns
plt.figure(figsize=(10, 6))
sns.barplot(x=features, y=importance)
plt.title('特征重要性')
plt.xlabel('特征')
plt.ylabel('重要性')
plt.savefig(os.path.join(plots_dir, 'feature_importance.png'))
plt.close()

# 生成分析报告
report = {
    'model_performance': {'R_squared': r_squared, 'RMSE': rmse},
    'key_findings': '房屋面积与房价之间存在正相关关系。'
}
with open(os.path.join(reports_dir, 'analysis_report.json'), 'w') as f:
    json.dump(report, f)
