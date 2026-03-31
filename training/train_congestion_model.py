from pathlib import Path
import argparse
import json

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV  = ROOT / "training" / "out" / "congestion_dataset.csv"
DEFAULT_META = ROOT / "training" / "out" / "congestion_dataset_meta.json"
OUT_DIR      = ROOT / "training" / "out"


def save_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv",     default=str(DEFAULT_CSV),  help="Path to congestion_dataset.csv")
    parser.add_argument("--meta",    default=str(DEFAULT_META), help="Path to congestion_dataset_meta.json")
    parser.add_argument("--out-dir", default=str(OUT_DIR),      help="Output folder")
    args = parser.parse_args()

    csv_path  = Path(args.csv)
    meta_path = Path(args.meta)
    out_dir   = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise SystemExit(f"Dataset not found: {csv_path}")
    if not meta_path.exists():
        raise SystemExit(f"Meta file not found: {meta_path}")

    meta           = json.loads(meta_path.read_text(encoding="utf-8"))
    feature_columns = meta["feature_columns"]
    target_column  = meta["target_column"]

    df = pd.read_csv(csv_path)

    if len(df) < 300:
        raise SystemExit("Too few rows. Collect more data before training.")

    X = df[feature_columns]
    y = df[target_column]

    n         = len(df)
    train_end = int(n * 0.70)
    val_end   = int(n * 0.85)

    X_train    = X.iloc[:train_end];   y_train    = y.iloc[:train_end]
    X_val      = X.iloc[train_end:val_end]; y_val  = y.iloc[train_end:val_end]
    X_trainval = X.iloc[:val_end];     y_trainval = y.iloc[:val_end]
    X_test     = X.iloc[val_end:];     y_test     = y.iloc[val_end:]

    model = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)

    val_pred   = model.predict(X_val)
    val_acc    = accuracy_score(y_val, val_pred)
    val_report = classification_report(y_val, val_pred, digits=4)
    val_cm     = confusion_matrix(y_val, val_pred, labels=["LOW", "MEDIUM", "HIGH"])

    final_model = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1,
    )
    final_model.fit(X_trainval, y_trainval)

    test_pred  = final_model.predict(X_test)
    test_proba = final_model.predict_proba(X_test)
    test_acc   = accuracy_score(y_test, test_pred)
    test_report = classification_report(y_test, test_pred, digits=4)
    test_cm    = confusion_matrix(y_test, test_pred, labels=["LOW", "MEDIUM", "HIGH"])

    importances = pd.DataFrame({
        "feature":    feature_columns,
        "importance": final_model.feature_importances_,
    }).sort_values("importance", ascending=False)

    feature_importance_path = out_dir / "feature_importance.csv"
    metrics_json_path       = out_dir / "metrics.json"
    report_txt_path         = out_dir / "classification_report.txt"
    model_path              = out_dir / "traffic_congestion_model.joblib"

    report_text = (
        "=== VALIDATION ===\n"
        f"accuracy: {val_acc:.4f}\n\n"
        f"{val_report}\n"
        f"confusion_matrix (LOW, MEDIUM, HIGH):\n{val_cm}\n\n"
        "=== TEST ===\n"
        f"accuracy: {test_acc:.4f}\n\n"
        f"{test_report}\n"
        f"confusion_matrix (LOW, MEDIUM, HIGH):\n{test_cm}\n\n"
        "=== FEATURE IMPORTANCE ===\n"
        f"{importances.to_string(index=False)}\n"
    )

    save_text(report_txt_path, report_text)
    importances.to_csv(feature_importance_path, index=False)

    metrics = {
        "train_rows":           int(len(X_train)),
        "val_rows":             int(len(X_val)),
        "test_rows":            int(len(X_test)),
        "validation_accuracy":  float(val_acc),
        "test_accuracy":        float(test_acc),
        "feature_columns":      feature_columns,
        "classes":              list(final_model.classes_),
    }
    metrics_json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    bundle = {
        "model":            final_model,
        "feature_columns":  feature_columns,
        "classes":          list(final_model.classes_),
        "meta":             meta,
    }
    joblib.dump(bundle, model_path)

    print(f"[OK] Model saved:              {model_path}")
    print(f"[OK] Metrics saved:            {metrics_json_path}")
    print(f"[OK] Report saved:             {report_txt_path}")
    print(f"[OK] Feature importance saved: {feature_importance_path}")
    print(f"[OK] Validation accuracy:      {val_acc:.4f}")
    print(f"[OK] Test accuracy:            {test_acc:.4f}")
    print("[OK] Top features:")
    print(importances.head(10).to_string(index=False))

    if len(X_test) > 0:
        preview = pd.DataFrame({
            "ts":         df["ts"].iloc[val_end:].reset_index(drop=True),
            "actual":     y_test.reset_index(drop=True),
            "predicted":  pd.Series(test_pred),
            "confidence": pd.Series(test_proba.max(axis=1)).round(4),
        })
        preview_path = out_dir / "test_predictions_preview.csv"
        preview.to_csv(preview_path, index=False)
        print(f"[OK] Preview saved:            {preview_path}")


if __name__ == "__main__":
    main()
