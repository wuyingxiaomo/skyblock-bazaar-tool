import json
import os

import requests

from runtime_paths import data_path, ensure_data_dir


BAZAAR_URL = "https://api.hypixel.net/v2/skyblock/bazaar"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DEFAULT_CACHE_FILE = data_path("bazaar_data.json")


def fetch_bazaar_data(api_key="", cache_file=DEFAULT_CACHE_FILE, timeout=30):
    """请求 Bazaar quick_status，并保存可复用的本地缓存。"""
    params = {"key": api_key} if api_key else {}
    try:
        response = requests.get(BAZAAR_URL, headers=HEADERS, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            return [], f"API错误：{payload.get('cause', '未知原因')}"
        rows = []
        for item_id, info in payload.get("products", {}).items():
            quick = info.get("quick_status", {})
            # Hypixel names these from the order-book side: buyPrice is the
            # highest buy order, while sellPrice is the lowest sell order.
            # The UI labels describe our action, so the meanings are reversed.
            buy = quick.get("sellPrice", 0) or 0
            sell = quick.get("buyPrice", 0) or 0
            margin = sell - buy if buy > 0 else 0
            rows.append({
                "name": item_id,
                "buy": buy,
                "sell": sell,
                "margin": margin,
                "pct": round(margin / buy * 100, 2) if buy > 0 else 0,
                "buyOrders": quick.get("buyOrders", 0) or 0,
                "sellOrders": quick.get("sellOrders", 0) or 0,
                "vol_buy": quick.get("buyVolume", 0) or 0,
                "vol_sell": quick.get("sellVolume", 0) or 0,
                "week_buy": quick.get("buyMovingWeek", 0) or 0,
                "week_sell": quick.get("sellMovingWeek", 0) or 0,
            })
        ensure_data_dir()
        temp_file = f"{cache_file}.{os.getpid()}.tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(rows, file, ensure_ascii=False)
        os.replace(temp_file, cache_file)
        return rows, "success"
    except requests.exceptions.HTTPError as exc:
        return [], f"网络请求失败：{exc}"
    except Exception as exc:
        return [], f"网络请求失败：{exc}"
