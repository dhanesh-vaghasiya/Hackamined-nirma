from flask import Flask, request, jsonify, render_template
from chatbot import generate_response
import os

app = Flask(__name__, template_folder='templates')

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question required"}), 400

    answer = generate_response(question)

    return jsonify({
        "question": question,
        "answer": answer
    })


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)