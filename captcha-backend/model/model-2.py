import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os

# 1. Load dataset
print("\n🔹 Loading dataset...")
data = pd.read_csv("processed_user_behavior_final.csv")

# 2. Preprocess - Clip outliers BEFORE split to avoid leakage
print("🔹 Clipping outliers...")
for col in data.select_dtypes(include=["float", "int"]).columns:
    data[col] = data[col].clip(lower=data[col].quantile(0.01), upper=data[col].quantile(0.99))

# 3. Extract features and labels
X = data.drop(columns=["label", "usai_id", "classification", "timestamp"], errors="ignore")
y = data["label"]
print("🔹 Final features used for training:", list(X.columns))

# After extracting X and y
X = X.select_dtypes(include=["number", "bool"])
# 4. Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Define base learners from scratch (no memory of past)
print("🔹 Initializing fresh model instances...")
base_learners = [
    ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
    ('xgb', XGBClassifier(n_estimators=170, scale_pos_weight=1, eval_metric='mlogloss', random_state=42))
]

# 6. Build the stacking ensemble without imputer or logistic regression
stacked_model = StackingClassifier(
    estimators=base_learners,
    final_estimator=XGBClassifier(n_estimators=100, random_state=42),
    cv=5,
    passthrough=True
)
print(data.select_dtypes(include=["number", "bool"]).groupby('label').mean().T)

joblib.dump(list(X.columns), "model-2.joblib")

# 7. Train the model from scratch
print("🔹 Training model from scratch...")
stacked_model.fit(X_train, y_train)

# 8. Evaluate
y_pred = stacked_model.predict(X_test)
print("\n✅ Accuracy:", accuracy_score(y_test, y_pred))

# 9. Save the new model (overwrite old one)
joblib.dump(stacked_model, "model-2.pkl")
print("💾 Model saved as model.pkl")