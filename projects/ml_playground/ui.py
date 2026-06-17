"""
Gradio UI for ML Playground.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import gradio as gr

from .core import ALGORITHMS, train, predict, model_store
from .datasets import DATASETS, load_dataset, datasets_by_type

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 100


def _available_algorithms():
    """Return list of algorithm IDs for dropdown."""
    return list(ALGORITHMS.keys())


def _update_datasets(alg_id):
    """Update dataset dropdown based on selected algorithm."""
    if alg_id not in ALGORITHMS:
        return gr.update(choices=[], value=None)
    algo = ALGORITHMS[alg_id]
    compat = datasets_by_type(algo["type"])
    choices = [(DATASETS[name]["name"], name) for name in compat]
    default = algo["default_dataset"]
    return gr.update(choices=choices, value=default)


def _update_params(alg_id):
    """Update params textbox with default parameters."""
    if alg_id not in ALGORITHMS:
        return gr.update(value="{}")
    return gr.update(value=json.dumps(ALGORITHMS[alg_id]["default_params"], indent=2, ensure_ascii=False))


def _generate_plot(result):
    """Generate a matplotlib figure from training results."""
    alg_type = result["type"]
    algo_name = result["algorithm_name"]
    ds_name = result["dataset"]
    plot_data = result.get("_plot_data", {})
    model = result.get("_model")
    X_train = result.get("_X_train")
    y_train = result.get("_y_train")

    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("#f8f9fa")

    if alg_type == "classification":
        y_test = np.array(plot_data.get("_y_test", []))
        y_pred = np.array(plot_data.get("_y_pred", []))
        if len(y_test) > 0 and len(np.unique(y_test)) <= 5:
            cm = confusion_matrix(y_test, y_pred)
            ConfusionMatrixDisplay(cm).plot(ax=ax, cmap="Blues", colorbar=False)
            ax.set_title(f"{algo_name} — Confusion Matrix\nDataset: {ds_name}", fontsize=10)
        else:
            acc = result.get("metrics", {}).get("accuracy", 0)
            ax.bar(["Accuracy"], [acc], color="#3498db", width=0.4)
            ax.set_ylim(0, 1)
            ax.set_ylabel("Score")
            ax.set_title(f"{algo_name} — Accuracy: {acc:.2%}\nDataset: {ds_name}", fontsize=10)

    elif alg_type == "regression":
        y_test = np.array(plot_data.get("_y_test", []))
        y_pred = np.array(plot_data.get("_y_pred", []))
        if len(y_test) > 0:
            ax.scatter(y_test, y_pred, alpha=0.5, s=10, color="#e74c3c")
            min_val = min(y_test.min(), y_pred.min())
            max_val = max(y_test.max(), y_pred.max())
            ax.plot([min_val, max_val], [min_val, max_val], "k--", alpha=0.3)
            ax.set_xlabel("Actual")
            ax.set_ylabel("Predicted")
            r2 = result.get("metrics", {}).get("r2", 0)
            ax.set_title(f"{algo_name} — R²: {r2:.4f}\nDataset: {ds_name}", fontsize=10)

    elif alg_type == "clustering":
        X = X_train
        labels = np.array(plot_data.get("_labels", [])) if plot_data.get("_labels") else None
        if X is not None and labels is not None and X.shape[1] >= 2:
            scatter = ax.scatter(X[:, 0], X[:, 1], c=labels, cmap="tab10", s=15, alpha=0.7,
                                edgecolors="white", linewidth=0.2)
            ax.set_xlabel("Feature 1")
            ax.set_ylabel("Feature 2")
            n_clusters = result.get("metrics", {}).get("n_clusters", "?")
            ax.set_title(f"{algo_name} — Clusters: {n_clusters}\nDataset: {ds_name}", fontsize=10)
            legend = ax.legend(*scatter.legend_elements(), title="Cluster", fontsize=6)
        elif X is not None and X.shape[1] == 1:
            ax.scatter(X[:, 0], np.zeros_like(X[:, 0]), c=labels, cmap="tab10", s=15, alpha=0.7)
            ax.set_title(f"{algo_name} — Dataset: {ds_name}", fontsize=10)
        else:
            ax.text(0.5, 0.5, "Requires 2D data for visualization", ha="center", va="center", transform=ax.transAxes)

    elif alg_type == "dimensionality_reduction":
        X = X_train
        if X is not None and hasattr(model, "transform"):
            X_pca = model.transform(X)
            if X_pca.shape[1] >= 2:
                colors = y_train if y_train is not None else None
                scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=colors, cmap="tab10",
                                    s=12, alpha=0.6, edgecolors="white", linewidth=0.15)
                ax.set_xlabel("PC1")
                ax.set_ylabel("PC2")
                ev_ratio = result.get("metrics", {}).get("explained_variance_ratio", [])
                ratio_str = f"PC1={ev_ratio[0]*100:.1f}%, PC2={ev_ratio[1]*100:.1f}%" if len(ev_ratio) >= 2 else ""
                ax.set_title(f"{algo_name}\n{ratio_str}", fontsize=10)
                if colors is not None:
                    legend = ax.legend(*scatter.legend_elements(), title="Class", fontsize=6)
            else:
                ax.text(0.5, 0.5, f"1D projection (n_components={X_pca.shape[1]})", ha="center", va="center")

    plt.tight_layout()
    return fig


def _train_click(alg_id, ds_name, params_json):
    """Handle train button click."""
    try:
        params = json.loads(params_json) if params_json.strip() else {}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}, None

    try:
        result = train(alg_id, ds_name, params=params)
    except ValueError as e:
        return {"error": str(e)}, None

    metrics = result.get("metrics", {})
    info = {
        "Model ID": result["model_id"],
        "Algorithm": result["algorithm_name"],
        "Type": result["type"],
        "Dataset": result["dataset"],
        "Samples": result["n_samples"],
        "Features": result["n_features"],
    }
    info.update(metrics)
    info_str = json.dumps(info, indent=2, ensure_ascii=False)

    plot = _generate_plot(result)

    return info_str, plot


def _update_models():
    """Refresh the model list for dropdown."""
    models = model_store.list()
    if not models:
        return gr.update(choices=[], value=None, interactive=False)
    choices = [f"{m['model_id']} ({m['algorithm_name']} — {m['dataset']})" for m in models]
    return gr.update(choices=choices, value=choices[0], interactive=True)


def _get_n_features(model_id_str):
    """Get number of features for a model."""
    if not model_id_str:
        return "No model selected.", None
    mid = model_id_str.split(" ")[0]
    data = model_store.get(mid)
    if data is None:
        return "Model not found.", None
    nf = data.get("n_features", 0)
    feature_names = data.get("feature_names", [f"Feature {i+1}" for i in range(nf)])
    return f"Model: {mid} | Features: {nf}", feature_names


def _predict_click(model_id_str, features_text):
    """Handle predict button click."""
    if not model_id_str:
        return "No model selected."
    mid = model_id_str.split(" ")[0]

    try:
        rows = [list(map(float, line.strip().split(","))) for line in features_text.strip().split("\n") if line.strip()]
    except ValueError as e:
        return f"Invalid feature input: {e}"

    if not rows:
        return "No features provided."

    try:
        result = predict(mid, rows)
    except ValueError as e:
        return str(e)

    return json.dumps(result, indent=2, ensure_ascii=False)


def create_ui():
    """Build the Gradio Blocks interface."""
    with gr.Blocks(title="ML Playground", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # ML Playground
            从线性回归到 PCA — 11 个算法的统一实验平台
            """
        )

        with gr.Tab("训练"):
            with gr.Row():
                with gr.Column(scale=1):
                    alg_dropdown = gr.Dropdown(
                        choices=_available_algorithms(),
                        value="random_forest",
                        label="算法",
                        info="选择要训练的算法",
                    )
                    ds_dropdown = gr.Dropdown(
                        choices=[(DATASETS[n]["name"], n) for n in datasets_by_type("classification")],
                        value="breast_cancer",
                        label="数据集",
                        info="选择内置数据集",
                    )
                    params_input = gr.Textbox(
                        value=json.dumps(ALGORITHMS["random_forest"]["default_params"], indent=2, ensure_ascii=False),
                        label="超参数 (JSON)",
                        lines=6,
                    )
                    train_btn = gr.Button("训练", variant="primary")

                with gr.Column(scale=1):
                    metrics_output = gr.Textbox(label="训练结果", lines=10)
                    plot_output = gr.Plot(label="可视化")

            alg_dropdown.change(
                fn=_update_datasets,
                inputs=alg_dropdown,
                outputs=ds_dropdown,
            )
            alg_dropdown.change(
                fn=_update_params,
                inputs=alg_dropdown,
                outputs=params_input,
            )
            train_btn.click(
                fn=_train_click,
                inputs=[alg_dropdown, ds_dropdown, params_input],
                outputs=[metrics_output, plot_output],
            )

        with gr.Tab("预测"):
            with gr.Row():
                with gr.Column(scale=1):
                    refresh_btn = gr.Button("刷新模型列表", variant="secondary")
                    model_selector = gr.Dropdown(
                        choices=[], value=None, label="已训练模型",
                        info="选择要用于预测的模型", interactive=False,
                    )
                    feature_names_display = gr.Textbox(label="模型信息", value="请先训练模型", lines=2, interactive=False)
                    features_input = gr.Textbox(
                        label="输入特征 (每行一个样本，逗号分隔)",
                        lines=6,
                        placeholder="例如:\n5.1,3.5,1.4,0.2\n4.9,3.0,1.4,0.2",
                    )
                    predict_btn = gr.Button("预测", variant="primary")

                with gr.Column(scale=1):
                    predict_output = gr.Textbox(label="预测结果", lines=10)

            refresh_btn.click(fn=_update_models, outputs=model_selector)
            model_selector.change(fn=_get_n_features, inputs=model_selector, outputs=[feature_names_display])
            predict_btn.click(fn=_predict_click, inputs=[model_selector, features_input], outputs=predict_output)

        with gr.Tab("关于"):
            gr.Markdown(
                """
                ## ML Playground API

                本平台将本系列已实现的 11 个算法统一为可调用的 API + 交互界面。

                ### 已实现算法

                - **回归**: 线性回归, Ridge, Lasso, GBDT Regressor
                - **分类**: 逻辑回归, 决策树, 随机森林, GBDT Classifier, SVM
                - **聚类**: K-Means, DBSCAN
                - **降维**: PCA

                ### API 文档

                FastAPI Swagger 文档在 [](/docs) 路径。

                ### 代码

                所有算法使用 NumPy 从零实现。
                项目地址: `projects/ml_playground/`

                ### 使用流程

                1. **训练**: 选择算法 → 选择数据集 → 调整参数 → 训练
                2. **预测**: 刷新模型列表 → 选择模型 → 输入特征 → 预测
                """
            )

    return demo
