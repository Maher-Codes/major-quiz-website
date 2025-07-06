import os
from flask import Flask, render_template, request
import google.generativeai as genai
from dotenv import load_dotenv
import re

# Load environment variables from .env
load_dotenv()

# Flask app setup
app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

from flask import send_from_directory

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/quiz', methods=['POST'])
def quiz():
    selected_major = request.form['major']

    prompt = (
    f"Generate exactly 25 multiple choice questions for high school students about '{selected_major}'. "
    f"Each question should be numbered (1 to 25), with 4 options labeled A–D. After each question, provide the correct answer clearly like 'Answer: B'. "
    f"Follow this format exactly:\n"
    f"1. What is X?\nA. ...\nB. ...\nC. ...\nD. ...\nAnswer: B\n\n2. What is Y?..."
            )

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        print("=== GEMINI RAW RESPONSE ===")
        print(raw_text)

        # Match questions with regex
        question_blocks = re.findall(r"\d+\..+?(?:Answer:\s?[A-D])", raw_text, re.DOTALL)

        questions = []
        for i, block in enumerate(question_blocks):
            lines = block.strip().split('\n')
            question_line = lines[0].strip()
            options = lines[1:5]
            answer_line = [line for line in lines if line.strip().lower().startswith("answer:")]

            if len(options) == 4 and answer_line:
                correct_answer = answer_line[0].split(":")[-1].strip().upper()

                questions.append({
                    "id": i,
                    "question": question_line,
                    "options": options,
                    "correct": correct_answer
                })

        if not questions:
            return "<h2>No questions found. Please try again or change the major.</h2>"

        return render_template('quiz.html', major=selected_major, questions=questions)

    except Exception as e:
        return f"<p><strong>Error from Gemini API:</strong> {e}</p>"

@app.route('/result', methods=['POST'])
def result():
    total = 0
    correct = 0

    for key in request.form:
        if key.startswith("q"):
            user_ans = request.form[key]
            correct_ans = request.form.get("correct_" + key)
            total += 1
            if user_ans == correct_ans:
                correct += 1

    score = round((correct / total) * 100)

    if score >= 80:
        message = f"You scored {score}%. 🎉 Great job! This major really suits you!"
    elif score >= 50:
        message = f"You scored {score}%. You're on the right path! Keep learning and improving!"
    else:
        message = f"You scored {score}%. This major might not be the best fit, or you just need more preparation."

    return render_template("result.html", message=message)

if __name__ == '__main__':
    app.run(debug=True)
