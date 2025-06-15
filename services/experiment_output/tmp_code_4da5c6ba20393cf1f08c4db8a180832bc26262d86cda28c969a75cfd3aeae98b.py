# 5. 创建可视化图表
# 散点图显示面积与房价关系
plt.figure(figsize=(10, 6))
plt.scatter(housing_data['Area'], housing_data['Price'], color='blue', alpha=0.5)
plt.title('面积与房价关系图')
plt.xlabel('面积 (平方米)')
plt.ylabel('房价')
plt.plot(X_test['Area'], Y_pred, color='red')  # 回归线
plt.savefig('./plots/area_price_relationship.png')
logging.info('面积与房价关系图已保存到 ./plots/area_price_relationship.png')

# 残差分析
residuals = Y_test - Y_pred
plt.figure(figsize=(10, 6))
sns.scatterplot(x=Y_pred, y=residuals)
plt.axhline(0, color='red', linestyle='--')
plt.title('残差图')
plt.xlabel('预测房价')
plt.ylabel('残差')
plt.savefig('./plots/residuals_plot.png')
logging.info('残差图已保存到 ./plots/residuals_plot.png')

# 特征重要性图
importance = model.coef_
features = X.columns
plt.figure(figsize=(10, 6))
sns.barplot(x=importance, y=features)
plt.title('特征重要性图')
plt.xlabel('系数值')
plt.ylabel('特征')
plt.savefig('./plots/feature_importance.png')
logging.info('特征重要性图已保存到 ./plots/feature_importance.png')
