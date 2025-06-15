# 2. 进行探索性数据分析
# 数据基本统计信息
stats = housing_data.describe()
stats.to_csv(os.path.join(output_dir, 'data_statistics.csv'))
logging.info('数据基本统计信息已保存到 ./output/data_statistics.csv')

# 相关性分析
correlation = housing_data.corr()
correlation.to_csv(os.path.join(output_dir, 'correlation_matrix.csv'))
logging.info('相关性分析已保存到 ./output/correlation_matrix.csv')

# 数据分布可视化
plt.figure(figsize=(10, 6))
 sns.histplot(housing_data['Price'], bins=30, kde=True)
 plt.title('房价分布图')
 plt.xlabel('房价')
 plt.ylabel('频率')
 plt.savefig('./plots/price_distribution.png')
 logging.info('房价分布图已保存到 ./plots/price_distribution.png')
