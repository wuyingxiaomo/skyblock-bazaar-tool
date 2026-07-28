import json
import os
import sys
import time

from auction import fetch_auctions
from bazaar_api import fetch_bazaar_data
from runtime_paths import DATA_DIR, ensure_data_dir


APP_DIR = DATA_DIR
STATUS_FILE = os.path.join(APP_DIR, "market_status.json")
LOCK_FILE = os.path.join(APP_DIR, "market_worker.lock")


def get_api_key():
    for name in ("bazaar_config.json", "craft_config.json", "forge_config.json", "enchant_config.json"):
        path = os.path.join(APP_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as file:
                value = json.load(file)
            if value.get("api_key"):
                return value["api_key"]
        except Exception:
            pass
    return ""


def write_status(state, source, message=""):
    ensure_data_dir()
    value = {"state": state, "source": source, "pid": os.getpid(), "message": message, "updated": time.time()}
    temp = f"{STATUS_FILE}.{os.getpid()}.tmp"
    with open(temp, "w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False)
    os.replace(temp, STATUS_FILE)


def main():
    source = "all"
    if "--source" in sys.argv:
        index = sys.argv.index("--source")
        if index + 1 < len(sys.argv):
            source = sys.argv[index + 1]
    key = get_api_key()
    write_status("running", source, "请求中")
    messages = []
    try:
        if source in {"bazaar", "all"}:
            _, message = fetch_bazaar_data(key)
            messages.append(f"BZ: {message}")
        if source in {"auction", "all"}:
            _, message = fetch_auctions(key)
            messages.append(f"AH: {message}")
        write_status("done", source, "；".join(messages))
    except Exception as exc:
        write_status("error", source, str(exc))
    finally:
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass


if __name__ == "__main__":
    main()
