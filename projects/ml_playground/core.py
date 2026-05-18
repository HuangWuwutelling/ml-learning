"""
Algorithm registry, training/prediction wrappers, and model store.
"""
import uuid
import time
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error

from models.linear_regression import LinearRegression
from models.ridge_regression import RidgeRegression
from models.lasso_regression import LassoRegression
from models.logistic_regression import LogisticRegression
from models.decision_tree import DecisionTree
from models.random_forest import RandomForest
from models.gradient_boosting import GBDTClassifier, GBDTRegressor
from models.svm import SVM
from models.kmeans import KMeans
from models.dbscan import DBSCAN
from models.pca import PCA
from models.mlp import MLP


ALGORITHMS = {
    "linear_regression": {
        "name": "Linear Regression",
        "type": "regression",
        "description": "线性回归，最小二乘法 + 梯度下降",
        "class": LinearRegression,
        "default_params": {"lr": 0.01, "epochs": 1000},
        "needs_scaling": True,
        "supports_proba": False,
        "default_dataset": "california_housing",
    },
    "ridge": {
        "name": "Ridge Regression",
        "type": "regression",
        "description": "岭回归，L2 正则化缓解过拟合",
        "class": RidgeRegression,
        "default_params": {"lr": 0.01, "epochs": 1000, "alpha": 1.0},
        "needs_scaling": True,
        "supports_proba": False,
        "default_dataset": "california_housing",
    },
    "lasso": {
        "name": "Lasso Regression",
        "type": "regression",
        "description": "Lasso 回归，L1 正则化实现自动特征选择",
        "class": LassoRegression,
        "default_params": {"lr": 0.01, "epochs": 1000, "alpha": 1.0},
        "needs_scaling": True,
        "supports_proba": False,
        "default_dataset": "california_housing",
    },
    "logistic_regression": {
        "name": "Logistic Regression",
        "type": "classification",
        "description": "逻辑回归，Sigmoid 输出概率",
        "class": LogisticRegression,
        "default_params": {"lr": 0.01, "epochs": 1000},
        "needs_scaling": True,
        "supports_proba": True,
        "default_dataset": "breast_cancer",
    },
    "decision_tree": {
        "name": "Decision Tree",
        "type": "classification",
        "description": "CART 分类树，基尼系数分裂",
        "class": DecisionTree,
        "default_params": {"max_depth": 5, "min_samples_split": 2, "min_samples_leaf": 1},
        "needs_scaling": False,
        "supports_proba": True,
        "default_dataset": "iris",
    },
    "random_forest": {
        "name": "Random Forest",
        "type": "classification",
        "description": "随机森林，Bagging + 随机特征选择",
        "class": RandomForest,
        "default_params": {"n_estimators": 100, "max_depth": 5, "max_features": "sqrt"},
        "needs_scaling": False,
        "supports_proba": True,
        "default_dataset": "breast_cancer",
    },
    "gbdt_classifier": {
        "name": "GBDT Classifier",
        "type": "classification",
        "description": "梯度提升决策树（分类），串行回归树拟合残差",
        "class": GBDTClassifier,
        "default_params": {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3},
        "needs_scaling": False,
        "supports_proba": True,
        "default_dataset": "breast_cancer",
    },
    "gbdt_regressor": {
        "name": "GBDT Regressor",
        "type": "regression",
        "description": "梯度提升决策树（回归），串行回归树拟合残差",
        "class": GBDTRegressor,
        "default_params": {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3},
        "needs_scaling": False,
        "supports_proba": False,
        "default_dataset": "california_housing",
    },
    "svm": {
        "name": "SVM",
        "type": "classification",
        "description": "支持向量机，SMO 求解 + 核技巧",
        "class": SVM,
        "default_params": {"C": 1.0, "kernel": "rbf", "gamma": None},
        "needs_scaling": True,
        "supports_proba": True,
        "default_dataset": "breast_cancer",
    },
    "kmeans": {
        "name": "K-Means",
        "type": "clustering",
        "description": "K-Means 聚类，Lloyd 算法",
        "class": KMeans,
        "default_params": {"k": 3, "max_iters": 100, "random_state": 42},
        "needs_scaling": False,
        "supports_proba": False,
        "default_dataset": "mall_customers",
    },
    "dbscan": {
        "name": "DBSCAN",
        "type": "clustering",
        "description": "密度聚类，自动识别任意形状簇和噪声点",
        "class": DBSCAN,
        "default_params": {"eps": 0.5, "min_pts": 5},
        "needs_scaling": False,
        "supports_proba": False,
        "default_dataset": "make_moons",
    },
    "pca": {
        "name": "PCA",
        "type": "dimensionality_reduction",
        "description": "主成分分析，SVD 分解降维",
        "class": PCA,
        "default_params": {"n_components": 2},
        "needs_scaling": False,
        "supports_proba": False,
        "default_dataset": "digits",
    },
    "mlp": {
        "name": "MLP",
        "type": "classification",
        "description": "多层感知机，ReLU + Softmax + 反向传播",
        "class": MLP,
        "default_params": {"layer_dims": [64, 32, 10], "lr": 0.1, "epochs": 1000},
        "needs_scaling": True,
        "supports_proba": True,
        "default_dataset": "digits",
    },
}


class ModelStore:
    """In-memory model storage."""

    def __init__(self):
        self._models = {}

    def put(self, model_data):
        model_id = model_data["model_id"]
        self._models[model_id] = model_data
        return model_id

    def get(self, model_id):
        return self._models.get(model_id)

    def list(self):
        return [
            {
                "model_id": mid,
                "algorithm": data["algorithm"],
                "algorithm_name": data["algorithm_name"],
                "type": data["type"],
                "dataset": data["dataset"],
                "metrics": data.get("metrics", {}),
                "n_features": data.get("n_features", 0),
                "created_at": data.get("created_at", 0),
            }
            for mid, data in self._models.items()
        ]

    def remove(self, model_id):
        return self._models.pop(model_id, None)


model_store = ModelStore()


def _generate_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _compute_metrics(alg_type, model, X_test, y_test, X_train):
    """Compute evaluation metrics based on algorithm type."""
    if alg_type == "classification":
        y_pred = model.predict(X_test)
        if isinstance(model, SVM):
            y_pred = np.where(y_pred == -1, 0, 1)
        acc = float(accuracy_score(y_test, y_pred))
        return {
            "accuracy": round(acc, 4),
            "n_test_samples": len(y_test),
            "_y_test": y_test.tolist(),
            "_y_pred": y_pred.tolist(),
        }

    if alg_type == "regression":
        y_pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = float(r2_score(y_test, y_pred))
        return {
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "n_test_samples": len(y_test),
            "_y_test": y_test.tolist(),
            "_y_pred": y_pred.tolist(),
        }

    if alg_type == "clustering":
        result = {}
        if hasattr(model, "inertia_"):
            result["inertia"] = round(float(model.inertia_), 2)
        if hasattr(model, "n_clusters_"):
            result["n_clusters"] = int(model.n_clusters_)
        if hasattr(model, "n_noise_"):
            result["n_noise"] = int(model.n_noise_)
        result["_labels"] = model.labels_.tolist() if hasattr(model, "labels_") else []
        return result

    if alg_type == "dimensionality_reduction":
        return {
            "n_components": model.components_.shape[0],
            "explained_variance_ratio": [round(float(v), 4) for v in model.explained_variance_ratio_],
            "cumulative_variance": round(float(model.explained_variance_ratio_.sum()), 4),
        }

    return {}


def _normalize_proba(alg_type, model, X):
    """Get probabilities in consistent (n, n_classes) format."""
    if not (alg_type == "classification" and hasattr(model, "predict_proba")):
        return None
    try:
        proba = np.asarray(model.predict_proba(X))
    except Exception:
        return None
    if proba.ndim == 1:
        proba = np.column_stack([1 - proba, proba])
    return proba.tolist()


def train(algorithm_name, dataset_name, params=None, dataset_loader=None):
    """Unified training: load data → split/scale → fit → evaluate → store."""
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm_name}")

    algo = ALGORITHMS[algorithm_name]
    algo_class = algo["class"]
    algo_type = algo["type"]

    model_params = dict(algo["default_params"])
    if params:
        model_params.update(params)

    if dataset_loader is not None:
        X, y, ds_meta = dataset_loader()
    else:
        from .datasets import load_dataset
        X, y, ds_meta = load_dataset(dataset_name)

    model_id = _generate_id(algorithm_name[:3])

    result = {
        "model_id": model_id,
        "algorithm": algorithm_name,
        "algorithm_name": algo["name"],
        "type": algo_type,
        "dataset": dataset_name,
        "params": model_params,
        "feature_names": ds_meta.get("feature_names", []),
        "n_features": ds_meta.get("n_features", X.shape[1]),
        "n_samples": X.shape[0],
        "n_classes": ds_meta.get("n_classes", None),
        "created_at": time.time(),
    }

    if algo_type in ("classification", "regression"):
        if y is None:
            raise ValueError(f"Dataset '{dataset_name}' has no labels, but '{algorithm_name}' requires supervision.")

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = None
        if algo["needs_scaling"]:
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

        model = algo_class(**model_params)
        model.fit(X_train, y_train)

        metrics = _compute_metrics(algo_type, model, X_test, y_test, X_train)
        result["metrics"] = {k: v for k, v in metrics.items() if not k.startswith("_")}
        result["_plot_data"] = {k: v for k, v in metrics.items() if k.startswith("_")}
        result["_scaler"] = scaler
        result["_model"] = model
        result["_X_train"] = X_train
        result["_y_train"] = y_train

    else:
        model = algo_class(**model_params)
        model.fit(X)

        metrics = _compute_metrics(algo_type, model, None, None, X)
        result["metrics"] = metrics
        result["_model"] = model
        result["_X_train"] = X
        result["_y_train"] = y
        result["_plot_data"] = {"_labels": metrics.pop("_labels", [])}

    model_store.put(result)
    return result


def predict(model_id, features):
    """Run inference with a trained model."""
    data = model_store.get(model_id)
    if data is None:
        raise ValueError(f"Model not found: {model_id}")

    model = data["_model"]
    alg_type = data["type"]
    algo_name = data["algorithm"]

    X = np.array(features, dtype=float)
    if X.ndim == 1:
        X = X.reshape(1, -1)

    scaler = data.get("_scaler")
    if scaler is not None:
        X = scaler.transform(X)

    if algo_name == "pca":
        return {"predictions": model.transform(X).tolist(), "type": "dimensionality_reduction"}

    if algo_name == "dbscan":
        raise ValueError("DBSCAN does not support prediction on new data. Use the 'fit_predict' approach on the full dataset instead.")

    pred = model.predict(X)
    if alg_type == "classification" and isinstance(model, SVM):
        pred = np.where(pred == -1, 0, 1)

    result = {"predictions": pred.tolist() if hasattr(pred, "tolist") else pred, "type": alg_type}

    if alg_type == "classification":
        proba = _normalize_proba(alg_type, model, X)
        if proba is not None:
            result["probabilities"] = proba

    return result
