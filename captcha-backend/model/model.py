import json, joblib, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import VarianceThreshold
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt

# ────────────────────────── 1. Load and preprocess data ---------------------
df = pd.read_csv("processed_user_behavior_final.csv")
X = df.drop(columns=["label", "usai_id", "classification", "timestamp"], errors="ignore")
y = df["label"].astype(int)

print("\n--- Constant/All-NaN Feature Check ---")
for col in X.columns:
    unique_vals = X[col].nunique(dropna=True)
    nan_count = X[col].isna().sum()
    if unique_vals == 1:
        print(f"Feature '{col}' is constant (value: {X[col].dropna().unique()})")
    if nan_count == len(X):
        print(f"Feature '{col}' is all NaN!")

constant_cols = [col for col in X.columns if X[col].nunique(dropna=True) == 1]
print(f"Dropping constant features: {constant_cols}")
X = X.drop(columns=constant_cols)
print("Raw feature count:", X.shape[1])

# ────────────────────────── 2. Clip outliers -------------------------------
clip_bounds = {}
for c in X.select_dtypes(include=["number"]).columns:
    if X[c].dtype != "bool":
        q01, q99 = X[c].quantile([0.01, 0.99])
        clip_bounds[c] = (q01, q99)
        X[c] = X[c].clip(lower=q01, upper=q99)


# ────────────────────────── 3. Low-variance prune ---------------------------
vt = VarianceThreshold(threshold=0.0)
# Keep only numeric and boolean columns for ML
X = X.select_dtypes(include=["number", "bool"])
X = pd.DataFrame(vt.fit_transform(X), columns=X.columns[vt.get_support()])

# ────────────────────────── 4. Correlation prune ----------------------------
model = RandomForestClassifier(random_state=42)
model.fit(X, y)
importances = pd.Series(model.feature_importances_, index=X.columns)
corr = X.corr().abs()
upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

to_drop = []
for col in upper.columns:
    for row in upper.index:
        if upper.loc[row, col] > 0.95:
            if importances[row] < importances[col]:
                to_drop.append(row)
            else:
                to_drop.append(col)
X = X.drop(columns=list(set(to_drop)))
print("Final feature count:", X.shape[1])

# ────────────────────────── 5. Train-test split ----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# ────────────────────────── 6. Base learners --------------------------------
neg, pos = np.bincount(y)
scale_pos = neg / pos
print(f"Class counts: negative={neg}, positive={pos}, scale_pos_weight={scale_pos:.2f}")

base_learners = [
    ("rf", RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42)),
    ("xgb", XGBClassifier(
        n_estimators=170,
        missing=np.nan,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        eval_metric="logloss",
        random_state=42))
]

# ────────────────────────── 6A. Hyperparameter tuning ----------------------
from sklearn.model_selection import RandomizedSearchCV

# RandomForest tuning
rf_param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 5, 10, 20],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'class_weight': ['balanced']
}
rf_base = RandomForestClassifier(random_state=42)
rf_search = RandomizedSearchCV(rf_base, rf_param_grid, n_iter=10, cv=3, scoring='f1', n_jobs=-1, random_state=42)
rf_search.fit(X_train, y_train)
print('Best RF params:', rf_search.best_params_)
best_rf = rf_search.best_estimator_

# XGBoost tuning
xgb_param_grid = {
    'n_estimators': [100, 170, 250],
    'max_depth': [3, 6, 10],
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'subsample': [0.7, 0.9, 1.0],
    'colsample_bytree': [0.7, 0.8, 1.0],
    'scale_pos_weight': [scale_pos]
}
xgb_base = XGBClassifier(missing=np.nan, eval_metric='logloss', random_state=42)
xgb_search = RandomizedSearchCV(xgb_base, xgb_param_grid, n_iter=10, cv=3, scoring='f1', n_jobs=-1, random_state=42)
xgb_search.fit(X_train, y_train)
print('Best XGB params:', xgb_search.best_params_)
best_xgb = xgb_search.best_estimator_

# Use best_rf and best_xgb in base_learners
base_learners = [
    ("rf", best_rf),
    ("xgb", best_xgb)
]

# ────────────────────────── 7. Meta-learner pipeline (no scaling) -----------
meta_learner = Pipeline([
    ("imputer", SimpleImputer(strategy="mean", keep_empty_features=True)),
    ("lr", LogisticRegression(
        class_weight="balanced",
        penalty="l2",
        C=1.0,
        max_iter=1000,
        solver="lbfgs"))
])



# ────────────────────────── 8. Stacking classifier --------------------------
stack = StackingClassifier(
    estimators=base_learners,
    final_estimator=meta_learner,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    passthrough=True,
    n_jobs=-1
)

# ────────────────────────── 9. Calibrate probabilities ----------------------
calibrated = CalibratedClassifierCV(
    estimator=stack,
    method="sigmoid",
    cv=5
)

# ────────────────────────── 10. Train ----------------------------------------
calibrated.fit(X_train, y_train)
joblib.dump(list(X.columns), "model.joblib")

# ────────────────────────── 11. Evaluate ------------------------------------
proba_test = calibrated.predict_proba(X_test)[:, 1]
y_pred = (proba_test >= 0.5).astype(int)

print("Label distribution:", y.value_counts())
print(df.select_dtypes(include=["number", "bool"]).groupby('label').mean().T)
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))

print("\n───────── Validation metrics ─────────")
print("Accuracy :", accuracy_score(y_test, y_pred))
print("F1-score :", f1_score(y_test, y_pred))
print("ROC-AUC  :", roc_auc_score(y_test, proba_test))

print("Prediction confidence breakdown:")
for rng in [(0,0.6),(0.6,0.8),(0.8,1)]:
    pct = np.mean((proba_test>=rng[0]) & (proba_test<rng[1]))*100
    print(f"  {rng[0]:.1f}–{rng[1]:.1f}: {pct:5.1f}%")

# ────────────── Error analysis: print most misclassified samples ─────────────
print("\nTop 10 most confident misclassifications (False Positives):")
false_positives = (y_test == 0) & (y_pred == 1)
fp_conf = proba_test[false_positives]
if np.any(false_positives):
    top_fp_idx = np.argsort(-fp_conf)[:10]
    print(X_test[false_positives].iloc[top_fp_idx].assign(
        true_label=y_test[false_positives].iloc[top_fp_idx],
        pred_proba=fp_conf[top_fp_idx]
    ))
else:
    print("None.")

print("\nTop 10 most confident misclassifications (False Negatives):")
false_negatives = (y_test == 1) & (y_pred == 0)
fn_conf = 1 - proba_test[false_negatives]
if np.any(false_negatives):
    top_fn_idx = np.argsort(-fn_conf)[:10]
    print(X_test[false_negatives].iloc[top_fn_idx].assign(
        true_label=y_test[false_negatives].iloc[top_fn_idx],
        pred_proba=proba_test[false_negatives][top_fn_idx]
    ))
else:
    print("None.")

# ────────────────────────── 12. Persist artefacts ---------------------------
joblib.dump(calibrated, "model.pkl")
with open("model_features.json", "w") as f:
    json.dump(list(X.columns), f)
print("\nModel + feature list saved ✓")
