import joblib
import numpy as np

# Load the trained model and encoders
model = joblib.load("cutoff_model.pkl")
encoders = joblib.load("cutoff_encoders.pkl")

# Define input data
input_data = {
    "Year": 2024,
    "Branch": "Computer Engineering",
    "Category": "Sc",
    "University Type": "Hu"
}

# Encode categorical features
for col in ["Branch", "Category", "University Type"]:
    if input_data[col] in encoders[col].classes_:
        input_data[col] = encoders[col].transform([input_data[col]])[0]
    else:
        raise ValueError(f"Value '{input_data[col]}' for column '{col}' not found in training data.")

# Convert to numpy array and reshape for prediction
X_input = np.array([[input_data["Year"], input_data["Branch"], input_data["Category"], input_data["University Type"]]])

# Predict percentile score
predicted_percentile = model.predict(X_input)[0]
print("Predicted Percentile Score:", predicted_percentile)
