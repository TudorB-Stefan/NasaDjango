import json, faiss
from pathlib import Path
from google import genai
from .program_utils import setup_client, search_semantic, answer_from_hits

INDEX_PATH = Path(__file__).with_name("spacebio.faiss")
IDS_PATH = Path(__file__).with_name("spacebio_ids.json")
TEXTS_PATH = Path(__file__).with_name("spacebio_texts.json")
# INDEX_PATH = Path("spacebio.faiss")
# IDS_PATH = Path("spacebio_ids.json")
# TEXTS_PATH = Path("spacebio_texts.json")
GEN_MODEL = "gemini-2.5-flash"


def ask_ai(question: str, topk: int = 5, use_local: bool = False) -> str:
    client = setup_client(use_local)
    index = faiss.read_index(str(INDEX_PATH))
    with open(IDS_PATH, "r", encoding="utf-8") as f: ids = json.load(f)
    with open(TEXTS_PATH, "r", encoding="utf-8") as f: texts = json.load(f)

    hits = search_semantic(question, index, ids, texts, use_local, client, k=topk)
    if client is None:
        return json.dumps(hits, indent=2)
    return answer_from_hits(question, hits, texts, client)