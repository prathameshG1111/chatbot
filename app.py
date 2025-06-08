import os
import openai
import pandas as pd
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
import re
from symspellpy.symspellpy import SymSpell
import requests
import uuid
import secrets
import spacy
from predict import predict_cutoff

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load dataset
df = pd.read_csv('Dataset.csv')
questions_dict = dict(zip(df['Question'], df['Answer']))

# Initialize Flask App
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Load Sentence Transformer Model
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Initialize SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = os.path.join('frequency_dictionary_en_82_765.txt')
bigram_path = os.path.join('frequency_bigramdictionary_en_243_342.txt')
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
sym_spell.load_bigram_dictionary(bigram_path, term_index=0, count_index=1)

# Load spaCy Model
nlp = spacy.load("en_core_web_sm")

# Load previous cutoffs dataset
cutoff_df = pd.read_excel("cutoff_dataset.xlsx", engine="openpyxl")
cutoff_df.columns = cutoff_df.columns.str.strip()
cutoff_df["Year"] = cutoff_df["Year"].astype(str).str[:4].astype(int)
latest_year = cutoff_df["Year"].max()
df_previous = cutoff_df[cutoff_df["Year"] == latest_year - 1]

# Spell correction function
def correct_spelling(text: str) -> str:
    suggestions = sym_spell.lookup_compound(text, max_edit_distance=2)
    return suggestions[0].term if suggestions else text

# Preprocessing function
def preprocess(text: str) -> str:
    return correct_spelling(str(text).lower().strip())

# Get closest question using embeddings
def get_closest_question_embedding(user_question: str, questions_dict: dict) -> str:
    user_question = preprocess(user_question)
    questions = list(map(preprocess, questions_dict.keys()))
    
    user_embedding = embedding_model.encode(user_question, convert_to_tensor=True)
    question_embeddings = embedding_model.encode(questions, convert_to_tensor=True)
    
    similarities = util.pytorch_cos_sim(user_embedding, question_embeddings)[0]
    highest_similarity, best_match_idx = similarities.max(), similarities.argmax().item()

    if highest_similarity >= 0.7:
        return list(questions_dict.keys())[best_match_idx]
    return None

# Get dataset response
def get_dataset_response(user_question: str) -> str:
    closest_question = get_closest_question_embedding(user_question, questions_dict)
    return questions_dict.get(closest_question, None)

# OpenAI Fallback
openai_cache = {}

def query_openai(user_question: str) -> str:
    try:
        if user_question in openai_cache:
            return openai_cache[user_question]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_question}]
        )
        openai_answer = response.choices[0].message['content'].strip()
        openai_cache[user_question] = openai_answer
        return openai_answer
    except Exception as e:
        return "Sorry, I couldn't retrieve an answer at this moment."

# Intent detection
cutoff_keywords = ["cutoff", "previous year cutoff", "last year cutoff", "merit list"]
admission_keywords = ["admission", "apply", "enrollment", "intake", "fees", "deadline", "ug", "pg", "diploma", "undergraduate", "postgraduate", "computer engineering", "ai & ml", "artificial intelligence", "civil engineering",
    "mechanical engineering", "electrical engineering", "electronics and telecommunications",
    "ai & ds", "data science", "telecom", "comp engg", "ce", "cs", "e&tc"]

def detect_intent(user_query):
    query = user_query.lower()
    if any(keyword in query for keyword in cutoff_keywords):
        return "cutoff_query"
    if any(keyword in query for keyword in admission_keywords):
        return "admission_query"
    return "general_query"

# Extract cutoff details
def extract_cutoff_details(user_query):
    doc = nlp(user_query)
    branch, category, university_type = None, None, None
    is_previous, is_expected = False, False

    category_keywords = ["open", "obc", "sc", "st"]
    university_keywords = ["hu", "osu"]
    
    past_keywords = ["last year", "previous year", "2023"]
    future_keywords = ["expected", "predict", "this year"]

    for token in doc:
        word = token.text.lower()
        if word in category_keywords:
            category = word
        elif word in university_keywords:
            university_type = word
        elif word in past_keywords:
            is_previous = True
        elif word in future_keywords:
            is_expected = True

    # Assume prediction if neither past nor expected is specified
    if not is_previous and not is_expected:
        is_expected = True

    return branch, category, university_type, is_previous, is_expected

@app.route("/")
def index():
    return render_template('index.html')

user_sessions = {}

@app.route("/chatbot", methods=["POST"])
def chatbot_response():
    user_query = request.json.get("message", "").strip()
    user_id = request.json.get("user_id", "default")
    intent = detect_intent(user_query)

    # Ensure session exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {}

    # Handle Cutoff Prediction Flow
    if intent == "cutoff_query":
        session_data = user_sessions[user_id]

        if "branch" not in session_data:
            return jsonify({"response": "Which branch are you interested in? (Computer Engineering, Artificial Intelligence and Data Science, Electonics and Telecommunication, Mechanical Engineering, Civil Engineering"})
        
        if "university_type" not in session_data:
            return jsonify({"response": "Is it for Home University (HU) or Other than Home University (OHU)?"})
        
        if "category" not in session_data:
            return jsonify({"response": "Which category are you applying under? (Open, OBC, SC, ST)"})

        # Predict once all inputs are collected
        branch = session_data["branch"]
        university_type = session_data["university_type"]
        category = session_data.get("category", "Open")  # Default category = Open
        year = 2024  # Predict for the latest year

        predicted_cutoff = predict_cutoff(branch, category, university_type, year)
        print("Predicted cutoff:", predicted_cutoff, type(predicted_cutoff))
        if isinstance(predicted_cutoff, str):  # Check if an error message was returned
            return jsonify({"response": predicted_cutoff})
        return jsonify({"response": f"The expected cutoff for {branch} ({category}, {university_type}) is {predicted_cutoff:.2f} percentile."})


    # Handle user responses for missing details
    if user_query in ["Computer Engineering", "IT", "AI&DS"]:
        user_sessions[user_id]["branch"] = user_query
        return jsonify({"response": "Is it for Home University (HU) or Other than Home University (OHU)?"})

    if user_query in ["HU", "OHU"]:
        user_sessions[user_id]["university_type"] = user_query
        return jsonify({"response": "Which category are you applying under? (Open, OBC, SC, ST)"})

    if user_query in ["Open", "OBC", "SC", "ST"]:
        user_sessions[user_id]["category"] = user_query

        branch = user_sessions[user_id]["branch"]
        university_type = user_sessions[user_id]["university_type"]
        category = user_sessions[user_id]["category"]
        year = 2024

        predicted_cutoff = predict_cutoff(branch, category, university_type, year)
        return jsonify({"response": f"The expected cutoff for {branch} ({category}, {university_type}) is {predicted_cutoff:.2f} percentile."})

    # Handle Admission Queries (via Rasa)
    elif intent == "admission_query":
        return get_rasa_response(user_query)

    # Handle Dataset/OpenAI Queries
    response = get_dataset_response(user_query) or query_openai(user_query)
    return jsonify({"response": response})

@app.route("/predict_cutoff", methods=["POST"])
def get_cutoff():
    data = request.json
    branch = data.get("branch")
    university_type = data.get("university_type")
    category = data.get("category", "Open")  # Default category = Open
    year = data.get("year", 2024)  # Default year = 2024

    if not branch or not university_type:
        return jsonify({"error": "Branch and University Type are required!"}), 400

    predicted_cutoff = predict_cutoff(branch, category, university_type, year)

    return jsonify({
        "branch": branch,
        "university_type": university_type,
        "category": category,
        "year": year,
        "predicted_cutoff": predicted_cutoff
    })

def get_rasa_response(user_input):
    try:
        response = requests.post(
            "http://localhost:5005/webhooks/rest/webhook",
            json={"message": user_input},
            timeout=5
        )
        if response.status_code == 200 and response.json():
            return jsonify({"response": response.json()[0].get('text', "I'm sorry, I couldn't understand that.")})
        return jsonify({"response": "Sorry, there was an issue with the Rasa server."})
    except requests.exceptions.RequestException:
        return jsonify({"response": "Connection to Rasa failed."})

if __name__ == "__main__":
    app.run(debug=True)
