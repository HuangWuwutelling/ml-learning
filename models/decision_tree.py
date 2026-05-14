import numpy as np


class DecisionTree:
    """
    CART 决策树（分类），纯 numpy 实现。

    参数
    ----
    max_depth : int
        树的最大深度，默认 5
    min_samples_split : int
        内部节点再划分所需最小样本数，默认 2
    min_samples_leaf : int
        叶子节点最少样本数，默认 1
    """
    def __init__(self, max_depth=5, min_samples_split=2, min_samples_leaf=1):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.tree_ = None
        self.n_classes_ = None
        self.n_features_ = None
        self.feature_importances_ = None

    def fit(self, X, y):
        n_samples, self.n_features_ = X.shape
        self.n_classes_ = len(np.unique(y))
        # 统计每个特征的总 Gini 下降（for feature importance）
        self._impurity_reductions = np.zeros(self.n_features_)
        self._tree = self._build_tree(X, y, depth=0)
        # 归一化特征重要性
        total = self._impurity_reductions.sum()
        self.feature_importances_ = (
            self._impurity_reductions / total if total > 0
            else np.ones(self.n_features_) / self.n_features_
        )

    def predict(self, X):
        return np.array([self._predict_one(x, self._tree) for x in X])

    def predict_proba(self, X):
        probas = []
        for x in X:
            node = self._traverse(x, self._tree)
            probas.append(node['value'] / node['n_samples'])
        return np.array(probas)

    # ---------- helper ----------

    def _gini(self, y):
        """计算 Gini 不纯度"""
        _, counts = np.unique(y, return_counts=True)
        p = counts / counts.sum()
        return 1 - (p ** 2).sum()

    def _cart_split(self, X, y):
        """遍历所有特征和可能切分点，找到最优切分"""
        best_gini = float('inf')
        best_feat, best_thresh = None, None

        for f in range(self.n_features_):
            col = X[:, f]
            values = np.unique(col)
            if len(values) < 2:
                continue
            # 候选切分点：相邻值的中点
            candidates = (values[:-1] + values[1:]) / 2
            for thresh in candidates:
                mask = col <= thresh
                if mask.sum() < self.min_samples_leaf or (~mask).sum() < self.min_samples_leaf:
                    continue
                y_left, y_right = y[mask], y[~mask]
                gini = (len(y_left) * self._gini(y_left) +
                        len(y_right) * self._gini(y_right)) / len(y)
                if gini < best_gini:
                    best_gini = gini
                    best_feat = f
                    best_thresh = thresh
        return best_feat, best_thresh, best_gini

    def _build_tree(self, X, y, depth):
        n_samples, n_classes = len(y), self.n_classes_
        _, counts = np.unique(y, return_counts=True)
        value = np.zeros(n_classes)
        for cls, cnt in zip(*np.unique(y, return_counts=True)):
            value[cls] = cnt

        # Gini 不纯度
        current_gini = self._gini(y)

        node = {
            'value': value,
            'n_samples': n_samples,
            'gini': current_gini,
            'prediction': np.argmax(value),
        }

        # 停止条件
        if (depth >= self.max_depth
                or n_samples < self.min_samples_split
                or current_gini == 0):
            return node

        feat, thresh, gini = self._cart_split(X, y)
        if feat is None:
            return node

        mask = X[:, feat] <= thresh
        X_left, y_left = X[mask], y[mask]
        X_right, y_right = X[~mask], y[~mask]

        # 记录 Gini 下降（用于特征重要性）
        reduction = current_gini - gini
        self._impurity_reductions[feat] += reduction * n_samples

        node['feature_idx'] = feat
        node['threshold'] = thresh
        node['left'] = self._build_tree(X_left, y_left, depth + 1)
        node['right'] = self._build_tree(X_right, y_right, depth + 1)
        return node

    def _traverse(self, x, node):
        """递归下降到叶子节点"""
        if 'left' not in node:
            return node
        if x[node['feature_idx']] <= node['threshold']:
            return self._traverse(x, node['left'])
        return self._traverse(x, node['right'])

    def _predict_one(self, x, node):
        return self._traverse(x, node)['prediction']

    # ---------- 树结构打印 ----------

    def print_tree(self, node=None, indent=""):
        """以文本形式打印树结构"""
        if node is None:
            node = self._tree
        if 'left' in node:
            print(f"{indent}[特征 {node['feature_idx']} <= {node['threshold']:.2f}]")
            print(f"{indent}  ├─ 左分支:")
            self.print_tree(node['left'], indent + "  │ ")
            print(f"{indent}  └─ 右分支:")
            self.print_tree(node['right'], indent + "    ")
        else:
            pred = np.argmax(node['value'])
            dist = node['value'].astype(int)
            print(f"{indent}→ 类别 {pred}  (样本分布: {dist})")
