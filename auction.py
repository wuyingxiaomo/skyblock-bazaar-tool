import json
import os
import re
import time

import requests

from runtime_paths import data_path, ensure_data_dir


AUCTIONS_URL = "https://api.hypixel.net/v2/skyblock/auctions"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DEFAULT_CACHE_FILE = data_path("auction_data.json")


def normalize_key(value):
    value = str(value or "")
    value = re.sub(r"§.", "", value).strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _read_cache(cache_file):
    if not os.path.exists(cache_file):
        return []
    try:
        with open(cache_file, "r", encoding="utf-8") as file:
            value = json.load(file)
        if isinstance(value, dict):
            return value.get("auctions", [])
        return value if isinstance(value, list) else []
    except Exception:
        return []


def fetch_auctions(api_key="", cache_file=DEFAULT_CACHE_FILE, timeout=30):
    """请求全部活跃 AH 拍卖；失败时返回本地缓存。"""
    params = {"page": 0}
    if api_key:
        params["key"] = api_key
    try:
        first = requests.get(AUCTIONS_URL, headers=HEADERS, params=params, timeout=timeout)
        first.raise_for_status()
        payload = first.json()
        if not payload.get("success"):
            raise RuntimeError(payload.get("cause", "Auction House API 返回失败"))
        auctions = list(payload.get("auctions", []))
        total_pages = int(payload.get("totalPages", 1) or 1)
        for page in range(1, total_pages):
            page_params = {"page": page}
            if api_key:
                page_params["key"] = api_key
            response = requests.get(AUCTIONS_URL, headers=HEADERS, params=page_params, timeout=timeout)
            response.raise_for_status()
            page_payload = response.json()
            if page_payload.get("success"):
                auctions.extend(page_payload.get("auctions", []))
        ensure_data_dir()
        temp_file = f"{cache_file}.{os.getpid()}.tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump({"updated": int(time.time()), "auctions": auctions}, file, ensure_ascii=False)
        os.replace(temp_file, cache_file)
        return auctions, f"Auction House 已更新（{len(auctions)} 条）"
    except Exception as exc:
        cached = _read_cache(cache_file)
        if cached:
            return cached, f"Auction House 请求失败，使用缓存（{len(cached)} 条）：{exc}"
        return [], f"Auction House 请求失败：{exc}"


def build_bin_index(auctions):
    """按 internal ID、extra、物品名称建立最低 BIN 索引。"""
    index = {}
    for auction in auctions:
        if not isinstance(auction, dict) or not auction.get("bin"):
            continue
        try:
            price = float(auction.get("starting_bid", 0) or 0)
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        keys = {
            str(auction.get("extra", "")).upper(),
            normalize_key(auction.get("extra", "")),
            normalize_key(auction.get("item_name", "")),
        }
        keys.discard("")
        for key in keys:
            current = index.setdefault(key, {"lowest_bin": price, "bin_count": 0, "item_name": auction.get("item_name", "")})
            current["lowest_bin"] = min(current["lowest_bin"], price)
            current["bin_count"] += 1
    return index


def lookup_bin(index, item_id, display_name=""):
    for key in (str(item_id or "").upper(), normalize_key(item_id), normalize_key(display_name)):
        if key in index:
            return index[key]
    return None
