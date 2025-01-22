import subprocess
import os

def update_logs():
  try:
     #проверяем наличие изменений в logs.txt
    if os.path.exists("logs.txt"):
      subprocess.run(["git", "add", "logs.txt"], check=True)
      subprocess.run(["git", "commit", "-m", "Обновление логов"], check=True)
      subprocess.run(["git", "push", "origin", "main"], check=True)
      print("Файлы успешно обновлены на GitHub.")
    else:
      print("Файл logs.txt не найден.")
  except subprocess.CalledProcessError as e:
    print(f"Ошибка при обновлении логов на GitHub: {e}")
update_logs()