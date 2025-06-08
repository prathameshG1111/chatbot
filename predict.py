import joblib
import numpy as np

# Load the trained model and encoders
model = joblib.load("cutoff_model.pkl")
encoders = joblib.load("cutoff_encoders.pkl")

def safe_encode(encoder, value, feature_name):
    try:
        return encoder.transform([value])[0]
    except ValueError:
        print(f"Warning: Unseen category '{value}' for {feature_name}. Using default encoding.")
        return -1  # Assigning a default encoding for unseen values

def predict_cutoff(branch, category, university_type, year):
    """
    Predicts the Percentile Score based on given inputs.

    Parameters:
        branch (str): Branch name (e.g., "Computer Engineering")
        category (str): Category (e.g., "Open", "OBC")
        university_type (str): University Type (HU/OHU)
        year (int): Year of admission

    Returns:
        float: Predicted Percentile Score
    """
    try:
        # Normalize inputs to match dataset case format
        university_type = university_type.capitalize()  # Convert "HU" -> "Hu"
        category_type = category_type.capitalize()
        # Encode inputs safely
        branch_encoded = safe_encode(encoders["Branch"], branch, "Branch")
        category_encoded = safe_encode(encoders["Category"], category, "Category")
        university_type_encoded = safe_encode(encoders["University Type"], university_type, "University Type")
        # Prepare input for prediction
        input_data = np.array([[year, branch_encoded, category_encoded, university_type_encoded]])
        # Predict percentile score
        predicted_percentile = model.predict(input_data)[0]
        print("Raw Prediction Output:", predicted_percentile, type(predicted_percentile))  # Debugging line

    except ValueError as e:
        print("Prediction Error:", str(e))  # Debugging line
        return f"Error: {e}. Please enter valid inputs."

    # Prepare input for prediction
    input_data = np.array([[year, branch_encoded, category_encoded, university_type_encoded]])

    # Predict percentile score
    predicted_percentile = float(model.predict(input_data)[0])
    
    return predicted_percentile  # Return numeric value for integration