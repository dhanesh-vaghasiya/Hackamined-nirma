from groq import Groq

client = Groq(api_key="Groq_API_Key")

chat = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": "Say hello"}
    ]
)

print(chat.choices[0].message.content)