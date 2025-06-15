# 3. 建立线性回归模型
# 划分训练集和测试集
X = housing_data[['Area', 'Bedrooms', 'Bathrooms']]
Y = housing_data['Price']
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# 创建并训练模型
model = LinearRegression()
model.fit(X_train, Y_train)

# 4. 评估模型性能
Y_pred = model.predict(X_test)
R2 = r2_score(Y_test, Y_pred)
RMSE = np.sqrt(mean_squared_error(Y_test, Y_pred))

# 保存模型性能评估结果
performance = {'R²': R2, 'RMSE': RMSE}
with open(os.path.join(output_dir, 'model_performance.json'), 'w') as f:
    json.dump(performance, f)
logging.info('模型性能评估结果已保存到 ./output/model_performance.json')
