from flask import Flask, request, jsonify
import requests
import os
import json
import re

app = Flask(__name__)

# Load Gemini API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found. Please set it in your environment.")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def build_prompt(mode, grade, difficulty):
    templates = {
        "alphabet": f"Generate a simple alphabet learning question not exceeding 5 words for Grade {grade} children, difficulty: {difficulty}. "
                    "Each question must include 'question', 'options' (4 choices), and 'correct' (index). Focus on letter identification. Return only JSON.",
        "numbers": f"Generate a number learning question not exceeding 5 words for Grade {grade} children, difficulty: {difficulty}. "
                   "Each question must have 'question', 'options' (4 numbers), and 'correct'. Return JSON.",
        "math": f"Generate an arithmetic question not exceeding 5 words for Grade {grade} children, difficulty: {difficulty}. "
                "Include 'question', 'options' (4), and 'correct'. Output JSON.",
        "tables": f"Generate a multiplication table question for Grade {grade} students, difficulty: {difficulty}. "
                  "Include 'question', 'options' (4), and 'correct'. Output JSON.",
        "quiz": f"Generate a mixed quiz question for Grade {grade}, difficulty: {difficulty}, across alphabets, numbers, and math. "
                "Include 'question', 'options', and 'correct'. Output JSON."
    }
    return templates.get(mode.lower(), templates["quiz"])

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Edu-Kit Gemini API running!"})

@app.route("/generate", methods=["POST"])
def generate_questions():
    try:
        data = request.json
        mode = data.get("mode", "math")
        grade = data.get("grade", "1")
        difficulty = data.get("difficulty", "easy")

        prompt = build_prompt(mode, grade, difficulty)
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

        response = requests.post(GEMINI_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({"error": "Gemini API error", "details": response.text}), 500

        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

        try:
            questions = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))
            else:
                return jsonify({"error": "Invalid JSON from Gemini", "raw": text}), 500

        return jsonify({"mode": mode, "grade": grade, "difficulty": difficulty, "questions": questions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
