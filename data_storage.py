import json

DATA_FILE = "bot_data.json"


def load_data():
    """Загружает данные из файла."""
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"loans": {}}


def save_data(data):
    """Сохраняет данные в файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)