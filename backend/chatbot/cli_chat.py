from chatbot import generate_response

print("Skills Mirage Chatbot (CLI Mode)")
print("Type 'exit' to quit\n")

while True:

    question = input("You: ")

    if question.lower() == "exit":
        print("Goodbye!")
        break

    answer = generate_response(question)

    print("\nBot:", answer)
    print()