"""
ML Playground — FastAPI backend.
Run: uvicorn projects.ml_playground.app:app
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from .core import ALGORITHMS, train, predict, model_store
from .datasets import DATASETS, load_dataset, datasets_by_type

app = FastAPI(
    title="ML Playground API",
    description="统一的机器学习算法 API — 覆盖回归、分类、聚类、降维",
    version="1.0.0",
    docs_url="/docs",
)


# ── Schemas ──────────────────────────────────────────────

class TrainRequest(BaseModel):
    algorithm: str
    dataset: str
    params: Optional[dict] = None


class PredictRequest(BaseModel):
    model_id: str
    features: list


# ── Routes ───────────────────────────────────────────────

@app.get("/api/algorithms")
def list_algorithms():
    """List all available algorithms with metadata."""
    return {
        alg_id: {
            "name": info["name"],
            "type": info["type"],
            "description": info["description"],
            "default_params": info["default_params"],
            "needs_scaling": info["needs_scaling"],
            "supports_proba": info["supports_proba"],
            "default_dataset": info["default_dataset"],
            "compatible_datasets": datasets_by_type(info["type"]),
        }
        for alg_id, info in ALGORITHMS.items()
    }


@app.get("/api/datasets")
def list_datasets():
    """List all built-in datasets."""
    return {
        ds_id: {
            "name": info["name"],
            "type": info["type"],
            "description": info["description"],
        }
        for ds_id, info in DATASETS.items()
    }


@app.post("/api/train")
def train_model(req: TrainRequest):
    """Train a model on a built-in dataset."""
    if req.algorithm not in ALGORITHMS:
        raise HTTPException(400, f"Unknown algorithm '{req.algorithm}'. See GET /api/algorithms.")

    if req.dataset not in DATASETS:
        raise HTTPException(400, f"Unknown dataset '{req.dataset}'. See GET /api/datasets.")

    try:
        result = train(req.algorithm, req.dataset, params=req.params)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "model_id": result["model_id"],
        "algorithm": result["algorithm"],
        "algorithm_name": result["algorithm_name"],
        "type": result["type"],
        "dataset": result["dataset"],
        "params": result["params"],
        "metrics": result["metrics"],
        "feature_names": result["feature_names"],
        "n_features": result["n_features"],
        "n_samples": result["n_samples"],
        "n_classes": result.get("n_classes"),
    }


@app.post("/api/predict")
def predict_model(req: PredictRequest):
    """Run inference with a trained model."""
    try:
        result = predict(req.model_id, req.features)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return result


@app.get("/api/models")
def list_models():
    """List all trained models."""
    return {"models": model_store.list()}


@app.delete("/api/models/{model_id}")
def delete_model(model_id: str):
    """Remove a trained model."""
    removed = model_store.remove(model_id)
    if removed is None:
        raise HTTPException(404, f"Model '{model_id}' not found.")
    return {"status": "deleted", "model_id": model_id}


# ── Gradio Mount ─────────────────────────────────────────

def create_gradio_app():
    from .ui import create_ui
    return create_ui()


try:
    import gradio as gr
    demo = create_gradio_app()
    app = gr.mount_gradio_app(app, demo, path="/")
except ImportError:
    print("Gradio not installed. UI at / will not be available. Run: pip install gradio")
