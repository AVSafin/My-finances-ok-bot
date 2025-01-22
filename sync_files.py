import os
import requests

# Укажите URL для загрузки файлов в ChatGPT (получаете при загрузке файлов вручную)
UPLOAD_URL = "https://chatai.openai.com/upload"

# Укажите директории и файлы, которые хотите синхронизировать
FILES_TO_SYNC = [
    "main.py",
    "bot.py",
    "requirements.txt",
    "handlers",
    "loan_handlers",
    "keyboards",
    "utils"
]

def upload_file(file_path):
    """Загружает файл на сервер ChatGPT."""
    with open(file_path, "rb") as file:
        response = requests.post(UPLOAD_URL, files={"file": file})
        if response.status_code == 200:
            print(f"Файл {file_path} успешно загружен.")
        else:
            print(f"Ошибка при загрузке {file_path}: {response.text}")

def sync_files():
    """Синхронизирует указанные файлы и директории."""
    for path in FILES_TO_SYNC:
        if os.path.isfile(path):
            upload_file(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    upload_file(full_path)

if __name__ == "__main__":
    sync_files()