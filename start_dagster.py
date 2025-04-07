#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import signal
import platform
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="Запуск dagit (UI) и dagster-daemon в одном файле, с автогенерацией dagster.yaml"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default="3000")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    mosaic_dir = base_dir / "mosaic_conductor"
    if not mosaic_dir.exists():
        print("Папка mosaic_conductor не найдена", file=sys.stderr)
        sys.exit(1)

    # 1) Определяем папку для DAGSTER_HOME (можно взять из .env или задать руками)
    env_dagster_home = os.getenv("DAGSTER_HOME")
    if env_dagster_home:
        dagster_home = Path(env_dagster_home)
    else:
        dagster_home = mosaic_dir / "dagster_home"

    dagster_home.mkdir(parents=True, exist_ok=True)
    (dagster_home / "storage").mkdir(parents=True, exist_ok=True)

    # 2) Формируем абсолютный путь
    final_home = str(dagster_home.resolve()).replace("\\", "/")
    print(f"DAGSTER_HOME: {final_home}")

    # 3) Генерируем (перезаписываем) файл dagster.yaml в папке DAGSTER_HOME
    dagster_yaml_path = dagster_home / "dagster.yaml"
    dagster_yaml_content = f"""\
run_storage:
  module: dagster.core.storage.runs
  class: SqliteRunStorage
  config:
    base_dir: "{final_home}/storage"

event_log_storage:
  module: dagster.core.storage.event_log
  class: SqliteEventLogStorage
  config:
    base_dir: "{final_home}/storage"

schedule_storage:
  module: dagster.core.storage.schedules
  class: SqliteScheduleStorage
  config:
    base_dir: "{final_home}/storage"
"""
    dagster_yaml_path.write_text(dagster_yaml_content, encoding="utf-8")
    print(f"Сгенерирован {dagster_yaml_path}")

    # 4) Устанавливаем переменную окружения (на всякий случай)
    os.environ["DAGSTER_HOME"] = final_home

    # 5) Запускаем daemon + webserver
    daemon_cmd = ["dagster-daemon", "run"]
    webserver_cmd = ["dagit", "--host", args.host, "--port", args.port]

    # Если Linux, оборачиваем команды в xvfb-run для эмуляции дисплея
    if platform.system() == "Linux":
        daemon_cmd = ["xvfb-run", "-a"] + daemon_cmd
        webserver_cmd = ["xvfb-run", "-a"] + webserver_cmd
    print("Запускаем daemon:", " ".join(daemon_cmd))
    print("Запускаем dagit:", " ".join(webserver_cmd))

    daemon_proc = subprocess.Popen(daemon_cmd)
    webserver_proc = subprocess.Popen(webserver_cmd)

    def shutdown(signum, frame):
        print("Останавливаем процессы...")
        daemon_proc.terminate()
        webserver_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while daemon_proc.poll() is None and webserver_proc.poll() is None:
            pass
    except KeyboardInterrupt:
        shutdown(None, None)

    daemon_proc.terminate()
    webserver_proc.terminate()

if __name__ == "__main__":
    main()
