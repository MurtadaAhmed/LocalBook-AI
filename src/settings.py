import os
import json
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
SETTINGS_PATH = os.path.join(ROOT_DIR, "storage", "settings.json")

DEFAULT_SETTINGS = {
    "temperature": 0.3,
    "repeat_penalty": 1.15,
    "max_tokens": 4096,
    "system_prompt": (
        "You are an expert analytical assistant. Use the provided context to comprehensively answer the user's question. "
        "Synthesize information from multiple parts of the text if necessary to provide a detailed, well-structured response. "
        "Use bullet points or markdown formatting to make complex information easy to read. "
        "If the information is not in the context, clearly state that."
    )
}

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