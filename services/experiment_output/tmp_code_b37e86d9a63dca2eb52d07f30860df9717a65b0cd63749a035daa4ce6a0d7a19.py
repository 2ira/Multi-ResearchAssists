import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import os
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. 生成模拟房屋数据
np.random.seed(42)
num_samples = 1000
area = np.random.uniform(50, 300, num_samples)
noise = np.random.normal(0, 50000, num_samples)
price = (area * 3000) + noise  # 假设每平方米3000元

# 创建其他特征（如卧室数量、浴室数量等）
num_bedrooms = np.random.randint(1, 5, num_samples)
num_bathrooms = np.random.randint(1, 3, num_samples)

# 创建DataFrame
housing_data = pd.DataFrame({
    'Area': area,
    'Price': price,
    'Bedrooms': num_bedrooms,
    'Bathrooms': num_bathrooms
})

# 输出数据到 ./output/ 目录
output_dir = './output/'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

housing_data.to_csv(os.path.join(output_dir, 'housing_data.csv'), index=False)
logging.info('模拟房屋数据已生成并保存到 ./output/housing_data.csv')
