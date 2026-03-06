from langdetect import detect

def is_hindi(text):

    try:
        return detect(text) == "hi"
    except:
        return False