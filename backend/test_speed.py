"""Speed test: compare old multi-call vs new single-call approach."""
import time
import json
from app import create_app

app = create_app()

TESTS = [
    "What is the demand for Data Scientist?",
    "What skills are needed for Backend Developer?",
    "Hello, what can you do?",
]

with app.test_client() as c:
    for query in TESTS:
        print(f"QUERY: {query}")
        t0 = time.time()
        r = c.post("/api/chatbot/chat", json={"message": query, "history": []})
        elapsed = time.time() - t0
        d = r.get_json()
        print(f"  Status: {r.status_code} | Time: {elapsed:.1f}s | Tools: {d.get('tools_used', [])}")
        reply = d.get("reply", "")
        # Show first 400 chars
        print(f"  Reply: {reply[:400]}")
        print()
        # Small delay between requests
        time.sleep(2)
