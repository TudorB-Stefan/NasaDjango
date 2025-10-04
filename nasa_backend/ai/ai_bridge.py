import base64
from .program_core import ask_ai

def encode_token(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()

def decode_token(token: str) -> str:
    return base64.urlsafe_b64decode(token.encode()).decode()

def run_ai_from_token(token: str) -> str:
    question = decode_token(token)
    answer = ask_ai(question)
    return encode_token(answer)