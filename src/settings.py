import os
import json
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
SETTINGS_PATH = os.path.join(ROOT_DIR, "storage", "settings.json")
import torch

DEFAULT_SETTINGS = {
    "temperature": 0.3,
    "repeat_penalty": 1.1,
    "max_tokens": 512,
    "system_prompt": (
        "You are an expert analytical assistant. Use the provided context to answer the user's question. "
        "Synthesize information from ALL parts of the context and make sure it is related to the question asked by the user. "
        "Bear in mind that the context is retrieve from the vector database, and might not exactly matches the user question. The most important thing is to provide the answer based on the user question "
        "If the information is not in the context, clearly state that, but feel free to provide from your general knowledge about the topic, and state if what you provided is from general knowledge and not from the context."
    )
}

def get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"

def load_settings():
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SETTINGS

def save_settings(settings_dict):
    """Saves a settings dictionary straight to the json file."""
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False