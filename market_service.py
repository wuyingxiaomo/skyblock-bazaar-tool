import json
import os
import subprocess
import sys
import time

from runtime_paths import DATA_DIR, SOURCE_DIR, ensure_data_dir


APP_DIR = DATA_DIR
WORKER_FILE = os.path.join(SOURCE_DIR, "market_worker.py")
STATUS_FILE = os.path.join(APP_DIR, "market_status.json")
LOCK_FILE = os.path.join(APP_DIR, "market_worker.lock")


def read_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def request_refresh(source):
    """启动独立请求进程；已有请求时复用，不重复请求。"""
    ensure_data_dir()
    status = read_status()
    if status.get("state") in {"queued", "running"} and _pid_alive(status.get("pid")):
        return status
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        status = read_status()
        queued_recently = status.get("state") == "queued" and time.time() - float(status.get("updated", 0) or 0) < 60
        if status.get("state") == "running" and _pid_alive(status.get("pid")) or queued_recently:
            return status
        try:
            os.remove(LOCK_FILE)
        except OSError:
            return status
        return request_refresh(source)
    except OSError:
        return {}

    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
    queued = {"state": "queued", "source": source, "pid": 0, "updated": time.time()}
    with open(STATUS_FILE, "w", encoding="utf-8") as file:
        json.dump(queued, file, ensure_ascii=False)
    try:
        command = ([sys.executable, "--worker"] if getattr(sys, "frozen", False)
                   else [sys.executable, WORKER_FILE])
        process = subprocess.Popen(
            command + ["--source", source],
            cwd=APP_DIR,
            creationflags=flags,
            close_fds=True,
        )
        status = {"state": "queued", "source": source, "pid": process.pid, "updated": time.time()}
        current = read_status()
        if current.get("state") not in {"done", "error"}:
            with open(STATUS_FILE, "w", encoding="utf-8") as file:
                json.dump(status, file, ensure_ascii=False)
        return status
    except Exception:
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass
        return {}
