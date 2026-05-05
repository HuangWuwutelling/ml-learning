import numpy as np

class LassoRegression:
    def __init__(self, lr=0.01, epochs=1000, alpha=1.0):
        self.lr = lr
        self.epochs = epochs
        self.alpha = alpha  # L1 正则化强度
        self.w = None
        self.b = None
        self.losses = []

    def fit(self, X, y):
        n_samples, n_features = X.shape
        self.w = np.zeros(n_features)
        self.b = 0

        for _ in range(self.epochs):
            y_pred = np.dot(X, self.w) + self.b

            # MSE + L1 正则化
            mse_loss = np.mean((y_pred - y) ** 2)
            reg_loss = self.alpha * np.sum(np.abs(self.w))
            loss = mse_loss + reg_loss
            self.losses.append(loss)

            # 梯度：d(MSE)/dw + α * sign(w)
            # sign(0) = 0 （次梯度处理）
            dw = (1 / n_samples) * np.dot(X.T, (y_pred - y)) + self.alpha * np.sign(self.w)
            db = (1 / n_samples) * np.sum(y_pred - y)

            self.w -= self.lr * dw
            self.b -= self.lr * db

    def predict(self, X):
        return np.dot(X, self.w) + self.b
