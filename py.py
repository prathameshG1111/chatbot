import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Load the dataset
data = pd.read_csv("cutoff_dataset.csv")

# Encode categorical features
encoders = {}
categorical_cols = ["Branch", "Category", "University Type"]
for col in categorical_cols:
    encoders[col] = LabelEncoder()
    data[col] = encoders[col].fit_transform(data[col])

# Define independent (X) and dependent (y) variables
X = data[["Year", "Branch", "Category", "University Type"]]
y = data["Percentile Score"]

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define models and hyperparameter grid
models = {
    "RandomForest": RandomForestRegressor(),
    "GradientBoosting": GradientBoostingRegressor(),
    "XGBoost": XGBRegressor()
}

param_grid = {
    "RandomForest": {
        "n_estimators": [100, 200],
        "max_depth": [None, 10, 20],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2]
    },
    "GradientBoosting": {
        "n_estimators": [100, 200],
        "learning_rate": [0.05, 0.1],
        "max_depth": [3, 5],
    },
    "XGBoost": {
        "n_estimators": [100, 200],
        "learning_rate": [0.05, 0.1],
        "max_depth": [3, 5],
    }
}

# Train and evaluate models
best_model = None
best_score = -np.inf
best_params = None

for name, model in models.items():
    grid_search = GridSearchCV(model, param_grid[name], cv=5, scoring="r2", n_jobs=-1)
    grid_search.fit(X_train, y_train)

    # Predict and evaluate
    y_pred = grid_search.best_estimator_.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"Model: {name}, R²: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}, Best Params: {grid_search.best_params_}")

    if r2 > best_score:
        best_score = r2
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_

# Save the best model and encoders
joblib.dump(best_model, "cutoff_model.pkl")
joblib.dump(encoders, "cutoff_encoders.pkl")

print("Best model saved:", best_model)
print("Best parameters:", best_params)
