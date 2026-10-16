import json
import os
import re
import time

import requests

from runtime_paths import data_path, ensure_data_dir


AUCTIONS_URL = "https://api.hypixel.net/v2/skyblock/auctions"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DEFAULT_CACHE_FILE = data_path("auction_data.json")
PAGE_ATTEMPTS = 4
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


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


def _fetch_auction_page(session, page, api_key, timeout):
    """重试完整的响应读取，覆盖分块传输中断和不完整 JSON。"""
    params = {"page": page}
    if api_key:
        params["key"] = api_key
    for attempt in range(1, PAGE_ATTEMPTS + 1):
        retryable = True
        delay = 2 ** (attempt - 1)
        try:
            with session.get(AUCTIONS_URL, headers=HEADERS, params=params, timeout=timeout) as response:
                retryable = response.status_code in RETRYABLE_HTTP_STATUS
                if response.status_code == 429:
                    try:
                        delay = max(delay, min(60, float(response.headers.get("Retry-After", delay))))
                    except (TypeError, ValueError):
                        pass
                response.raise_for_status()
                retryable = True
                payload = response.json()
                if not isinstance(payload, dict) or not payload.get("success"):
                    cause = payload.get("cause") if isinstance(payload, dict) else None
                    raise ValueError(cause or "Auction House API 返回失败")
                if payload.get("page") != page or not isinstance(payload.get("auctions"), list):
                    raise ValueError("Auction House API 返回的页码或拍卖列表无效")
                if type(payload.get("totalPages")) is not int or payload["totalPages"] <= page:
                    raise ValueError("Auction House API 返回的总页数无效")
                return payload
        except (requests.RequestException, ValueError) as exc:
            if not retryable or attempt == PAGE_ATTEMPTS:
                detail = re.sub(r"(?i)([?&]key=)[^&\s]+", r"\1[REDACTED]", str(exc))
                raise RuntimeError(f"第 {page + 1} 页请求失败（已尝试 {attempt} 次）：{detail}") from exc
            time.sleep(delay)


def fetch_auctions(api_key="", cache_file=DEFAULT_CACHE_FILE, timeout=30):
    """逐页请求全部活跃 AH 拍卖；失败页重试，最终失败时保留本地缓存。"""
    try:
        with requests.Session() as session:
            payload = _fetch_auction_page(session, 0, api_key, timeout)
            auctions = list(payload["auctions"])
            total_pages = payload["totalPages"]
            for page in range(1, total_pages):
                page_payload = _fetch_auction_page(session, page, api_key, timeout)
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
