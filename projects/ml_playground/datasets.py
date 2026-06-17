"""
Built-in dataset loaders. Each loader returns (X, y, metadata).
y can be None for unsupervised datasets.
"""
import os
import numpy as np
import pandas as pd
from sklearn.datasets import (
    load_breast_cancer,
    load_iris,
    load_digits,
    fetch_california_housing,
    make_moons,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _get_data_path(name):
    return os.path.join(DATA_DIR, name)


def load_breast_cancer_dataset():
    bc = load_breast_cancer()
    X = bc.data.astype(float)
    y = bc.target.astype(int)
    return X, y, {
        "feature_names": list(bc.feature_names),
        "target_names": list(bc.target_names),
        "n_features": X.shape[1],
        "n_classes": len(np.unique(y)),
    }


def load_iris_dataset():
    iris = load_iris()
    X = iris.data.astype(float)
    y = iris.target.astype(int)
    return X, y, {
        "feature_names": list(iris.feature_names),
        "target_names": list(iris.target_names),
        "n_features": X.shape[1],
        "n_classes": len(np.unique(y)),
    }


def load_digits_dataset():
    digits = load_digits()
    X = digits.data.astype(float)
    y = digits.target.astype(int)
    return X, y, {
        "n_features": X.shape[1],
        "n_classes": len(np.unique(y)),
        "description": "1797 samples, 64 features (8x8 grayscale)",
    }


def load_california_housing_dataset():
    housing = fetch_california_housing()
    X = housing.data.astype(float)
    y = housing.target.astype(float)
    return X, y, {
        "feature_names": list(housing.feature_names),
        "n_features": X.shape[1],
        "description": "20640 samples, 8 features",
    }


def load_make_moons_dataset():
    X, y = make_moons(n_samples=300, noise=0.08, random_state=42)
    return X, y, {
        "n_features": X.shape[1],
        "n_classes": len(np.unique(y)),
        "description": "300 samples, 2 features (synthetic moons)",
    }


def load_mall_customers_dataset():
    path = _get_data_path("Mall_Customers.csv")
    df = pd.read_csv(path)
    X = df[["Annual Income (k$)", "Spending Score (1-100)"]].values.astype(float)
    return X, None, {
        "feature_names": ["Annual Income (k$)", "Spending Score (1-100)"],
        "n_features": X.shape[1],
        "description": "200 samples, 2 features (customer segmentation)",
    }


DATASETS = {
    "breast_cancer": {
        "name": "Breast Cancer Wisconsin",
        "type": "classification",
        "loader": load_breast_cancer_dataset,
        "description": "569 samples, 30 features — 恶性/良性肿瘤分类",
    },
    "iris": {
        "name": "Iris",
        "type": "classification",
        "loader": load_iris_dataset,
        "description": "150 samples, 4 features — 3 种鸢尾花分类",
    },
    "digits": {
        "name": "Digits",
        "type": "classification",
        "loader": load_digits_dataset,
        "description": "1797 samples, 64 features — 手写数字 0-9 分类",
    },
    "california_housing": {
        "name": "California Housing",
        "type": "regression",
        "loader": load_california_housing_dataset,
        "description": "20640 samples, 8 features — 加州房价回归",
    },
    "make_moons": {
        "name": "Make Moons (Synthetic)",
        "type": "clustering",
        "loader": load_make_moons_dataset,
        "description": "300 samples, 2 features — 月牙形合成数据",
    },
    "mall_customers": {
        "name": "Mall Customers",
        "type": "clustering",
        "loader": load_mall_customers_dataset,
        "description": "200 samples, 2 features — 商场客户分群",
    },
}


def load_dataset(name):
    """Load a built-in dataset by name."""
    if name not in DATASETS:
        raise ValueError(f"Unknown dataset: {name}. Available: {list(DATASETS.keys())}")
    ds = DATASETS[name]
    X, y, meta = ds["loader"]()
    meta["dataset_name"] = name
    meta["dataset_type"] = ds["type"]
    meta["dataset_description"] = ds["description"]
    return X, y, meta


def datasets_by_type(alg_type):
    """Return dataset names compatible with an algorithm type."""
    type_map = {
        "classification": "classification",
        "regression": "regression",
        "clustering": "clustering",
        "dimensionality_reduction": "classification",
    }
    target = type_map.get(alg_type, "classification")
    return [name for name, ds in DATASETS.items() if ds["type"] == target]
