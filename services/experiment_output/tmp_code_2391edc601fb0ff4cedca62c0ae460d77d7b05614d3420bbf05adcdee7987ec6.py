import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# 生成模拟房屋数据的函数（包含二次关系）
def generate_quadratic_housing_data(num_samples: int) -> pd.DataFrame:
    """生成模拟房屋数据，包括面积、房价及其他特征，模拟二次关系"""
    np.random.seed(42)  # 设置随机种子以保证结果可重现
    area = np.random.randint(50, 301, size=num_samples)  # 面积数据（50-300平方米）
    price = 2000 * area + 0.5 * (area ** 2) + np.random.normal(0, 20000, size=num_samples)  # 二次关系加上噪声
    bedrooms = np.random.randint(1, 6, size=num_samples)  # 其他特征（卧室数量）
    housing_data = pd.DataFrame({
        'Area': area,
        'Price': price,
        'Bedrooms': bedrooms
    })
    return housing_data

# 生成20个样本的房屋数据
housing_data_quadratic = generate_quadratic_housing_data(20)

# 准备数据
X = housing_data_quadratic[['Area']]
Y = housing_data_quadratic['Price']

# 划分训练集与测试集
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# 多项式特征转换
poly = PolynomialFeatures(degree=2)
X_poly_train = poly.fit_transform(X_train)
X_poly_test = poly.transform(X_test)

# 建立线性回归模型
model_poly = LinearRegression()
model_poly.fit(X_poly_train, Y_train)

# 进行预测
Y_pred = model_poly.predict(X_poly_test)

# 评估模型性能
r2 = r2_score(Y_test, Y_pred)
rmse = mean_squared_error(Y_test, Y_pred, squared=False)

# 打印性能指标
print(f'R²: {r2}')
print(f'RMSE: {rmse}')

# 可视化实际值与预测值的对比
plt.figure(figsize=(10, 5))
plt.scatter(X_test, Y_test, color='blue', label='实际值')
plt.scatter(X_test, Y_pred, color='red', label='预测值')
plt.plot(X_test, Y_pred, color='red')
plt.title('实际值与预测值的对比')
plt.xlabel('面积 (sqm)')
plt.ylabel('房价')
plt.legend()
plt.savefig('./plots/comparison_actual_predicted.png')
plt.close()