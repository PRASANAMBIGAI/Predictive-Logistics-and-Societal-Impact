"""
Train an XGBoost model on synthetic logistics data.

Produces:
  - XGBClassifier   → predicts delay probability
  - XGBRegressor    → predicts delay duration (point estimate)
  - XGBRegressor x2 → quantile regressors for confidence interval (lower/upper)

All models + the encoder are saved as a dict in model.pkl.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data.csv")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")


def main():
    # ── Load data ──────────────────────────────────────────────
    df = pd.read_csv(DATA_PATH)
    print(f"[DATA] Loaded {len(df)} rows from {DATA_PATH}")

    # ── Encode categorical feature ─────────────────────────────
    le = LabelEncoder()
    df["weather_encoded"] = le.fit_transform(df["weather_condition"])

    feature_cols = [
        "current_speed_kmh",
        "weather_encoded",
        "traffic_index",
        "warehouse_backlog_index",
        "distance_remaining",
    ]

    X = df[feature_cols].values
    y_class = df["is_delayed"].values
    y_reg = df["delay_minutes"].values

    # ── Train / test split ─────────────────────────────────────
    X_train, X_test, yc_train, yc_test, yr_train, yr_test = train_test_split(
        X, y_class, y_reg, test_size=0.2, random_state=42
    )

    # ── Classifier (delay probability) ─────────────────────────
    clf = XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
    )
    clf.fit(X_train, yc_train)
    yc_pred = clf.predict(X_test)
    acc = accuracy_score(yc_test, yc_pred)
    print(f"[TARGET] Classifier Accuracy: {acc:.2%}")

    # ── Regressor — point estimate (delay minutes) ─────────────
    reg = XGBRegressor(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )
    reg.fit(X_train, yr_train)
    yr_pred = reg.predict(X_test)
    mae = mean_absolute_error(yr_test, yr_pred)
    print(f"[METRIC] Regressor MAE: {mae:.1f} minutes")

    # ── Quantile Regressors — confidence interval ──────────────
    print("\n[TRAINING] Quantile regressors for confidence intervals...")

    reg_lower = XGBRegressor(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        objective="reg:quantileerror",
        quantile_alpha=0.25,
    )
    reg_lower.fit(X_train, yr_train)

    reg_upper = XGBRegressor(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        objective="reg:quantileerror",
        quantile_alpha=0.75,
    )
    reg_upper.fit(X_train, yr_train)

    # Evaluate interval coverage
    yr_low = reg_lower.predict(X_test)
    yr_high = reg_upper.predict(X_test)
    coverage = np.mean((yr_test >= yr_low) & (yr_test <= yr_high))
    avg_width = np.mean(yr_high - yr_low)
    print(f"[METRIC] Confidence Interval Coverage: {coverage:.1%}")
    print(f"[METRIC] Average Interval Width: {avg_width:.1f} minutes")

    # ── Feature importances ────────────────────────────────────
    print("\n[CHART] Classifier Feature Importances:")
    for name, imp in zip(feature_cols, clf.feature_importances_):
        print(f"   {name:30s} {imp:.4f}")

    # ── Save model bundle ──────────────────────────────────────
    bundle = {
        "classifier": clf,
        "regressor": reg,
        "regressor_lower": reg_lower,
        "regressor_upper": reg_upper,
        "label_encoder": le,
        "feature_cols": feature_cols,
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\n[OK] Model bundle saved -> {MODEL_PATH}")
    print(f"     Contains: classifier, regressor, regressor_lower, regressor_upper, label_encoder")


if __name__ == "__main__":
    main()
