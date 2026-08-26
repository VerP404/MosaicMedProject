#!/usr/bin/env python3
"""Запуск dagster-webserver (UI) и dagster-daemon с автогенерацией dagster.yaml."""
from __future__ import annotations

import argparse
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Запуск dagster-webserver (UI) и dagster-daemon, с автогенерацией dagster.yaml"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default="3000")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    mosaic_dir = base_dir / "mosaic_conductor"
    if not mosaic_dir.exists():
        print("Папка mosaic_conductor не найдена", file=sys.stderr)
        sys.exit(1)

    workspace = base_dir / "workspace.yaml"
    if not workspace.exists():
        print(f"Не найден {workspace}", file=sys.stderr)
        sys.exit(1)

    # Работаем из корня проекта — иначе workspace.yaml / пакеты могут не подхватиться
    os.chdir(base_dir)

    env_dagster_home = os.getenv("DAGSTER_HOME")
    if env_dagster_home:
        dagster_home = Path(env_dagster_home)
    else:
        dagster_home = mosaic_dir / "dagster_home"

    dagster_home.mkdir(parents=True, exist_ok=True)
    (dagster_home / "storage").mkdir(parents=True, exist_ok=True)

    final_home = str(dagster_home.resolve()).replace("\\", "/")
    print(f"DAGSTER_HOME: {final_home}")

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

run_monitoring:
  enabled: true
  poll_interval_seconds: 30
"""
    dagster_yaml_path.write_text(dagster_yaml_content, encoding="utf-8")
    print(f"Сгенерирован {dagster_yaml_path}")

    os.environ["DAGSTER_HOME"] = final_home

    # CLI лежат в bin/Scripts venv. НЕ делать Path(sys.executable).resolve():
    # на Linux python в .venv/bin — symlink на /usr/bin/python3.x, resolve() уводит в /usr/bin.
    if platform.system() == "Windows":
        scripts_dir = Path(sys.prefix) / "Scripts"
        ext = ".exe"
    else:
        scripts_dir = Path(sys.prefix) / "bin"
        ext = ""
    daemon_bin = scripts_dir / f"dagster-daemon{ext}"
    webserver_bin = scripts_dir / f"dagster-webserver{ext}"
    if not daemon_bin.exists() or not webserver_bin.exists():
        # запасной вариант: рядом с интерпретатором без resolve()
        alt_dir = Path(sys.executable).parent
        alt_daemon = alt_dir / f"dagster-daemon{ext}"
        alt_web = alt_dir / f"dagster-webserver{ext}"
        if alt_daemon.exists() and alt_web.exists():
            scripts_dir, daemon_bin, webserver_bin = alt_dir, alt_daemon, alt_web
        else:
            print(
                f"Не найдены CLI Dagster в {scripts_dir}\n"
                f"  daemon: {daemon_bin.exists()}  webserver: {webserver_bin.exists()}\n"
                f"  sys.executable={sys.executable}  sys.prefix={sys.prefix}\n"
                "Запускайте из активированного .venv или: pip install dagster dagster-webserver",
                file=sys.stderr,
            )
            sys.exit(1)

    # dagit deprecated → dagster-webserver; явно передаём workspace
    daemon_cmd = [str(daemon_bin), "run"]
    webserver_cmd = [
        str(webserver_bin),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "-w",
        str(workspace),
    ]

    use_xvfb = os.getenv("DAGSTER_USE_XVFB", "1").strip().lower() not in {"0", "false", "no"}
    if platform.system() == "Linux" and use_xvfb:
        daemon_cmd = ["xvfb-run", "-a"] + daemon_cmd
        webserver_cmd = ["xvfb-run", "-a"] + webserver_cmd

    print("Запускаем daemon:", " ".join(daemon_cmd))
    print("Запускаем webserver:", " ".join(webserver_cmd))
    print(f"UI: http://127.0.0.1:{args.port}/  (Ctrl+C — остановка)")

    popen_kwargs = {}
    if platform.system() == "Windows":
        # Отдельная группа процессов: Ctrl+C не рвёт детей хаотично до нашего shutdown
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    daemon_proc = subprocess.Popen(daemon_cmd, **popen_kwargs)
    webserver_proc = subprocess.Popen(webserver_cmd, **popen_kwargs)

    stopping = False

    def shutdown(signum=None, frame=None):
        nonlocal stopping
        if stopping:
            return
        stopping = True
        print("\nОстанавливаем процессы...")
        for proc in (daemon_proc, webserver_proc):
            if proc.poll() is None:
                try:
                    proc.terminate()
                except OSError:
                    pass
        deadline = time.time() + 15
        while time.time() < deadline:
            if daemon_proc.poll() is not None and webserver_proc.poll() is not None:
                break
            time.sleep(0.2)
        for proc in (daemon_proc, webserver_proc):
            if proc.poll() is None:
                try:
                    proc.kill()
                except OSError:
                    pass

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    try:
        while not stopping:
            d_code = daemon_proc.poll()
            w_code = webserver_proc.poll()
            if d_code is not None:
                print(f"daemon завершился с кодом {d_code}")
                break
            if w_code is not None:
                print(f"webserver завершился с кодом {w_code}")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()

    if not stopping:
        shutdown()

    sys.exit(1 if (daemon_proc.returncode or webserver_proc.returncode) else 0)


if __name__ == "__main__":
    main()
