import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 读取生成的房屋数据
housing_data = pd.read_csv('./output/housing_data.csv')

# 1. 数据基本统计信息
stats = housing_data.describe()
# 保存基本统计信息
stats.to_csv('./output/housing_data_stats.csv')

# 2. 相关性分析
correlation = housing_data.corr()
# 保存相关性矩阵
correlation.to_csv('./output/housing_data_correlation.csv')

# 3. 数据分布可视化
plt.figure(figsize=(10, 5))
# 面积分布
sns.histplot(housing_data['Area'], bins=30, kde=True)
plt.title('Area Distribution')
plt.xlabel('Area (sqm)')
plt.ylabel('Frequency')
plt.savefig('./plots/area_distribution.png')
plt.close()

plt.figure(figsize=(10, 5))
# 房价分布
sns.histplot(housing_data['Price'], bins=30, kde=True)
plt.title('Price Distribution')
plt.xlabel('Price')
plt.ylabel('Frequency')
plt.savefig('./plots/price_distribution.png')
plt.close()