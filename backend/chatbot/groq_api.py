from groq import Groq
import os

client = Groq(
    api_key="GROQ_API_KEY"
)

def ask_llm(prompt):

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a workforce intelligence assistant. Use provided data only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )
    return completion.choices[0].message.content