import os
import openai
import pandas as pd
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from difflib import get_close_matches
import re

# Load environment variables from .env file
load_dotenv()

# Load API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load your dataset
df = pd.read_csv('Dataset.csv')
questions_dict = dict(zip(df['Question'], df['Answer']))

app = Flask(__name__)

# Preprocessing function
def preprocess(text: str) -> str:
    text = str(text)
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

# Function to find closest question
def get_closest_question(user_question: str, questions_dict: dict) -> str:
    user_question = preprocess(user_question)
    questions = list(map(preprocess, questions_dict.keys()))
    
    closest_matches = get_close_matches(user_question, questions, n=1, cutoff=0.8)
    
    if closest_matches:
        for original_question in questions_dict.keys():
            if preprocess(original_question) == closest_matches[0]:
                return original_question
    return None

# Function to query OpenAI API
def query_openai(user_question: str) -> str:
    try:
        closest_question = get_closest_question(user_question, questions_dict)
        if closest_question:
            return questions_dict[closest_question]
        else:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_question}]
            )
            return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return "Sorry, I couldn't retrieve an answer at this moment."

# Frontend Route
@app.route('/')
def index():
    return render_template('index.html')

# API route for chatbot
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    user_message = data.get('message')
    response = query_openai(user_message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
