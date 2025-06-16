import numpy as np
import pandas as pd
import random

# 设置随机种子以保证结果可重现
np.random.seed(42)

# 生成模拟房屋数据的函数
def generate_housing_data(num_samples: int) -> pd.DataFrame:
    """生成模拟房屋数据，包括面积、房价及其他特征"""
    # 生成面积数据（50-300平方米）
    area = np.random.randint(50, 301, size=num_samples)
    # 生成价格数据（线性关系加上噪声）
    price = area * 3000 + np.random.normal(0, 30000, size=num_samples)
    # 生成其他特征（例如卧室数量）
    bedrooms = np.random.randint(1, 6, size=num_samples)
    # 创建数据框
    housing_data = pd.DataFrame({
        'Area': area,
        'Price': price,
        'Bedrooms': bedrooms
    })
    return housing_data

# 生成1000个样本的房屋数据
housing_data = generate_housing_data(1000)
# 保存数据到./output目录
housing_data.to_csv('./output/housing_data.csv', index=False)