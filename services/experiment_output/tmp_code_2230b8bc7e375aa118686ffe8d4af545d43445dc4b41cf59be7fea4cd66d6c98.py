# 进行残差分析
residuals = Y_test - Y_pred

# 创建残差散点图
plt.figure(figsize=(10, 5))
sns.scatterplot(x=Y_pred, y=residuals)
plt.axhline(0, color='red', linestyle='--')
plt.title('Residuals vs Predicted Values')
plt.xlabel('Predicted Values')
plt.ylabel('Residuals')
plt.savefig('./plots/residuals_plot.png')
plt.close()