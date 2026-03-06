from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

SKILLS = [
"python","java","php","sql","analytics","crm",
"customer support","django","spring","laravel",
"api","automation"
]

skill_embeddings = model.encode(SKILLS)

def extract_skills(text):

    text_emb = model.encode([text])[0]

    found = []

    for skill, emb in zip(SKILLS, skill_embeddings):

        similarity = np.dot(text_emb, emb) / (
            np.linalg.norm(text_emb) * np.linalg.norm(emb)
        )

        if similarity > 0.45:
            found.append(skill)

    return found