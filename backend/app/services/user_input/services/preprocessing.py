from app.services.user_input.utils.text_cleaner import clean_text


def preprocess_text(text):
    cleaned_text = clean_text(text or "")
    tokens = cleaned_text.split()
    return {
        "cleaned_text": cleaned_text,
        "tokens": tokens,
    }
