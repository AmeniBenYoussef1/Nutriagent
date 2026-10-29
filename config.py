import os
from dotenv import load_dotenv

load_dotenv(override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

VISION_MODEL = os.getenv("VISION_MODEL", "claude-sonnet-4-6")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Modal-hosted fine-tuned specialist model ---
MODAL_SPECIALIST_URL = os.getenv("MODAL_SPECIALIST_URL", "")  # empty = use fallback heuristic

# --- Vector store for the frontier/RAG agent ---
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "./vectorstore")

# --- Persistence ---
MEMORY_PATH = os.getenv("MEMORY_PATH", "./memory.json")

# --- Default goals if the user hasn't set any yet ---
DEFAULT_DAILY_CALORIES = 2000
DEFAULT_PROTEIN_G = 120
DEFAULT_CARBS_G = 220
DEFAULT_FAT_G = 65


def get_anthropic_client():
    if not ANTHROPIC_API_KEY:
        return None
    from anthropic import Anthropic

    return Anthropic(api_key=ANTHROPIC_API_KEY)


def get_gemini_model():
    if not GEMINI_API_KEY:
        return None
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL)