from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clean" / "practice_dataset.csv"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
target = "disease_next_3d"

feature_sets = {
    "M0_baseline": [
        "age_days", "weight_kg", "ambient_temp_c", "humidity_pct", "pen_id"
    ],
    "M1_current_vitality": [
        "age_days", "weight_kg", "ambient_temp_c", "humidity_pct", "pen_id",
        "activity_minutes", "distance_m", "lying_ratio", "feeding_visits",
        "feeding_minutes", "drinking_visits", "social_contacts",
        "posture_changes", "cough_events", "vitality_score",
        "camera_coverage_pct",
    ],
    "M2_change": [
        "age_days", "weight_kg", "ambient_temp_c", "humidity_pct", "pen_id",
        "activity_minutes", "distance_m", "lying_ratio", "feeding_visits",
        "feeding_minutes", "drinking_visits", "social_contacts",
        "posture_changes", "cough_events", "vitality_score",
        "camera_coverage_pct", "vitality_delta_3d", "activity_delta_pct_3d",
        "cough_events_prior_3d",
    ],
}


def build_model(features):
    categorical = [c for c in features if c in {"pen_id", "sex", "breed"}]
    numeric = [c for c in features if c not in categorical]
    prep = ColumnTransformer(
        [
            ("num", Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    return Pipeline([
        ("prep", prep),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
    ])


def choose_threshold(y_true, probabilities, min_sensitivity=0.80):
    candidates = np.unique(probabilities)
    best = None
    for threshold in candidates:
        pred = probabilities >= threshold
        tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
        sensitivity = tp / (tp + fn) if tp + fn else 0
        precision = tp / (tp + fp) if tp + fp else 0
        if sensitivity >= min_sensitivity:
            item = (precision, -threshold, threshold)
            if best is None or item > best:
                best = item
    return float(best[2] if best else 0.5)


def metrics(y_true, probabilities, threshold):
    pred = probabilities >= threshold
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "n": int(len(y_true)),
        "positives": int(np.sum(y_true)),
        "auprc": float(average_precision_score(y_true, probabilities)),
        "auroc": float(roc_auc_score(y_true, probabilities)),
        "threshold": float(threshold),
        "sensitivity": float(tp / (tp + fn) if tp + fn else 0),
        "specificity": float(tn / (tn + fp) if tn + fp else 0),
        "ppv": float(tp / (tp + fp) if tp + fp else 0),
        "alerts_per_100_pig_days": float(100 * (tp + fp) / len(y_true)),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
    }


train = df.loc[df["split"].eq("train")]
validation = df.loc[df["split"].eq("validation")]
test = df.loc[df["split"].eq("test")]
all_results = {}
prediction_frame = test[["observation_date", "pig_id", "pen_id", target]].copy()

for name, features in feature_sets.items():
    model = build_model(features)
    model.fit(train[features], train[target])
    val_prob = model.predict_proba(validation[features])[:, 1]
    threshold = choose_threshold(validation[target].to_numpy(), val_prob)
    test_prob = model.predict_proba(test[features])[:, 1]
    all_results[name] = metrics(test[target].to_numpy(), test_prob, threshold)
    prediction_frame[f"prob_{name}"] = test_prob

(RESULTS / "metrics.json").write_text(
    json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
)
prediction_frame.to_csv(RESULTS / "test_predictions.csv", index=False)

metric_table = pd.DataFrame(all_results).T.reset_index(names="model")
metric_table.to_csv(RESULTS / "model_comparison.csv", index=False)

best_prob = prediction_frame["prob_M2_change"]
precision, recall, _ = precision_recall_curve(test[target], best_prob)
fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
axes[0].plot(recall, precision, color="#00A99D", linewidth=2)
axes[0].axhline(test[target].mean(), color="0.5", linestyle="--", label="prevalence")
axes[0].set(xlabel="Recall", ylabel="Precision", title="Test precision-recall curve")
axes[0].legend()
sns.boxplot(data=prediction_frame, x=target, y="prob_M2_change", ax=axes[1], color="#DCEFEB")
sns.stripplot(data=prediction_frame, x=target, y="prob_M2_change", ax=axes[1], color="0.2", alpha=0.25)
axes[1].set(xlabel="Disease within next 3 days", ylabel="Predicted probability", title="Risk distribution")
fig.savefig(RESULTS / "model_evaluation.png", dpi=180)

print(metric_table[["model", "auprc", "auroc", "sensitivity", "ppv", "alerts_per_100_pig_days"]].round(3))
print(f"Saved results to {RESULTS}")

