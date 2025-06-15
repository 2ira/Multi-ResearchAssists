from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# 准备数据
X = housing_data[['Area', 'Bedrooms']]
Y = housing_data['Price']

# 划分训练集与测试集
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# 建立线性回归模型
model = LinearRegression()
model.fit(X_train, Y_train)

# 进行预测
Y_pred = model.predict(X_test)

# 评估模型性能
r2 = r2_score(Y_test, Y_pred)
rmse = mean_squared_error(Y_test, Y_pred, squared=False)

# 保存模型性能指标
performance = pd.DataFrame({'R²': [r2], 'RMSE': [rmse]})
performance.to_csv('./output/model_performance.csv', index=False)