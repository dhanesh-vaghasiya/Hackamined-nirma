from layer1.risk_model import predict_risk
from question_router import detect_question_type
from prompts.prompt_builder import build_prompt
from utils.language import is_hindi
from groq_api import ask_llm


def generate_response(question):

    layer1 = predict_risk()

    qtype = detect_question_type(question)

    hindi = is_hindi(question)

    prompt = build_prompt(layer1, question, qtype, hindi)

    answer = ask_llm(prompt)

    return answer