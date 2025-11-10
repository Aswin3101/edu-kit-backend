from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Replace with your Gemini API key
GEMINI_API_KEY = os.getenv("AIzaSyCllKjYum5SL1ruCF7zD4vx9h9m8iUg_ds")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def build_prompt(mode, grade, difficulty):
    """
    Dynamically create a structured prompt for Gemini.
    """
    templates = {
        "alphabet": f"Generate a simple alphabet learning question not exceeding 5 words for Grade {grade} children, difficulty: {difficulty}. "
                    "Each question must include a 'question', 'options' (4 choices), and 'correct' (index of correct answer). "
                    "Focus on letter identification and phonics. Return only JSON.",
        "numbers": f"Generate a number learning question not exceeding 5 words for Grade {grade} children, difficulty: {difficulty}. "
                   "Each question must have a 'question', 'options' (4 numbers), and 'correct' (index). Return JSON.",
        "math": f"Generate a arithmetic question not exceeding 5 words (addition/subtraction/multiplication) for Grade {grade} children, difficulty: {difficulty}. "
                "Each item must include 'question', 'options' (4 choices), and 'correct'. Output JSON.",
        "tables": f"Generate a multiplication table question not exceeding 5 words for Grade {grade} students, difficulty: {difficulty}. "
                  "Each should include 'question', 'options' (4), and 'correct'. Output JSON.",
        "quiz": f"Generate a mixed quiz question not exceeding 5 words for Grade {grade}, difficulty: {difficulty}, across alphabets, numbers, and math. "
                "Each question must include 'question', 'options', and 'correct'. Output only JSON."
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

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }

        response = requests.post(GEMINI_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({"error": "Gemini API error", "details": response.text}), 500

        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]

        # Try to clean and parse the Gemini output safely
        import json
        try:
            questions = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON manually if Gemini adds text
            import re
            json_str = re.search(r"\[.*\]", text, re.DOTALL)
            if json_str:
                questions = json.loads(json_str.group(0))
            else:
                return jsonify({"error": "Invalid JSON from Gemini"}), 500

        return jsonify({"mode": mode, "grade": grade, "difficulty": difficulty, "questions": questions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# For local testing
if __name__ == "__main__":
    app.run(debug=True)
