import numpy as np
from collections import Counter


class RandomForest:
    """
    随机森林（分类），基于 DecisionTree 实现 Bagging + 特征随机采样。

    参数
    ----
    n_estimators : int
        决策树数量，默认 100
    max_depth : int
        每棵树的最大深度，默认 5
    max_features : str or int
        每棵树每次分裂考虑的特征数：
        - 'sqrt': sqrt(n_features)，分类任务默认
        - 'log2': log2(n_features)
        - int: 直接指定
    min_samples_split : int
        内部节点再划分所需最小样本数，默认 2
    min_samples_leaf : int
        叶子节点最少样本数，默认 1
    random_state : int
        随机种子，默认 42
    oob_score : bool
        是否计算袋外误差，默认 True
    """
    def __init__(self, n_estimators=100, max_depth=5, max_features='sqrt',
                 min_samples_split=2, min_samples_leaf=1,
                 random_state=42, oob_score=True):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_features = max_features
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state
        self.oob_score = oob_score
        self.trees = []
        self.feature_importances_ = None
        self.oob_error_ = None

    def _get_max_features(self, n_features):
        """根据模式计算每棵树用的特征数"""
        if isinstance(self.max_features, int):
            return max(1, min(self.max_features, n_features))
        elif self.max_features == 'sqrt':
            return max(1, int(np.sqrt(n_features)))
        elif self.max_features == 'log2':
            return max(1, int(np.log2(n_features)))
        else:
            return n_features

    def fit(self, X, y):
        np.random.seed(self.random_state)
        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))
        n_features_subset = self._get_max_features(n_features)

        self.trees = []
        # 记录每个样本被哪些树 OOB（用于计算 OOB 误差）
        oob_mask = np.zeros((n_samples, self.n_estimators), dtype=bool)

        for i in range(self.n_estimators):
            # Bootstrap 采样（有放回）
            rng = np.random.RandomState(self.random_state + i)
            indices = rng.choice(n_samples, n_samples, replace=True)
            oob_idx = np.setdiff1d(np.arange(n_samples), indices)
            X_boot, y_boot = X[indices], y[indices]

            # 记录 OOB
            oob_mask[oob_idx, i] = True

            # 随机选择特征子集
            feat_idx = rng.choice(n_features, n_features_subset, replace=False)
            feat_idx.sort()

            # 训练决策树（只在选中特征上训练）
            tree = _DecisionTreeWrapper(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
            )
            tree.fit(X_boot[:, feat_idx], y_boot, feat_idx, n_total_features=n_features)
            self.trees.append(tree)

        # --- 特征重要性：所有树的平均值 ---
        self.feature_importances_ = np.zeros(n_features)
        for tree in self.trees:
            self.feature_importances_ += tree.feature_importances_
        self.feature_importances_ /= self.n_estimators

        # --- OOB 误差 ---
        if self.oob_score:
            oob_preds = np.full((n_samples, self.n_estimators), -1)
            for i, tree in enumerate(self.trees):
                if oob_mask[:, i].sum() > 0:
                    oob_preds[oob_mask[:, i], i] = tree.predict(X[oob_mask[:, i]])
            self.oob_error_ = 0
            for j in range(n_samples):
                mask = oob_preds[j] != -1
                if mask.sum() > 0:
                    votes = Counter(oob_preds[j][mask])
                    pred = votes.most_common(1)[0][0]
                    if pred != y[j]:
                        self.oob_error_ += 1
            self.oob_error_ /= n_samples

    def predict(self, X):
        """多数投票"""
        preds = np.array([tree.predict(X) for tree in self.trees])  # (n_estimators, n_samples)
        y_pred = np.zeros(X.shape[0], dtype=int)
        for i in range(X.shape[0]):
            votes = Counter(preds[:, i])
            y_pred[i] = votes.most_common(1)[0][0]
        return y_pred

    def predict_proba(self, X):
        """各类概率 = 所有树的平均概率"""
        probas = np.array([tree.predict_proba(X) for tree in self.trees])
        return probas.mean(axis=0)


class _DecisionTreeWrapper:
    """
    决策树包装器，支持特征子集。
    内部用 DecisionTree 实现，但保存特征映射以正确计算重要性。
    """
    def __init__(self, max_depth=5, min_samples_split=2, min_samples_leaf=1):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.feat_idx_ = None
        self.feature_importances_ = None
        self._tree = None

    def fit(self, X, y, feat_idx, n_total_features=None):
        self.feat_idx_ = feat_idx
        dt = _SimpleDecisionTree(
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
        )
        dt.fit(X, y)
        # 将局部特征重要性映射回全局特征空间
        n_total = n_total_features if n_total_features else feat_idx.max() + 1
        global_imp = np.zeros(n_total)
        for local_i, global_i in enumerate(self.feat_idx_):
            global_imp[global_i] = dt.feature_importances_[local_i]
        self.feature_importances_ = global_imp
        self._tree = dt._tree if hasattr(dt, '_tree') else dt.tree_

    def predict(self, X):
        dt = _SimpleDecisionTree()
        dt._tree = self._tree
        return dt.predict(X[:, self.feat_idx_])

    def predict_proba(self, X):
        dt = _SimpleDecisionTree()
        dt._tree = self._tree
        dt.n_classes_ = len(np.unique(self._tree['value']))
        return dt.predict_proba(X[:, self.feat_idx_])


class _SimpleDecisionTree:
    """
    精简版决策树，复用 DecisionTree 的核心逻辑。
    去掉 print_tree 等非必需功能，保持接口一致。
    """
    def __init__(self, max_depth=5, min_samples_split=2, min_samples_leaf=1):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.n_classes_ = None
        self.n_features_ = None
        self.feature_importances_ = None
        self._impurity_reductions = None
        self._tree = None

    def fit(self, X, y):
        n_samples, self.n_features_ = X.shape
        self.n_classes_ = len(np.unique(y))
        self._impurity_reductions = np.zeros(self.n_features_)
        self._tree = self._build_tree(X, y, depth=0)
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

    def _gini(self, y):
        _, counts = np.unique(y, return_counts=True)
        p = counts / counts.sum()
        return 1 - (p ** 2).sum()

    def _cart_split(self, X, y):
        best_gini = float('inf')
        best_feat, best_thresh = None, None
        for f in range(self.n_features_):
            col = X[:, f]
            values = np.unique(col)
            if len(values) < 2:
                continue
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
        n_samples = len(y)
        _, counts = np.unique(y, return_counts=True)
        value = np.zeros(self.n_classes_)
        for cls, cnt in zip(*np.unique(y, return_counts=True)):
            value[cls] = cnt

        current_gini = self._gini(y)
        node = {
            'value': value,
            'n_samples': n_samples,
            'gini': current_gini,
            'prediction': np.argmax(value),
        }

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

        reduction = current_gini - gini
        self._impurity_reductions[feat] += reduction * n_samples

        node['feature_idx'] = feat
        node['threshold'] = thresh
        node['left'] = self._build_tree(X_left, y_left, depth + 1)
        node['right'] = self._build_tree(X_right, y_right, depth + 1)
        return node

    def _traverse(self, x, node):
        if 'left' not in node:
            return node
        if x[node['feature_idx']] <= node['threshold']:
            return self._traverse(x, node['left'])
        return self._traverse(x, node['right'])

    def _predict_one(self, x, node):
        return self._traverse(x, node)['prediction']
