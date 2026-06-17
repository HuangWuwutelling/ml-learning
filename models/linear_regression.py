import numpy as np

class LinearRegression:
    def __init__(self, lr=0.01, epochs=1000):
        self.lr = lr # 学习率：控制每次参数更新的步长
        self.epochs = epochs # 训练轮数：整个数据要训练多少次
        self.w = None # 权重参数（w），初始化为 None，后面会赋值
        self.b = None# 偏置参数（b）
        self.losses = []   # 用来记录每一轮训练的损失（误差）

    def fit(self, X, y):
        """
        训练模型（核心函数）
        X: 特征数据 (n_samples, n_features)
        y: 标签数据 (n_samples,)
        """
        n_samples, n_features = X.shape # 获取样本数量和特征数量

        self.w = np.zeros(n_features) # 初始化权重为 0（长度 = 特征数量）
        self.b = 0 # 初始化偏置为 0
        # 开始梯度下降训练
        for _ in range(self.epochs):
            # 计算预测值：y_hat = Xw + b
            y_pred = np.dot(X, self.w) + self.b

            # 计算当前损失（均方误差 MSE）
            loss = np.mean((y_pred - y) ** 2)
            # 保存损失，用于后续画图
            self.losses.append(loss)
            # 计算权重 w 的梯度（偏导数）
            # 表示：误差对 w 的影响方向
            dw = (1 / n_samples) * np.dot(X.T, (y_pred - y))
            # 计算偏置 b 的梯度
            db = (1 / n_samples) * np.sum(y_pred - y)

            #  更新权重（沿负梯度方向移动）
            self.w -= self.lr * dw
            # 更新偏置
            self.b -= self.lr * db

    def predict(self, X):
        # 使用训练好的 w 和 b 计算预测值
        return np.dot(X, self.w) + self.b