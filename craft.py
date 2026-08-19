import ctypes
import ctypes.wintypes
import json
import math
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk

import requests
from auction import build_bin_index, fetch_auctions, lookup_bin
from bazaar_api import fetch_bazaar_data
from market_service import read_status, request_refresh
from runtime_paths import DATA_DIR, RESOURCE_DIR, SOURCE_DIR, ensure_data_dir


APP_DIR = DATA_DIR
SOURCE_APP_DIR = SOURCE_DIR
CONFIG_FILE = os.path.join(APP_DIR, "craft_config.json")
LEGACY_CONFIG_FILE = os.path.join(APP_DIR, "config.json")
DATA_CACHE_FILE = os.path.join(APP_DIR, "bazaar_data.json")
RECIPE_DIR = os.path.join(RESOURCE_DIR, "craft_recipe", "items")
RECIPE_DIRS = [RECIPE_DIR]
APP_TITLE = "Skyblock Craft 主界面"
REQUIRE_AH_PRICE = False
USE_AH_FALLBACK = True
BAZAAR_URL = "https://api.hypixel.net/skyblock/bazaar"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/150.0.0.0"}
UNIT_SCALE = {"默认": 1, "k": 1000, "m": 1000000, "b": 1000000000}
HYPIXEL_API_KEY = ""


COL_META = [
    {"cid": "name", "name": "物品ID", "is_num": False},
    {"cid": "item_buy", "name": "物品收购价", "is_num": True},
    {"cid": "item_sell", "name": "物品出售价", "is_num": True},
    {"cid": "item_ah", "name": "AH最低一口价", "is_num": True},
    {"cid": "recipe", "name": "合成配方的材料", "is_num": False},
    {"cid": "mat_buy", "name": "材料收购价", "is_num": True},
    {"cid": "mat_sell", "name": "材料出售价", "is_num": True},
    {"cid": "buy_mat_buy", "name": "收购价-材料收购", "is_num": True},
    {"cid": "buy_mat_sell", "name": "收购价-材料出售", "is_num": True},
    {"cid": "sell_mat_buy", "name": "出售价-材料收购", "is_num": True},
    {"cid": "sell_mat_sell", "name": "出售价-材料出售", "is_num": True},
    {"cid": "rate_buy_mat_buy", "name": "收购价/材料收购利润率%", "is_num": True},
    {"cid": "rate_buy_mat_sell", "name": "收购价/材料出售利润率%", "is_num": True},
    {"cid": "rate_sell_mat_buy", "name": "出售价/材料收购利润率%", "is_num": True},
    {"cid": "rate_sell_mat_sell", "name": "出售价/材料出售利润率%", "is_num": True},
    {"cid": "item_buyOrders", "name": "物品收购挂单量", "is_num": True},
    {"cid": "item_sellOrders", "name": "物品出售挂单量", "is_num": True},
    {"cid": "item_vol_buy", "name": "物品总收购成交量", "is_num": True},
    {"cid": "item_vol_sell", "name": "物品总出售成交量", "is_num": True},
    {"cid": "item_week_buy", "name": "物品7日收购成交量", "is_num": True},
    {"cid": "item_week_sell", "name": "物品7日出售成交量", "is_num": True},
    {"cid": "mat_buyOrders", "name": "材料收购订单数（合计）", "is_num": True},
    {"cid": "mat_sellOrders", "name": "材料出售订单数（合计）", "is_num": True},
    {"cid": "mat_vol_buy", "name": "材料总收购量（各材料合计）", "is_num": True},
    {"cid": "mat_vol_sell", "name": "材料总出售量（各材料合计）", "is_num": True},
    {"cid": "mat_week_buy", "name": "材料7日收购量（各材料合计）", "is_num": True},
    {"cid": "mat_week_sell", "name": "材料7日出售量（各材料合计）", "is_num": True},
    {"cid": "mat_craft_buy", "name": "材料可制作数量（收购量）", "is_num": True},
    {"cid": "mat_craft_sell", "name": "材料可制作数量（出售量）", "is_num": True},
    {"cid": "mat_craft_week_buy", "name": "材料可制作数量（7日收购）", "is_num": True},
    {"cid": "mat_craft_week_sell", "name": "材料可制作数量（7日出售）", "is_num": True},
]
COL_CID_LIST = [x["cid"] for x in COL_META]
COL_NAME_MAP = {x["cid"]: x["name"] for x in COL_META}
COL_ISNUM_MAP = {x["cid"]: x["is_num"] for x in COL_META}
DISPLAY_NO_UNIT_CIDS = set()
DEFAULT_WIDTHS = {"name": 230, "recipe": 300}
for _meta in COL_META:
    DEFAULT_WIDTHS.setdefault(_meta["cid"], 115)

sort_key = "sell_mat_sell"
sort_reverse = True
item_data_cache = []
recipe_map = {}
auction_index = {}
auction_loading = False
bazaar_loading = False
is_topmost = False
search_query = ""
btn_order = []
shortcut_map = {"search": "CTRL+F"}
shortcut_global = {"search": False}
shortcut_win_geometry = None
search_win_geometry = None
col_order = list(COL_CID_LIST)
col_width_map = dict(DEFAULT_WIDTHS)
col_var_map = {}
filter_min_var_map = {}
filter_max_var_map = {}
unit_var_map = {}
filter_sources = {"bazaar": True, "auction": True}
setting_win = None
setting_win_geometry = None
pw_sash_positions = None
panel_scroll = {}
panel_col_widths = {"check": 150, "field": 220, "min": 130, "max": 130, "unit": 100}
panel_column_order = ["check", "field", "min", "max", "unit"]
tree_scroll_x = 0
tree_scroll_y = 0
_prev_shortcut_map = {}
_global_hotkey_thread = None
_global_hotkey_stop = threading.Event()
_held_keys = set()
_combo_bindings = {}
_combo_listeners_bound = False
root = None
tree = None
top_canvas = None
top_frame = None
status_var = None


def read_config():
    config_path = CONFIG_FILE if os.path.exists(CONFIG_FILE) else LEGACY_CONFIG_FILE
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_config(cfg):
    ensure_data_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def save_api_key(key):
    cfg = read_config()
    cfg["api_key"] = key
    try:
        write_config(cfg)
    except Exception:
        pass


def load_api_key():
    global HYPIXEL_API_KEY
    key = read_config().get("api_key", "")
    HYPIXEL_API_KEY = key if isinstance(key, str) else ""


def prompt_api_key(parent=None, current_key=""):
    dlg = tk.Toplevel(parent) if parent else tk.Tk()
    dlg.title("请输入 API Key")
    dlg.resizable(False, False)
    dlg.attributes("-topmost", True)
    result = [None]
    tk.Label(dlg, text="请输入 Hypixel API Key：", font=("", 12)).pack(padx=20, pady=(15, 5))
    entry = tk.Entry(dlg, width=50, font=("", 11))
    entry.insert(0, current_key)
    entry.pack(padx=20, pady=5)
    tk.Label(dlg, text="⚠ 请勿泄露自己的 API Key！！！", fg="red", font=("", 12, "bold")).pack(padx=20, pady=5)
    buttons = tk.Frame(dlg)
    buttons.pack(pady=(5, 15))

    def ok():
        result[0] = entry.get().strip()
        dlg.destroy()

    def cancel():
        dlg.destroy()

    tk.Button(buttons, text="确认", command=ok, width=10).pack(side=tk.LEFT, padx=8)
    tk.Button(buttons, text="取消", command=cancel, width=10).pack(side=tk.LEFT, padx=8)
    entry.bind("<Return>", lambda _event: ok())
    dlg.protocol("WM_DELETE_WINDOW", cancel)
    if parent:
        dlg.transient(parent)
        dlg.grab_set()
        dlg.wait_window()
    else:
        dlg.mainloop()
    return result[0]


def open_api_dialog():
    global HYPIXEL_API_KEY
    key = prompt_api_key(root, HYPIXEL_API_KEY)
    if key is not None:
        HYPIXEL_API_KEY = key
        save_api_key(key)
        status_var.set("API Key 已保存" if key else "API Key 已清空")


def fetch_data():
    params = {"key": HYPIXEL_API_KEY} if HYPIXEL_API_KEY else {}
    try:
        response = requests.get(BAZAAR_URL, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            return [], f"API错误：{payload.get('cause', '未知原因')}"
    except requests.exceptions.HTTPError as exc:
        return [], f"网络请求失败：{exc}"
    except Exception as exc:
        return [], f"网络请求失败：{exc}"

    rows = []
    for item_id, info in payload.get("products", {}).items():
        quick = info.get("quick_status", {})
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
    return rows, "success"


def load_cached_data():
    if not os.path.exists(DATA_CACHE_FILE):
        return []
    try:
        with open(DATA_CACHE_FILE, "r", encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, list) else []
    except Exception:
        return []


def refresh_table():
    refresh_bazaar_data()
    refresh_auction_data()


def refresh_bazaar_data():
    global bazaar_loading, item_data_cache
    if bazaar_loading:
        return
    bazaar_loading = True
    status_var.set("正在后台请求 Bazaar...")

    def worker():
        data, message = fetch_bazaar_data(HYPIXEL_API_KEY)

        def finish():
            global bazaar_loading, item_data_cache
            bazaar_loading = False
            if message == "success":
                item_data_cache = data
                apply_filter_sort(save_current_widths=False)
                status_var.set(f"Bazaar 数据已更新：{len(data)} 条")
            else:
                status_var.set(message)

        try:
            root.after(0, finish)
        except tk.TclError:
            pass

    threading.Thread(target=worker, daemon=True).start()


def refresh_auction_data():
    global auction_loading
    if auction_loading:
        return
    auction_loading = True
    status_var.set("正在后台请求 Auction House...")

    def worker():
        auctions, message = fetch_auctions(HYPIXEL_API_KEY)
        index = build_bin_index(auctions)

        def finish():
            global auction_index, auction_loading
            auction_index = index
            auction_loading = False
            if item_data_cache:
                apply_filter_sort(save_current_widths=False)
            status_var.set(message)

        try:
            root.after(0, finish)
        except tk.TclError:
            pass

    threading.Thread(target=worker, daemon=True).start()


def parse_recipe_entry(value):
    if not isinstance(value, str) or ":" not in value:
        return None
    item_id, amount_text = value.rsplit(":", 1)
    item_id = item_id.strip()
    try:
        amount = float(amount_text)
    except (TypeError, ValueError):
        return None
    if not item_id or amount <= 0:
        return None
    return item_id, amount


def parse_recipe_object(recipe):
    if not isinstance(recipe, dict):
        return None
    materials = {}
    for key, value in recipe.items():
        if str(key).lower() in {"type", "count", "output", "output_count"}:
            continue
        parsed = parse_recipe_entry(value)
        if parsed:
            item_id, amount = parsed
            materials[item_id] = materials.get(item_id, 0) + amount
    if not materials:
        return None
    try:
        output_count = float(recipe.get("count", 1) or 1)
    except (TypeError, ValueError):
        output_count = 1
    if output_count <= 0:
        output_count = 1
    return {"materials": {k: v / output_count for k, v in materials.items()}, "output_count": output_count}


def get_item_recipe(item_data):
    single = parse_recipe_object(item_data.get("recipe"))
    if single:
        return single
    recipes = item_data.get("recipes", [])
    if isinstance(recipes, list):
        for recipe in recipes:
            if not isinstance(recipe, dict):
                continue
            recipe_type = str(recipe.get("type", "crafting")).lower()
            if recipe_type not in {"crafting", "craft"}:
                continue
            parsed = parse_recipe_object(recipe)
            if parsed:
                return parsed
    return None


def load_recipe_map():
    result = {}
    for recipe_dir in RECIPE_DIRS:
        if not os.path.isdir(recipe_dir):
            continue
        for filename in os.listdir(recipe_dir):
            if not filename.lower().endswith(".json"):
                continue
            path = os.path.join(recipe_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    item_data = json.load(f)
                recipe = get_item_recipe(item_data)
                item_id = item_data.get("internalname") or os.path.splitext(filename)[0]
                if recipe and item_id:
                    result[item_id] = recipe
            except (OSError, ValueError, TypeError):
                continue
    return result


def format_quantity(value):
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def format_recipe(materials):
    return " + ".join(f"{item_id} x {format_quantity(amount)}" for item_id, amount in sorted(materials.items()))


def bazaar_material_entries(materials, market_by_id):
    """Return only materials backed by Bazaar data.

    AH fallback rows are useful for displaying an item's AH price, but they
    must not make the Bazaar material calculations unavailable.
    """
    return [
        (item_id, amount, market_by_id[item_id])
        for item_id, amount in materials.items()
        if item_id in market_by_id
        and market_by_id[item_id].get("_source", "bazaar") == "bazaar"
    ]


def aggregate_material_cost(materials, market_by_id, field):
    entries = bazaar_material_entries(materials, market_by_id)
    if not entries:
        return None
    total = 0
    for _item_id, amount, market_row in entries:
        value = market_row.get(field)
        if value is None:
            return None
        total += amount * value
    return total


def aggregate_material_metric(materials, market_by_id, field):
    total = 0
    found = False
    for _item_id, _amount, market_row in bazaar_material_entries(materials, market_by_id):
        value = market_row.get(field)
        if value is None:
            return None
        total += value
        found = True
    # AH-only and completely unavailable recipes have no Bazaar metric.
    return total if found else None


def material_craft_capacity(materials, market_by_id, field):
    """按 Bazaar 材料的最小供应比例计算完整成品数量。"""
    capacities = []
    for _item_id, amount, market_row in bazaar_material_entries(materials, market_by_id):
        if amount <= 0:
            return None
        value = market_row.get(field)
        if value is None:
            return None
        capacities.append(value / amount)
    return math.floor(min(capacities)) if capacities else None


def build_craft_rows(raw_data):
    market_by_id = {
        row.get("name"): {**row, "_source": "bazaar"}
        for row in raw_data
        if row.get("name")
    }
    recipe_ids = set(recipe_map)
    recipe_materials = {mid for recipe in recipe_map.values() for mid in recipe.get("materials", {})}
    for item_id in recipe_ids | recipe_materials:
        if item_id in market_by_id:
            continue
        auction = lookup_bin(auction_index, item_id) if USE_AH_FALLBACK else None
        if auction:
            price = auction["lowest_bin"]
            market_by_id[item_id] = {
                "name": item_id,
                "buy": price,
                "sell": price,
                "buyOrders": None,
                "sellOrders": None,
                "vol_buy": None,
                "vol_sell": None,
                "week_buy": None,
                "week_sell": None,
                "_source": "auction",
            }
    rows = []
    for item_id, recipe in recipe_map.items():
        item_ah = lookup_bin(auction_index, item_id) or {}
        if REQUIRE_AH_PRICE and not item_ah.get("lowest_bin"):
            continue
        item = market_by_id.get(item_id)
        if not item:
            continue
        materials = recipe["materials"]
        mat_buy = aggregate_material_cost(materials, market_by_id, "buy")
        mat_sell = aggregate_material_cost(materials, market_by_id, "sell")

        item_buy = item.get("buy", 0) or 0
        item_sell = item.get("sell", 0) or 0
        values = {
            "name": item_id,
            "item_buy": item_buy,
            "item_sell": item_sell,
            "item_ah": item_ah.get("lowest_bin"),
            "recipe": format_recipe(materials),
            "mat_buy": mat_buy,
            "mat_sell": mat_sell,
        }
        for field in ("buyOrders", "sellOrders", "vol_buy", "vol_sell", "week_buy", "week_sell"):
            values[f"item_{field}"] = (
                item.get(field)
                if item.get("_source", "bazaar") == "bazaar"
                else None
            )
        for field in ("buyOrders", "sellOrders", "vol_buy", "vol_sell", "week_buy", "week_sell"):
            values[f"mat_{field}"] = aggregate_material_metric(materials, market_by_id, field)
        for output_field, source_field in (
            ("mat_craft_buy", "vol_buy"),
            ("mat_craft_sell", "vol_sell"),
            ("mat_craft_week_buy", "week_buy"),
            ("mat_craft_week_sell", "week_sell"),
        ):
            values[output_field] = material_craft_capacity(materials, market_by_id, source_field)

        pairs = {
            "buy_mat_buy": (item_buy, mat_buy),
            "buy_mat_sell": (item_buy, mat_sell),
            "sell_mat_buy": (item_sell, mat_buy),
            "sell_mat_sell": (item_sell, mat_sell),
        }
        for profit_field, (output_price, material_cost) in pairs.items():
            values[profit_field] = output_price - material_cost if material_cost is not None else None
            rate_field = "rate_" + profit_field
            values[rate_field] = (
                values[profit_field] / material_cost * 100
                if material_cost is not None and material_cost > 0
                else None
            )
        rows.append(values)
    return rows


def parse_filter_number(value, default):
    value = value.strip().upper()
    if not value:
        return default
    multiplier = 1
    if value.endswith("K"):
        multiplier, value = 1000, value[:-1]
    elif value.endswith("M"):
        multiplier, value = 1000000, value[:-1]
    elif value.endswith("B"):
        multiplier, value = 1000000000, value[:-1]
    try:
        return float(value) * multiplier
    except ValueError:
        return default


def format_value(value, unit, _cid=None):
    if value is None:
        return "-"
    return f"{round(value / UNIT_SCALE.get(unit, 1), 2)}"


def get_visible_cols():
    return [cid for cid in col_order if col_var_map[cid].get()]


def row_matches_filter_sources(row):
    """按当前数据源选择决定配方行是否显示。"""
    # Enchant 复用 Craft，但已移除 AH 字段，因此只有 Bazaar 数据源能显示配方。
    if "item_ah" not in COL_CID_LIST:
        return filter_sources.get("bazaar", True)
    use_bazaar = filter_sources.get("bazaar", True)
    use_auction = filter_sources.get("auction", True)
    has_auction_price = row.get("item_ah") is not None
    if use_bazaar and use_auction:
        return True
    if use_bazaar:
        return not has_auction_price
    if use_auction:
        return has_auction_price
    return False


def filter_rows(rows):
    result = []
    for row in rows:
        if not row_matches_filter_sources(row):
            continue
        valid = True
        for meta in COL_META:
            cid = meta["cid"]
            if not meta["is_num"]:
                continue
            source = "auction" if cid == "item_ah" else "bazaar"
            if not filter_sources.get(source, True):
                continue
            value = row.get(cid)
            if value is None:
                if filter_min_var_map[cid].get().strip() or filter_max_var_map[cid].get().strip():
                    valid = False
                    break
                continue
            unit = UNIT_SCALE.get(unit_var_map[cid].get(), 1)
            minimum = parse_filter_number(filter_min_var_map[cid].get(), -float("inf")) * unit
            maximum = parse_filter_number(filter_max_var_map[cid].get(), float("inf")) * unit
            if value < minimum or value > maximum:
                valid = False
                break
        if valid:
            result.append(row)
    return result


def open_search_dialog():
    """以记事本式的方向和循环规则定位 Craft/Enchant 表格中的物品 ID。"""
    global search_query
    dialog = tk.Toplevel(root)
    dialog.title("查找")
    dialog.resizable(False, False)
    dialog.geometry(search_win_geometry or "430x190")
    dialog.transient(root)
    dialog.grab_set()

    query_var = tk.StringVar(value=search_query)
    direction_var = tk.StringVar(value="down")
    cycle_var = tk.BooleanVar(value=True)
    result_var = tk.StringVar(value="")
    frame = ttk.Frame(dialog, padding=14)
    frame.pack(fill=tk.BOTH, expand=True)
    ttk.Label(frame, text="查找物品ID：").grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="w")
    entry = ttk.Entry(frame, textvariable=query_var, width=36)
    entry.grid(row=0, column=1, columnspan=2, pady=(0, 10), sticky="ew")

    direction = ttk.LabelFrame(frame, text="方向")
    direction.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 8), pady=(0, 8))
    ttk.Radiobutton(direction, text="向上", variable=direction_var, value="up").pack(side=tk.LEFT, padx=8, pady=4)
    ttk.Radiobutton(direction, text="向下", variable=direction_var, value="down").pack(side=tk.LEFT, padx=8, pady=4)
    ttk.Checkbutton(frame, text="循环查找", variable=cycle_var).grid(row=1, column=2, sticky="w", pady=(0, 8))
    ttk.Label(frame, textvariable=result_var, foreground="#666").grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))

    def find_next():
        global search_query
        term = query_var.get().strip().upper().replace(" ", "_")
        if not term:
            result_var.set("请输入要查找的物品 ID")
            return
        search_query = query_var.get()
        items = list(tree.get_children())
        if not items:
            result_var.set("当前没有可查找的数据")
            return
        selected = tree.selection()
        current = items.index(selected[0]) if selected and selected[0] in items else None
        step = -1 if direction_var.get() == "up" else 1
        start = (current + step) if current is not None else (len(items) - 1 if step < 0 else 0)
        if step > 0:
            indexes = list(range(max(start, 0), len(items)))
            if cycle_var.get():
                indexes.extend(range(0, min(max(start, 0), len(items))))
        else:
            indexes = list(range(min(start, len(items) - 1), -1, -1))
            if cycle_var.get():
                indexes.extend(range(len(items) - 1, max(min(start, len(items) - 1), -1), -1))
        name_index = COL_CID_LIST.index("name")
        for index in indexes:
            item = items[index]
            values = tree.item(item, "values")
            if name_index < len(values) and term in str(values[name_index]).upper():
                tree.selection_set(item)
                tree.focus(item)
                tree.see(item)
                result_var.set(f"已找到：{values[name_index]}")
                return
        result_var.set("找不到匹配项" if cycle_var.get() else "已到达查找方向的末尾")

    def on_return(_event):
        find_next()
        return "break"

    buttons = ttk.Frame(frame)
    buttons.grid(row=3, column=0, columnspan=3, pady=(2, 0))
    ttk.Button(buttons, text="查找下一个", command=find_next).pack(side=tk.LEFT, padx=5)
    def close_dialog():
        global search_win_geometry
        search_win_geometry = dialog.geometry()
        _save_search_geometry(search_win_geometry)
        dialog.destroy()

    ttk.Button(buttons, text="关闭", command=close_dialog).pack(side=tk.LEFT, padx=5)
    dialog.protocol("WM_DELETE_WINDOW", close_dialog)
    entry.bind("<Return>", on_return)
    entry.focus_set()
    entry.select_range(0, tk.END)


def _save_search_geometry(geometry):
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                value = json.load(file)
                if isinstance(value, dict):
                    cfg = value
        except Exception:
            pass
    cfg["search_win_geometry"] = geometry
    try:
        write_config(cfg)
    except Exception:
        pass


def apply_filter_sort(save_current_widths=True):
    if save_current_widths and tree.get_children():
        for cid in col_width_map:
            try:
                col_width_map[cid] = tree.column(cid, "width")
            except tk.TclError:
                pass
    rows = filter_rows(build_craft_rows(item_data_cache))
    key = sort_key if sort_key in COL_CID_LIST else "sell_mat_sell"
    rows.sort(key=lambda row: (row.get(key) is not None, row.get(key) or 0), reverse=sort_reverse)
    tree.delete(*tree.get_children())
    visible_cols = get_visible_cols()
    # 保持完整逻辑列，displaycolumns 只负责控制显示和顺序。
    tree["columns"] = COL_CID_LIST
    tree["displaycolumns"] = visible_cols
    units = {cid: unit_var_map[cid].get() or "默认" for cid in unit_var_map}
    for row in rows:
        display = []
        for cid in visible_cols:
            display.append(row.get(cid) if not COL_ISNUM_MAP[cid] else format_value(row.get(cid), units[cid], cid))
        tree.insert("", tk.END, values=[row.get(cid) if not COL_ISNUM_MAP[cid] else format_value(row.get(cid), units[cid], cid) for cid in COL_CID_LIST])
    arrow = " ↓" if sort_reverse else " ↑"
    for cid in COL_CID_LIST:
        heading = COL_NAME_MAP[cid]
        if COL_ISNUM_MAP[cid] and cid not in DISPLAY_NO_UNIT_CIDS:
            heading += f"({units.get(cid, '默认')})"
        if cid == key:
            heading += arrow
        tree.heading(cid, text=heading, command=lambda selected=cid: on_header_click(selected))
        tree.column(cid, width=col_width_map.get(cid, 115), minwidth=50, stretch=False)
    status_var.set(f"缓存物品{len(item_data_cache)}条，配方结果{len(rows)}条")


def on_header_click(cid):
    global sort_key, sort_reverse
    if cid == sort_key:
        sort_reverse = not sort_reverse
    else:
        sort_key, sort_reverse = cid, True
    apply_filter_sort()


def _bind_panel_mousewheel(widget, canvas):
    def on_enter(_event):
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"))

    def on_leave(_event):
        canvas.unbind_all("<MouseWheel>")

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def on_unit_change(_event=None):
    apply_filter_sort()


def _legacy_open_param_panel():
    global setting_win, setting_win_geometry, pw_sash_positions, panel_scroll
    if setting_win and setting_win.winfo_exists():
        setting_win.lift()
        return
    setting_win = tk.Toplevel(root)
    setting_win.title("Craft 参数设置")
    setting_win.geometry(setting_win_geometry or "1100x750")
    setting_win.transient(root)
    setting_win.grab_set()

    panel_snapshot = {
        "columns": {cid: col_var_map[cid].get() for cid in COL_CID_LIST},
        "filter_min": {cid: filter_min_var_map[cid].get() for cid in COL_CID_LIST},
        "filter_max": {cid: filter_max_var_map[cid].get() for cid in COL_CID_LIST},
        "units": {cid: unit_var_map[cid].get() for cid in COL_CID_LIST},
    }

    pw = ttk.PanedWindow(setting_win, orient=tk.HORIZONTAL)
    pw.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    frame_check = ttk.LabelFrame(pw, text="显示列勾选")
    frame_filter = ttk.LabelFrame(pw, text="数值筛选（最低 / 最高）")
    frame_unit = ttk.LabelFrame(pw, text="单位切换")
    pw.add(frame_check, weight=1)
    pw.add(frame_filter, weight=3)
    pw.add(frame_unit, weight=1)

    def create_scroll_area(parent):
        canvas = tk.Canvas(parent)
        scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=canvas.xview)
        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _bind_panel_mousewheel(parent, canvas)
        return canvas, inner

    canvas_check, inner_check = create_scroll_area(frame_check)
    canvas_filter, inner_filter = create_scroll_area(frame_filter)
    canvas_unit, inner_unit = create_scroll_area(frame_unit)
    inner_filter.columnconfigure(0, weight=1)
    inner_filter.columnconfigure(1, weight=1)
    inner_filter.columnconfigure(2, weight=1)

    for index, meta in enumerate(COL_META):
        cid = meta["cid"]
        ttk.Checkbutton(inner_check, text=meta["name"], variable=col_var_map[cid], command=apply_filter_sort).pack(anchor="w", pady=4)
        if meta["is_num"]:
            ttk.Label(inner_filter, text=meta["name"], width=28, anchor="w").grid(row=index, column=0, sticky="ew", padx=2, pady=6)
            ttk.Entry(inner_filter, textvariable=filter_min_var_map[cid], width=15).grid(row=index, column=1, padx=3, pady=6)
            ttk.Entry(inner_filter, textvariable=filter_max_var_map[cid], width=15).grid(row=index, column=2, padx=3, pady=6)
            ttk.Combobox(inner_unit, values=list(UNIT_SCALE), state="readonly", textvariable=unit_var_map[cid], width=10).pack(anchor="w", padx=2, pady=6)
        else:
            ttk.Label(inner_filter, text=meta["name"], width=28, anchor="w").grid(row=index, column=0, sticky="ew", padx=2, pady=6)
            ttk.Label(inner_filter, text="不支持数值筛选", foreground="#888").grid(row=index, column=1, columnspan=2, padx=3, pady=6)

    for widget in inner_unit.winfo_children():
        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", on_unit_change)

    def restore_panel_snapshot():
        for cid in COL_CID_LIST:
            col_var_map[cid].set(panel_snapshot["columns"][cid])
            filter_min_var_map[cid].set(panel_snapshot["filter_min"][cid])
            filter_max_var_map[cid].set(panel_snapshot["filter_max"][cid])
            unit_var_map[cid].set(panel_snapshot["units"][cid])
        apply_filter_sort()

    def close_panel(discard_changes=False):
        global setting_win, setting_win_geometry, pw_sash_positions, panel_scroll
        if discard_changes:
            restore_panel_snapshot()
        setting_win_geometry = setting_win.geometry()
        try:
            pw_sash_positions = [pw.sashpos(index) for index in range(2)]
        except tk.TclError:
            pass
        panel_scroll = {
            "check_x": canvas_check.xview()[0],
            "check_y": canvas_check.yview()[0],
            "filter_x": canvas_filter.xview()[0],
            "filter_y": canvas_filter.yview()[0],
            "unit_x": canvas_unit.xview()[0],
            "unit_y": canvas_unit.yview()[0],
        }
        setting_win.destroy()
        setting_win = None

    buttons = ttk.Frame(setting_win)
    buttons.pack(side=tk.BOTTOM, pady=(8, 12))
    ttk.Button(buttons, text="应用筛选并关闭", command=lambda: (apply_filter_sort(), close_panel())).pack(side=tk.LEFT, padx=8)
    ttk.Button(buttons, text="仅关闭", command=lambda: close_panel(True)).pack(side=tk.LEFT, padx=8)

    def restore_panel_layout():
        try:
            if pw_sash_positions:
                for index, position in enumerate(pw_sash_positions):
                    pw.sashpos(index, position)
            for key, canvas in (("check_x", canvas_check), ("check_y", canvas_check), ("filter_x", canvas_filter), ("filter_y", canvas_filter), ("unit_x", canvas_unit), ("unit_y", canvas_unit)):
                if key in panel_scroll:
                    if key.endswith("_x"):
                        canvas.xview_moveto(panel_scroll[key])
                    else:
                        canvas.yview_moveto(panel_scroll[key])
        except tk.TclError:
            pass

    apply_filter_sort()
    setting_win.after(200, restore_panel_layout)


def save_panel_config():
    cfg = read_config()
    cfg["craft_columns"] = {cid: col_var_map[cid].get() for cid in COL_CID_LIST}
    cfg["craft_filter_min"] = {cid: filter_min_var_map[cid].get() for cid in COL_CID_LIST}
    cfg["craft_filter_max"] = {cid: filter_max_var_map[cid].get() for cid in COL_CID_LIST}
    cfg["craft_units"] = {cid: unit_var_map[cid].get() for cid in COL_CID_LIST}
    cfg["craft_filter_sources"] = dict(filter_sources)
    cfg["craft_col_order"] = list(col_order)
    cfg["craft_setting_win_geometry"] = setting_win_geometry
    cfg["craft_pw_sash_positions"] = pw_sash_positions
    cfg["craft_panel_scroll"] = panel_scroll
    cfg["craft_panel_col_widths"] = dict(panel_col_widths)
    cfg["craft_panel_column_order"] = list(panel_column_order)
    cfg["btn_order"] = btn_order
    cfg["shortcut_map"] = dict(shortcut_map)
    cfg["shortcut_global"] = dict(shortcut_global)
    cfg["shortcut_win_geometry"] = shortcut_win_geometry
    cfg["search_win_geometry"] = search_win_geometry
    try:
        write_config(cfg)
        status_var.set("Craft 参数面板配置已保存")
    except Exception as exc:
        status_var.set(f"配置保存失败：{exc}")


def normalize_button_order(value):
    order = list(value) if isinstance(value, list) else []
    order = ["bazaar" if bid == "craft" else bid for bid in order]
    order = [bid for bid in order if bid != "filter"]
    defaults = ["refresh", "refresh_bazaar", "refresh_auction", "param", "save", "load", "reset", "search", "topmost", "shortcut", "bazaar", "forge", "enchant", "api"]
    for bid in defaults:
        if bid not in order:
            if bid == "bazaar":
                shortcut_index = order.index("shortcut") + 1 if "shortcut" in order else len(order)
                order.insert(shortcut_index, bid)
            elif bid == "refresh_bazaar":
                order.insert(order.index("refresh") + 1 if "refresh" in order else len(order), bid)
            elif bid == "refresh_auction":
                order.insert(order.index("refresh_bazaar") + 1 if "refresh_bazaar" in order else len(order), bid)
            elif bid == "param":
                order.insert(order.index("refresh_auction") + 1 if "refresh_auction" in order else len(order), bid)
            elif bid == "search":
                order.insert(order.index("reset") + 1 if "reset" in order else len(order), bid)
            elif bid == "forge":
                forge_index = order.index("bazaar") + 1 if "bazaar" in order else len(order)
                order.insert(forge_index, bid)
            elif bid == "enchant":
                enchant_index = order.index("forge") + 1 if "forge" in order else len(order)
                order.insert(enchant_index, bid)
            else:
                order.append(bid)
    return order


def save_config():
    global tree_scroll_x, tree_scroll_y
    if tree.get_children():
        for cid in col_width_map:
            try:
                col_width_map[cid] = tree.column(cid, "width")
            except tk.TclError:
                pass
    tree_scroll_x, tree_scroll_y = tree.xview()[0], tree.yview()[0]
    cfg = read_config()
    cfg.update({
        "craft_window": {"w": root.winfo_width(), "h": root.winfo_height(), "x": root.winfo_x(), "y": root.winfo_y()},
        "craft_sort": {"key": sort_key, "reverse": sort_reverse},
        "craft_col_order": col_order,
        "craft_btn_order": btn_order,
        "craft_is_topmost": is_topmost,
        "craft_pw_sash_positions": pw_sash_positions,
        "craft_panel_col_widths": dict(panel_col_widths),
        "craft_top_scroll_pos": top_canvas.xview()[0],
        "craft_tree_scroll_x": tree_scroll_x,
        "craft_tree_scroll_y": tree_scroll_y,
        "craft_col_widths": dict(col_width_map),
    })
    cfg["btn_order"] = btn_order
    cfg["shortcut_map"] = dict(shortcut_map)
    cfg["shortcut_global"] = dict(shortcut_global)
    cfg["shortcut_win_geometry"] = shortcut_win_geometry
    cfg["craft_columns"] = {cid: col_var_map[cid].get() for cid in COL_CID_LIST}
    cfg["craft_filter_min"] = {cid: filter_min_var_map[cid].get() for cid in COL_CID_LIST}
    cfg["craft_filter_max"] = {cid: filter_max_var_map[cid].get() for cid in COL_CID_LIST}
    cfg["craft_units"] = {cid: unit_var_map[cid].get() for cid in COL_CID_LIST}
    try:
        write_config(cfg)
        status_var.set("Craft 配置已保存到 craft_config.json")
    except Exception as exc:
        status_var.set(f"配置保存失败：{exc}")


def load_config():
    global sort_key, sort_reverse, col_order, is_topmost, setting_win_geometry, pw_sash_positions, panel_col_widths, panel_column_order, filter_sources
    global panel_scroll, tree_scroll_x, tree_scroll_y, shortcut_win_geometry, search_win_geometry, btn_order
    cfg = read_config()
    window = cfg.get("craft_window")
    if isinstance(window, dict):
        try:
            root.geometry(f"{int(window['w'])}x{int(window['h'])}+{int(window['x'])}+{int(window['y'])}")
        except (KeyError, TypeError, ValueError):
            pass
    sorting = cfg.get("craft_sort", {})
    if sorting.get("key") in COL_CID_LIST:
        sort_key = sorting["key"]
    sort_reverse = bool(sorting.get("reverse", sort_reverse))
    stored_order = cfg.get("craft_col_order", col_order)
    if isinstance(stored_order, list):
        col_order[:] = [cid for cid in stored_order if cid in COL_CID_LIST]
        col_order.extend(cid for cid in COL_CID_LIST if cid not in col_order)
    btn_order[:] = normalize_button_order(cfg.get("btn_order", cfg.get("craft_btn_order", [])))
    shortcut_map.clear()
    shortcut_map.update(cfg.get("shortcut_map", {}))
    shortcut_map.setdefault("search", "CTRL+F")
    shortcut_global.clear()
    shortcut_global.update(cfg.get("shortcut_global", {}))
    shortcut_global.setdefault("search", False)
    shortcut_win_geometry = cfg.get("shortcut_win_geometry") or None
    search_win_geometry = cfg.get("search_win_geometry") or None
    for cid, width in cfg.get("craft_col_widths", {}).items():
        if cid in col_width_map and isinstance(width, (int, float)):
            col_width_map[cid] = width
    setting_win_geometry = cfg.get("craft_setting_win_geometry") or None
    pw_sash_positions = cfg.get("craft_pw_sash_positions") or None
    if isinstance(cfg.get("craft_panel_col_widths"), dict):
        for key, width in cfg["craft_panel_col_widths"].items():
            if key in panel_col_widths and isinstance(width, (int, float)):
                panel_col_widths[key] = width
    if isinstance(cfg.get("craft_panel_column_order"), list):
        panel_column_order[:] = [key for key in cfg["craft_panel_column_order"] if key in panel_col_widths]
        panel_column_order.extend(key for key in panel_col_widths if key not in panel_column_order)
    panel_scroll = cfg.get("craft_panel_scroll") or {"x": 0, "y": 0}
    tree_scroll_x = cfg.get("craft_tree_scroll_x", 0)
    tree_scroll_y = cfg.get("craft_tree_scroll_y", 0)
    columns = cfg.get("craft_columns", {})
    minimums = cfg.get("craft_filter_min", {})
    maximums = cfg.get("craft_filter_max", {})
    units = cfg.get("craft_units", {})
    stored_sources = cfg.get("craft_filter_sources", cfg.get("filter_sources", {}))
    if isinstance(stored_sources, dict):
        for source in filter_sources:
            if source in stored_sources:
                filter_sources[source] = bool(stored_sources[source])
    for cid in COL_CID_LIST:
        if cid in columns:
            col_var_map[cid].set(bool(columns[cid]))
        if cid in minimums:
            filter_min_var_map[cid].set(str(minimums[cid]))
        if cid in maximums:
            filter_max_var_map[cid].set(str(maximums[cid]))
        if units.get(cid) in UNIT_SCALE:
            unit_var_map[cid].set(units[cid])
    is_topmost = bool(cfg.get("craft_is_topmost", False))
    root.attributes("-topmost", is_topmost)
    apply_shortcuts()
    rebuild_button_bar()
    top_scroll_pos = cfg.get("craft_top_scroll_pos", 0)
    saved_x, saved_y = tree_scroll_x, tree_scroll_y

    def restore_scroll_positions():
        try:
            top_canvas.xview_moveto(top_scroll_pos)
            tree.xview_moveto(saved_x)
            tree.yview_moveto(saved_y)
        except tk.TclError:
            pass

    root.after(200, restore_scroll_positions)
    apply_filter_sort(save_current_widths=False)


def reset_all_default():
    global sort_key, sort_reverse, is_topmost, col_order, setting_win_geometry, pw_sash_positions, panel_scroll, panel_col_widths, panel_column_order, filter_sources, shortcut_win_geometry, search_win_geometry, search_query
    sort_key, sort_reverse = "sell_mat_sell", True
    filter_sources = {"bazaar": True, "auction": True}
    is_topmost = False
    shortcut_map.clear()
    shortcut_map["search"] = "CTRL+F"
    shortcut_global.clear()
    shortcut_global["search"] = False
    search_query = ""
    shortcut_win_geometry = None
    search_win_geometry = None
    col_order[:] = list(COL_CID_LIST)
    setting_win_geometry = None
    pw_sash_positions = None
    panel_scroll = {}
    panel_col_widths = {"check": 150, "field": 220, "min": 130, "max": 130, "unit": 100}
    panel_column_order[:] = ["check", "field", "min", "max", "unit"]
    for meta in COL_META:
        cid = meta["cid"]
        col_var_map[cid].set(True)
        filter_min_var_map[cid].set("")
        filter_max_var_map[cid].set("")
        unit_var_map[cid].set("默认")
        col_width_map[cid] = DEFAULT_WIDTHS[cid]
    root.attributes("-topmost", False)
    apply_shortcuts()
    apply_filter_sort(save_current_widths=False)
    rebuild_button_bar()
    status_var.set("已重置 Craft 设置为默认")


def toggle_topmost():
    global is_topmost
    is_topmost = not is_topmost
    root.attributes("-topmost", is_topmost)
    find_topmost_button().config(text="取消置顶" if is_topmost else "窗口置顶")
    if is_topmost:
        root.lift()


def open_bazaar():
    try:
        command = [sys.executable, "--page", "bazaar"] if getattr(sys, "frozen", False) else [sys.executable, os.path.join(SOURCE_APP_DIR, "bazaar.py")]
        subprocess.Popen(command, cwd=APP_DIR)
        root.destroy()
    except Exception as exc:
        status_var.set(f"打开 Bazaar 失败：{exc}")


def open_forge():
    try:
        command = [sys.executable, "--page", "forge"] if getattr(sys, "frozen", False) else [sys.executable, os.path.join(SOURCE_APP_DIR, "forge.py")]
        subprocess.Popen(command, cwd=APP_DIR)
        root.destroy()
    except Exception as exc:
        status_var.set(f"打开 Forge 失败：{exc}")


def open_enchant():
    try:
        command = [sys.executable, "--page", "enchant"] if getattr(sys, "frozen", False) else [sys.executable, os.path.join(SOURCE_APP_DIR, "enchant.py")]
        subprocess.Popen(command, cwd=APP_DIR)
        root.destroy()
    except Exception as exc:
        status_var.set(f"打开 Enchant 失败：{exc}")


# 顶部所有按钮都可以设置快捷键。
SHORTCUT_ELIGIBLE = [
    "refresh", "refresh_bazaar", "refresh_auction", "param", "save", "load",
    "reset", "search", "topmost", "shortcut", "bazaar", "forge", "enchant", "api",
]


def shortcut_dialog_order():
    """按当前顶部按钮顺序显示快捷键项。"""
    return [bid for bid in btn_order if bid in SHORTCUT_ELIGIBLE and bid in _btn_defs]
MODIFIER_KEYSYMS = {"SHIFT_L", "SHIFT_R", "CONTROL_L", "CONTROL_R", "ALT_L", "ALT_R"}
VK_MAP = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "SPACE": 0x20, "ESCAPE": 0x1B, "RETURN": 0x0D, "TAB": 0x09, "BACKSPACE": 0x08,
    "DELETE": 0x2E, "INSERT": 0x2D, "HOME": 0x24, "END": 0x23, "PAGE_UP": 0x21,
    "PAGE_DOWN": 0x22, "UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
}


def shortcut_to_tk(value):
    if not value:
        return None
    parts = [part.strip() for part in value.split("+")]
    key = parts[-1]
    modifiers = parts[:-1]
    if any(mod.upper() not in {"CTRL", "ALT", "SHIFT"} for mod in modifiers):
        return None
    modifier_text = "".join({"CTRL": "Control-", "ALT": "Alt-", "SHIFT": "Shift-"}[mod.upper()] for mod in modifiers)
    key_map = {"SPACE": "space", "ESCAPE": "Escape", "RETURN": "Return", "TAB": "Tab", "BACKSPACE": "BackSpace", "PAGE_UP": "Prior", "PAGE_DOWN": "Next"}
    key = key_map.get(key.upper(), key.lower() if len(key) == 1 else key)
    return f"<{modifier_text}{key}>"


def shortcut_to_win32(value):
    if not value:
        return None
    parts = [part.strip().upper() for part in value.split("+")]
    key = parts[-1]
    modifiers = parts[:-1]
    mod = 0x4000
    for modifier in modifiers:
        if modifier == "CTRL":
            mod |= 0x0002
        elif modifier == "ALT":
            mod |= 0x0001
        elif modifier == "SHIFT":
            mod |= 0x0004
        else:
            return None
    if key in VK_MAP:
        vk = VK_MAP[key]
    elif len(key) == 1 and (key.isalpha() or key.isdigit()):
        vk = ord(key)
    else:
        return None
    return mod, vk


def shortcut_commands():
    return {
        "refresh": refresh_table,
        "refresh_bazaar": refresh_bazaar_data,
        "refresh_auction": refresh_auction_data,
        "param": open_param_panel,
        "save": save_config,
        "load": load_config,
        "reset": reset_all_default,
        "search": open_search_dialog,
        "topmost": toggle_topmost,
        "shortcut": open_shortcut_dialog,
        "bazaar": open_bazaar,
        "forge": open_forge,
        "enchant": open_enchant,
        "api": open_api_dialog,
    }


def stop_global_hotkeys():
    global _global_hotkey_thread
    _global_hotkey_stop.set()
    if _global_hotkey_thread and _global_hotkey_thread.is_alive():
        _global_hotkey_thread.join(timeout=1)
    _global_hotkey_thread = None


def global_hotkey_worker(hotkeys):
    registered = {}
    for bid, (mod, vk) in hotkeys.items():
        hotkey_id = hash(bid) & 0x7FFFFFFF
        if ctypes.windll.user32.RegisterHotKey(None, hotkey_id, mod, vk):
            registered[bid] = hotkey_id
    if not registered:
        return
    message = ctypes.wintypes.MSG()
    while not _global_hotkey_stop.is_set():
        if ctypes.windll.user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
            if message.message == 0x0312:
                for bid, hotkey_id in registered.items():
                    if message.wParam == hotkey_id:
                        root.after(0, shortcut_commands()[bid])
                        break
        else:
            _global_hotkey_stop.wait(0.05)
    for hotkey_id in registered.values():
        try:
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
        except Exception:
            pass


def register_global_hotkeys():
    global _global_hotkey_thread
    stop_global_hotkeys()
    _global_hotkey_stop.clear()
    hotkeys = {}
    for bid in SHORTCUT_ELIGIBLE:
        if shortcut_global.get(bid) and shortcut_map.get(bid):
            converted = shortcut_to_win32(shortcut_map[bid])
            if converted:
                hotkeys[bid] = converted
    if hotkeys:
        _global_hotkey_thread = threading.Thread(target=global_hotkey_worker, args=(hotkeys,), daemon=True)
        _global_hotkey_thread.start()


def on_combo_press(event):
    if not _combo_bindings:
        return
    key = event.keysym.upper()
    if key in MODIFIER_KEYSYMS:
        return
    if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text)):
        return
    _held_keys.add(key)
    for _bid, (prefix, final, command) in _combo_bindings.items():
        if key == final and prefix.issubset(_held_keys):
            command()
            break


def on_combo_release(event):
    _held_keys.discard(event.keysym.upper())


def apply_shortcuts():
    global _prev_shortcut_map, _combo_listeners_bound
    commands = shortcut_commands()
    for _bid, old_value in _prev_shortcut_map.items():
        sequence = shortcut_to_tk(old_value)
        if sequence:
            try:
                root.unbind_all(sequence)
            except tk.TclError:
                pass
    _combo_bindings.clear()
    input_widgets = (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text)
    for bid in SHORTCUT_ELIGIBLE:
        value = shortcut_map.get(bid, "")
        if not value or shortcut_global.get(bid):
            continue
        sequence = shortcut_to_tk(value)
        command = commands[bid]
        if sequence:
            def handler(event, cmd=command):
                if not isinstance(event.widget, input_widgets):
                    cmd()
            root.bind_all(sequence, handler)
        else:
            parts = [part.strip().upper() for part in value.split("+")]
            if len(parts) > 1:
                _combo_bindings[bid] = (set(parts[:-1]), parts[-1], command)
    if _combo_bindings and not _combo_listeners_bound:
        root.bind_all("<KeyPress>", on_combo_press, add="+")
        root.bind_all("<KeyRelease>", on_combo_release, add="+")
        _combo_listeners_bound = True
    _prev_shortcut_map = dict(shortcut_map)
    register_global_hotkeys()


def _open_key_input_window(parent_dlg, bid, editing, row_labels):
    """Capture shortcuts with explicit modifier tracking for Windows."""
    sub = tk.Toplevel(parent_dlg)
    btn_name = _btn_defs.get(bid, ("?",))[0]
    sub.title(f"设置快捷键 — {btn_name}")
    sub.resizable(False, False)
    sub.attributes("-topmost", True)
    sub.transient(parent_dlg)
    captured = [None]
    mod_state = {"shift": False, "ctrl": False, "alt": False}
    held_non_mod = [None]

    frame = tk.Frame(sub, padx=20, pady=15)
    frame.pack()
    tk.Label(frame, text=f'请按下组合键作为 "{btn_name}" 的快捷键', font=("", 11)).pack(pady=(0, 5))
    tk.Label(frame, text="(支持 单键 / 修饰键+键 / 字母+字母，如 V+B)", font=("", 9), fg="#888").pack(pady=(0, 5))
    tk.Label(frame, text="⚠ 非修饰键组合（如 V+B）仅局部生效，全局快捷键无效", font=("", 9), fg="#E53935").pack(pady=(0, 10))
    display_lbl = tk.Label(frame, text="", font=("", 18, "bold"), fg="#2196F3", width=25, relief="sunken", bg="#fff", anchor="center")
    display_lbl.pack(pady=(0, 15))
    warn_lbl = tk.Label(frame, text="", font=("", 9), fg="#E53935")
    warn_lbl.pack(pady=(0, 5))
    tk.Label(frame, text="按 ESC 可清空快捷键", font=("", 9), fg="#999").pack()
    modifier_keys = {"SHIFT_L", "SHIFT_R", "CONTROL_L", "CONTROL_R", "ALT_L", "ALT_R"}

    def on_key_press(event):
        key = event.keysym.upper()
        if key in ("SHIFT_L", "SHIFT_R"):
            mod_state["shift"] = True
        elif key in ("CONTROL_L", "CONTROL_R"):
            mod_state["ctrl"] = True
        elif key in ("ALT_L", "ALT_R"):
            mod_state["alt"] = True
        if key in modifier_keys:
            return
        if key == "ESCAPE":
            captured[0] = "ESCAPE"
            display_lbl.config(text="ESCAPE", fg="#4CAF50")
            return
        if held_non_mod[0] and held_non_mod[0] != key:
            parts = []
            if mod_state["shift"]:
                parts.append("SHIFT")
            if mod_state["ctrl"]:
                parts.append("CTRL")
            if mod_state["alt"]:
                parts.append("ALT")
            parts.extend((held_non_mod[0], key))
            captured[0] = "+".join(parts)
            display_lbl.config(text=captured[0], fg="#4CAF50")
            warn_lbl.config(text="⚠ 此组合仅局部生效，不可全局")
            return
        held_non_mod[0] = key
        parts = []
        if mod_state["shift"]:
            parts.append("SHIFT")
        if mod_state["ctrl"]:
            parts.append("CTRL")
        if mod_state["alt"]:
            parts.append("ALT")
        parts.append(key)
        captured[0] = "+".join(parts)
        display_lbl.config(text=captured[0], fg="#4CAF50")
        if len(parts) <= 2:
            warn_lbl.config(text="")

    def on_key_release(event):
        key = event.keysym.upper()
        if key in ("SHIFT_L", "SHIFT_R"):
            mod_state["shift"] = False
        elif key in ("CONTROL_L", "CONTROL_R"):
            mod_state["ctrl"] = False
        elif key in ("ALT_L", "ALT_R"):
            mod_state["alt"] = False
        if held_non_mod[0] == key:
            held_non_mod[0] = None

    sub.bind("<KeyPress>", on_key_press)
    sub.bind("<KeyRelease>", on_key_release)
    sub.focus_force()

    def confirm():
        if captured[0] is not None:
            value = "" if captured[0] == "ESCAPE" else captured[0]
            editing[bid] = value
            row_labels[bid].config(text=value, bg="#f0f0f0")
        sub.destroy()

    buttons = tk.Frame(sub)
    buttons.pack(pady=(10, 10))
    tk.Button(buttons, text="确认", command=confirm, width=10, font=("", 11)).pack(side=tk.LEFT, padx=6)
    tk.Button(buttons, text="取消", command=sub.destroy, width=10, font=("", 11)).pack(side=tk.LEFT, padx=6)
    parent_dlg.update_idletasks()
    sub.update_idletasks()
    x = parent_dlg.winfo_x() + (parent_dlg.winfo_width() - sub.winfo_width()) // 2
    y = parent_dlg.winfo_y() + (parent_dlg.winfo_height() - sub.winfo_height()) // 2
    sub.geometry(f"+{x}+{y}")


def open_shortcut_dialog():
    global shortcut_win_geometry
    dialog = tk.Toplevel(root)
    dialog.title("快捷键设置")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)
    dialog.transient(root)
    dialog.grab_set()
    editing = dict(shortcut_map)
    editing_global = dict(shortcut_global)
    frame = tk.Frame(dialog, padx=15, pady=15)
    frame.pack()
    tk.Label(frame, text='点击快捷键列设置快捷键，勾选“全局”后窗口外也生效', fg="#666").grid(row=0, column=0, columnspan=3, pady=(0, 10))
    tk.Label(frame, text="按钮名称", width=20).grid(row=1, column=0)
    tk.Label(frame, text="快捷键", width=20).grid(row=1, column=1)
    tk.Label(frame, text="全局", width=6).grid(row=1, column=2)
    labels, global_vars = {}, {}
    for index, bid in enumerate(shortcut_dialog_order(), 2):
        tk.Label(frame, text=_btn_defs[bid][0], width=20, anchor="w").grid(row=index, column=0, sticky="w", padx=5, pady=3)
        label = tk.Label(frame, text=editing.get(bid, ""), width=20, relief="groove", bg="#f0f0f0")
        label.grid(row=index, column=1, padx=5, pady=3)
        labels[bid] = label
        variable = tk.BooleanVar(value=editing_global.get(bid, False))
        global_vars[bid] = variable
        tk.Checkbutton(frame, variable=variable).grid(row=index, column=2)

        def capture(_event, selected=bid):
            _open_key_input_window(dialog, selected, editing, labels)

        label.bind("<Button-1>", capture)
    buttons = tk.Frame(dialog)
    buttons.pack(pady=10)

    def reset_shortcuts():
        editing.clear()
        editing_global.clear()
        for bid in SHORTCUT_ELIGIBLE:
            editing[bid] = ""
            editing_global[bid] = False
            global_vars[bid].set(False)
            labels[bid].config(text="")

    def confirm_all():
        global shortcut_win_geometry
        shortcut_map.clear()
        shortcut_map.update(editing)
        shortcut_global.clear()
        for bid in SHORTCUT_ELIGIBLE:
            shortcut_global[bid] = bool(global_vars[bid].get() and shortcut_to_win32(editing.get(bid, "")))
        apply_shortcuts()
        shortcut_win_geometry = dialog.geometry()
        dialog.destroy()

    ttk.Button(buttons, text="确定", command=confirm_all).pack(side=tk.LEFT, padx=8)
    ttk.Button(buttons, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=8)
    ttk.Button(buttons, text="重置全部", command=reset_shortcuts).pack(side=tk.LEFT, padx=8)
    if shortcut_win_geometry:
        dialog.geometry(shortcut_win_geometry)


def move_button(delta):
    bid = button_menu_bid[0]
    if bid not in btn_order:
        return
    index = btn_order.index(bid)
    target = index + delta
    if 0 <= target < len(btn_order):
        btn_order[index], btn_order[target] = btn_order[target], btn_order[index]
        rebuild_button_bar()


button_menu_bid = [None]


def on_button_right_click(event, bid):
    button_menu_bid[0] = bid
    button_right_menu.tk_popup(event.x_root, event.y_root)


def rebuild_button_bar():
    for widget in top_frame.winfo_children():
        widget.destroy()
    for bid in btn_order:
        if bid not in _btn_defs:
            continue
        label, command = _btn_defs[bid]
        button = tk.Button(top_frame, text=label, command=command, font=("", 11))
        button.pack(side=tk.LEFT, padx=6)
        button.bind("<Button-3>", lambda event, selected=bid: on_button_right_click(event, selected))
    tk.Label(top_frame, textvariable=status_var, fg="#333").pack(side=tk.LEFT, padx=30)


def find_topmost_button():
    for widget in top_frame.winfo_children():
        if isinstance(widget, tk.Button) and "置顶" in widget.cget("text"):
            return widget
    return tk.Button(top_frame, text="窗口置顶")


def open_param_panel():
    """打开统一滚动、可拖动调整列宽的 Craft 参数面板。"""
    global setting_win, setting_win_geometry, panel_scroll, panel_col_widths
    if setting_win and setting_win.winfo_exists():
        setting_win.lift()
        return
    setting_win = tk.Toplevel(root)
    setting_win.title("Craft 参数设置")
    setting_win.geometry(setting_win_geometry or "1100x750")
    setting_win.transient(root)
    setting_win.grab_set()

    snapshot = {
        "columns": {cid: col_var_map[cid].get() for cid in COL_CID_LIST},
        "filter_min": {cid: filter_min_var_map[cid].get() for cid in COL_CID_LIST},
        "filter_max": {cid: filter_max_var_map[cid].get() for cid in COL_CID_LIST},
        "units": {cid: unit_var_map[cid].get() for cid in COL_CID_LIST},
    }
    columns = ["check", "field", "min", "max", "unit"]
    headers = ["显示", "字段", "最低值", "最高值", "单位"]
    body = ttk.Frame(setting_win)
    body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    # 使用原生 Treeview 表头，列分隔线拖拽方式与主界面一致。
    header = ttk.Treeview(body, columns=columns, show="headings", height=1, selectmode="none")
    header.pack(side=tk.TOP, fill=tk.X)
    content = ttk.Frame(body)
    content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    canvas = tk.Canvas(content, highlightthickness=0)
    scroll_y = ttk.Scrollbar(content, orient=tk.VERTICAL, command=canvas.yview)
    scroll_x = ttk.Scrollbar(content, orient=tk.HORIZONTAL)
    inner = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll_y.set)
    inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def shared_xscroll(*args):
        canvas.xview(*args)
        header.xview(*args)

    def set_shared_xscroll(first, last):
        scroll_x.set(first, last)

    scroll_x.configure(command=shared_xscroll)
    canvas.configure(xscrollcommand=set_shared_xscroll)

    def apply_column_widths():
        try:
            if not inner.winfo_exists():
                return
        except tk.TclError:
            return
        for index, key in enumerate(columns):
            inner.columnconfigure(index, minsize=int(panel_col_widths[key]), weight=0)

    for key, title in zip(columns, headers):
        header.heading(key, text=title)
        header.column(key, width=int(panel_col_widths[key]), minwidth=70, stretch=False, anchor="w")

    resize_sync = {"pending": False}

    def sync_header_widths(_event=None):
        resize_sync["pending"] = False
        try:
            if not header.winfo_exists() or not inner.winfo_exists():
                return
            for key in columns:
                panel_col_widths[key] = max(70, int(header.column(key, "width")))
            apply_column_widths()
            canvas.configure(scrollregion=canvas.bbox("all"))
        except tk.TclError:
            pass

    def schedule_header_sync(_event=None):
        if resize_sync["pending"]:
            return
        resize_sync["pending"] = True
        try:
            setting_win.after_idle(sync_header_widths)
        except tk.TclError:
            resize_sync["pending"] = False

    header.bind("<B1-Motion>", schedule_header_sync)
    header.bind("<ButtonRelease-1>", sync_header_widths)

    for index, meta in enumerate(COL_META, 1):
        cid = meta["cid"]
        ttk.Checkbutton(inner, variable=col_var_map[cid], command=lambda: apply_filter_sort(save_current_widths=False)).grid(row=index, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(inner, text=meta["name"], anchor="w").grid(row=index, column=1, sticky="w", padx=5, pady=5)
        if meta["is_num"]:
            ttk.Entry(inner, textvariable=filter_min_var_map[cid]).grid(row=index, column=2, sticky="ew", padx=5, pady=5)
            ttk.Entry(inner, textvariable=filter_max_var_map[cid]).grid(row=index, column=3, sticky="ew", padx=5, pady=5)
            ttk.Combobox(inner, values=list(UNIT_SCALE), state="readonly", textvariable=unit_var_map[cid]).grid(row=index, column=4, sticky="ew", padx=5, pady=5)
        else:
            ttk.Label(inner, text="不支持筛选", foreground="#888").grid(row=index, column=2, columnspan=2, sticky="w", padx=5, pady=5)
            ttk.Label(inner, text="—", foreground="#888").grid(row=index, column=4, sticky="w", padx=5, pady=5)
    apply_column_widths()

    def restore_snapshot():
        for cid in COL_CID_LIST:
            col_var_map[cid].set(snapshot["columns"][cid])
            filter_min_var_map[cid].set(snapshot["filter_min"][cid])
            filter_max_var_map[cid].set(snapshot["filter_max"][cid])
            unit_var_map[cid].set(snapshot["units"][cid])
        apply_filter_sort(save_current_widths=False)

    def close_panel(discard=False):
        global setting_win, setting_win_geometry, panel_scroll
        if discard:
            restore_snapshot()
        sync_header_widths()
        setting_win_geometry = setting_win.geometry()
        panel_scroll = {"x": canvas.xview()[0], "y": canvas.yview()[0]}
        setting_win.destroy()
        setting_win = None

    buttons = ttk.Frame(setting_win)
    buttons.pack(side=tk.BOTTOM, pady=(8, 12))
    ttk.Button(buttons, text="应用筛选并关闭", command=lambda: (apply_filter_sort(), close_panel())).pack(side=tk.LEFT, padx=8)
    ttk.Button(buttons, text="仅关闭", command=lambda: close_panel(True)).pack(side=tk.LEFT, padx=8)
    apply_filter_sort(save_current_widths=False)
    def restore_panel_scroll():
        try:
            x_pos = panel_scroll.get("x", 0)
            y_pos = panel_scroll.get("y", 0)
            canvas.xview_moveto(x_pos)
            header.xview_moveto(x_pos)
            canvas.yview_moveto(y_pos)
        except tk.TclError:
            pass
    root.after(200, restore_panel_scroll)


# 主表格表头右键列重排，与参数面板共用 col_order。
craft_header_menu_cid = [None]


def craft_move_col(delta):
    cid = craft_header_menu_cid[0]
    if cid not in col_order:
        return
    index = col_order.index(cid)
    target = index + delta
    if 0 <= target < len(col_order):
        col_order[index], col_order[target] = col_order[target], col_order[index]
        apply_filter_sort()


def copy_item_id(event_y):
    row = tree.identify_row(event_y)
    if not row:
        return
    visible = get_visible_cols()
    if "name" not in visible:
        return
    name_index = visible.index("name")
    values = tree.item(row).get("values", [])
    if name_index >= len(values):
        return
    item_id = str(values[name_index]).replace("_", " ")
    tree.selection_set(row)
    root.clipboard_clear()
    root.clipboard_append(item_id)
    status_var.set(f"已复制: {item_id}")


def craft_show_right_menu(event):
    if tree.identify_region(event.x, event.y) == "heading":
        column = tree.identify_column(event.x)
        index = int(column[1:]) - 1
        visible = get_visible_cols()
        if 0 <= index < len(visible):
            craft_header_menu_cid[0] = visible[index]
            header_right_menu.tk_popup(event.x_root, event.y_root)
        return
    copy_item_id(event.y)


# 恢复为统一 Canvas 参数面板：普通表头拖动调整列宽，控件外观保持原样。
def open_param_panel():
    global setting_win, setting_win_geometry, panel_scroll, panel_col_widths, col_order, panel_column_order, filter_sources
    if setting_win and setting_win.winfo_exists():
        setting_win.lift()
        return
    setting_win = tk.Toplevel(root)
    setting_win.title("Craft 参数设置")
    setting_win.geometry(setting_win_geometry or "1100x750")
    setting_win.transient(root)
    setting_win.grab_set()

    panel_order = list(col_order)
    columns = list(panel_column_order)
    snapshot = {
        "order": list(panel_order),
        "panel_columns": list(columns),
        "columns": {cid: col_var_map[cid].get() for cid in COL_CID_LIST},
        "filter_min": {cid: filter_min_var_map[cid].get() for cid in COL_CID_LIST},
        "filter_max": {cid: filter_max_var_map[cid].get() for cid in COL_CID_LIST},
        "units": {cid: unit_var_map[cid].get() for cid in COL_CID_LIST},
        "filter_sources": dict(filter_sources),
    }
    body = ttk.Frame(setting_win)
    body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
    canvas = tk.Canvas(body)
    scroll_y = ttk.Scrollbar(body, orient=tk.VERTICAL, command=canvas.yview)
    scroll_x = ttk.Scrollbar(body, orient=tk.HORIZONTAL, command=canvas.xview)
    inner = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    header_names = {"check": "显示", "field": "字段", "min": "最低值", "max": "最高值", "unit": "单位"}
    resize_state = {"key": None, "start_x": 0, "start_width": 0}

    def apply_column_widths():
        try:
            if not inner.winfo_exists():
                return
        except tk.TclError:
            return
        for index, key in enumerate(columns):
            inner.columnconfigure(index, minsize=int(panel_col_widths[key]), weight=0)

    def start_resize(event, key):
        resize_state.update(key=key, start_x=event.x_root, start_width=panel_col_widths[key])
        root.bind_all("<B1-Motion>", resize_column)
        root.bind_all("<ButtonRelease-1>", stop_resize)

    def resize_column(event):
        key = resize_state["key"]
        if key is None:
            return
        panel_col_widths[key] = max(70, resize_state["start_width"] + event.x_root - resize_state["start_x"])
        apply_column_widths()

    def stop_resize(_event):
        resize_state["key"] = None
        root.unbind_all("<B1-Motion>")
        root.unbind_all("<ButtonRelease-1>")

    header_widgets = {}
    selected_panel_column = [None]
    column_menu = tk.Menu(setting_win, tearoff=0)

    def regrid_panel():
        for index, key in enumerate(columns):
            header_widgets[key].grid_configure(row=0, column=index)
        for row, row_cid in enumerate(panel_order, 1):
            for widget, key, columnspan in row_widgets[row_cid]:
                widget.grid_configure(row=row, column=columns.index(key), columnspan=columnspan)
        apply_column_widths()

    def move_panel_column(delta):
        key = selected_panel_column[0]
        if key not in columns:
            return
        index = columns.index(key)
        target = index + delta
        if 0 <= target < len(columns):
            columns[index], columns[target] = columns[target], columns[index]
            panel_column_order[:] = columns
            regrid_panel()

    column_menu.add_command(label="← 左移此列", command=lambda: move_panel_column(-1))
    column_menu.add_command(label="→ 右移此列", command=lambda: move_panel_column(1))

    def show_panel_column_menu(event, key):
        selected_panel_column[0] = key
        index = columns.index(key)
        column_menu.entryconfigure(0, state=tk.NORMAL if index > 0 else tk.DISABLED)
        column_menu.entryconfigure(1, state=tk.NORMAL if index < len(columns) - 1 else tk.DISABLED)
        column_menu.tk_popup(event.x_root, event.y_root)

    row_widgets = {}
    selected_row = [None]
    row_menu = tk.Menu(setting_win, tearoff=0)

    def move_row(delta):
        cid = selected_row[0]
        if cid not in panel_order:
            return
        old_index = panel_order.index(cid)
        new_index = old_index + delta
        if not 0 <= new_index < len(panel_order):
            return
        panel_order[old_index], panel_order[new_index] = panel_order[new_index], panel_order[old_index]
        col_order[:] = panel_order
        regrid_panel()
        # 和 Forge 一样立即刷新主表，移动后无需点击“应用筛选并关闭”。
        try:
            apply_filter_sort(save_current_widths=False)
            root.update_idletasks()
        except tk.TclError:
            pass

    row_menu.add_command(label="↑ 上移", command=lambda: move_row(-1))
    row_menu.add_command(label="↓ 下移", command=lambda: move_row(1))

    def show_row_menu(event, cid):
        selected_row[0] = cid
        index = panel_order.index(cid)
        row_menu.entryconfigure(0, state=tk.NORMAL if index > 0 else tk.DISABLED)
        row_menu.entryconfigure(1, state=tk.NORMAL if index < len(panel_order) - 1 else tk.DISABLED)
        row_menu.tk_popup(event.x_root, event.y_root)

    def bind_row_menu(widget, cid):
        widget.bind("<Button-3>", lambda event, selected=cid: show_row_menu(event, selected), add="+")

    meta_by_cid = {meta["cid"]: meta for meta in COL_META}
    for index, key in enumerate(columns):
        header = tk.Label(inner, text=header_names[key], anchor="w", relief="raised", cursor="sb_h_double_arrow")
        header.grid(row=0, column=index, sticky="ew", padx=1, pady=(1, 5))
        header.bind("<ButtonPress-1>", lambda event, selected=key: start_resize(event, selected))
        header.bind("<Button-3>", lambda event, selected=key: show_panel_column_menu(event, selected), add="+")
        header_widgets[key] = header

    for index, cid in enumerate(panel_order, 1):
        meta = meta_by_cid[cid]
        row_widgets[cid] = []
        check = ttk.Checkbutton(inner, variable=col_var_map[cid], command=lambda: apply_filter_sort(save_current_widths=False))
        check.grid(row=index, column=columns.index("check"), sticky="w", padx=5, pady=5)
        row_widgets[cid].append((check, "check", 1))
        field = ttk.Label(inner, text=meta["name"], anchor="w")
        field.grid(row=index, column=columns.index("field"), sticky="w", padx=5, pady=5)
        row_widgets[cid].append((field, "field", 1))
        if meta["is_num"]:
            minimum = ttk.Entry(inner, textvariable=filter_min_var_map[cid])
            minimum.grid(row=index, column=columns.index("min"), sticky="ew", padx=5, pady=5)
            maximum = ttk.Entry(inner, textvariable=filter_max_var_map[cid])
            maximum.grid(row=index, column=columns.index("max"), sticky="ew", padx=5, pady=5)
            unit = ttk.Combobox(inner, values=list(UNIT_SCALE), state="readonly", textvariable=unit_var_map[cid])
            unit.grid(row=index, column=columns.index("unit"), sticky="ew", padx=5, pady=5)
            row_widgets[cid].extend(((minimum, "min", 1), (maximum, "max", 1), (unit, "unit", 1)))
        else:
            unsupported = ttk.Label(inner, text="不支持筛选", foreground="#888")
            unsupported.grid(row=index, column=columns.index("min"), sticky="w", padx=5, pady=5)
            dash = ttk.Label(inner, text="—", foreground="#888")
            dash.grid(row=index, column=columns.index("unit"), sticky="w", padx=5, pady=5)
            row_widgets[cid].extend(((unsupported, "min", 1), (dash, "unit", 1)))
        for widget, _column, _columnspan in row_widgets[cid]:
            bind_row_menu(widget, cid)
    apply_column_widths()

    source_vars = {
        source: tk.BooleanVar(value=filter_sources.get(source, True))
        for source in ("bazaar", "auction")
    }

    def commit_sources():
        for source, variable in source_vars.items():
            filter_sources[source] = bool(variable.get())

    def refresh_from_source_toggle():
        commit_sources()
        apply_filter_sort(save_current_widths=False)

    live_traces = []
    for cid in COL_CID_LIST:
        for variable in (filter_min_var_map[cid], filter_max_var_map[cid], unit_var_map[cid]):
            trace_id = variable.trace_add("write", lambda *_args: apply_filter_sort(save_current_widths=False))
            live_traces.append((variable, trace_id))

    def restore_snapshot():
        panel_order[:] = snapshot["order"]
        columns[:] = snapshot["panel_columns"]
        panel_column_order[:] = columns
        regrid_panel()
        col_order[:] = panel_order
        for cid in COL_CID_LIST:
            col_var_map[cid].set(snapshot["columns"][cid])
            filter_min_var_map[cid].set(snapshot["filter_min"][cid])
            filter_max_var_map[cid].set(snapshot["filter_max"][cid])
            unit_var_map[cid].set(snapshot["units"][cid])
        filter_sources.update(snapshot["filter_sources"])
        for source, variable in source_vars.items():
            variable.set(filter_sources[source])
        apply_filter_sort(save_current_widths=False)

    def remove_live_traces():
        """Remove listeners before restoring panel values in bulk."""
        for variable, trace_id in live_traces:
            try:
                variable.trace_remove("write", trace_id)
            except tk.TclError:
                pass
        live_traces.clear()

    def close_panel(discard=False):
        global setting_win, setting_win_geometry, panel_scroll
        # Without this, every restored StringVar triggers a full table rebuild.
        remove_live_traces()
        if discard:
            restore_snapshot()
        stop_resize(None)
        setting_win_geometry = setting_win.geometry()
        panel_scroll = {"x": canvas.xview()[0], "y": canvas.yview()[0]}
        setting_win.destroy()
        setting_win = None

    source_frame = ttk.Frame(setting_win)
    source_frame.pack(side=tk.BOTTOM, pady=(4, 0))
    ttk.Label(source_frame, text="筛选数据源：").pack(side=tk.LEFT, padx=(0, 8))
    ttk.Checkbutton(source_frame, text="Bazaar", variable=source_vars["bazaar"], command=refresh_from_source_toggle).pack(side=tk.LEFT, padx=8)
    ttk.Checkbutton(source_frame, text="Auction House", variable=source_vars["auction"], command=refresh_from_source_toggle).pack(side=tk.LEFT, padx=8)
    buttons = ttk.Frame(setting_win)
    buttons.pack(side=tk.BOTTOM, pady=(8, 12))
    ttk.Button(buttons, text="应用筛选并关闭", command=lambda: (commit_sources(), apply_filter_sort(), close_panel())).pack(side=tk.LEFT, padx=8)
    ttk.Button(buttons, text="仅关闭", command=lambda: close_panel(True)).pack(side=tk.LEFT, padx=8)
    apply_filter_sort(save_current_widths=False)
    root.after(200, lambda: (canvas.xview_moveto(panel_scroll.get("x", 0)), canvas.yview_moveto(panel_scroll.get("y", 0))))


# 使用独立市场进程，切换界面时 BZ/AH 请求不会被原窗口中断。
def _load_cached_auction_index():
    path = os.path.join(APP_DIR, "auction_data.json")
    try:
        with open(path, "r", encoding="utf-8") as file:
            value = json.load(file)
        auctions = value.get("auctions", []) if isinstance(value, dict) else value
        return build_bin_index(auctions if isinstance(auctions, list) else [])
    except Exception:
        return {}


def _poll_market_result(source):
    status = read_status()
    if status.get("state") in {"queued", "running"}:
        root.after(500, lambda: _poll_market_result(source))
        return
    global item_data_cache, auction_index
    if source in {"bazaar", "all"}:
        cached = load_cached_data()
        if cached:
            item_data_cache = cached
    if source in {"auction", "all"}:
        auction_index = _load_cached_auction_index()
    if item_data_cache:
        apply_filter_sort(save_current_widths=False)
    status_var.set(status.get("message") or "市场数据请求完成")


def refresh_bazaar_data():
    request_refresh("bazaar")
    status_var.set("已提交 BZ 请求，后台继续执行")
    root.after(300, lambda: _poll_market_result("bazaar"))


def refresh_auction_data():
    request_refresh("auction")
    status_var.set("已提交 AH 请求，后台继续执行")
    root.after(300, lambda: _poll_market_result("auction"))


def refresh_table():
    request_refresh("all")
    status_var.set("已提交 BZ + AH 请求，后台继续执行")
    root.after(300, lambda: _poll_market_result("all"))


def init_ui():
    global root, tree, top_canvas, top_frame, status_var, button_right_menu, header_right_menu
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1600x800")
    for meta in COL_META:
        cid = meta["cid"]
        col_var_map[cid] = tk.BooleanVar(value=True)
        filter_min_var_map[cid] = tk.StringVar(value="")
        filter_max_var_map[cid] = tk.StringVar(value="")
        unit_var_map[cid] = tk.StringVar(value="默认")

    outer = tk.Frame(root)
    outer.pack(fill=tk.X, padx=6, pady=6)
    top_scroll = ttk.Scrollbar(outer, orient=tk.HORIZONTAL)
    top_canvas = tk.Canvas(outer, height=45, xscrollcommand=top_scroll.set)
    top_scroll.config(command=top_canvas.xview)
    top_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    top_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    top_frame = tk.Frame(top_canvas)
    top_canvas.create_window((0, 0), window=top_frame, anchor="nw")
    top_frame.bind("<Configure>", lambda _event: top_canvas.configure(scrollregion=top_canvas.bbox("all")))

    _btn_defs.update({
        "refresh": ("刷新全部数据", refresh_table),
        "refresh_bazaar": ("刷新BZ数据", refresh_bazaar_data),
        "refresh_auction": ("刷新AH数据", refresh_auction_data),
        "param": ("参数设置面板", open_param_panel),
        "save": ("保存当前设置", save_config),
        "load": ("加载保存设置", load_config),
        "reset": ("重置全部默认", reset_all_default),
        "search": ("搜索", open_search_dialog),
        "topmost": ("窗口置顶", toggle_topmost),
        "shortcut": ("快捷键设置", open_shortcut_dialog),
        "bazaar": ("Bazaar", open_bazaar),
        "forge": ("Forge", open_forge),
        "enchant": ("Enchant", open_enchant),
        "api": ("输入api（可选）", open_api_dialog),
    })
    button_right_menu = tk.Menu(root, tearoff=0)
    button_right_menu.add_command(label="← 左移此按钮", command=lambda: move_button(-1))
    button_right_menu.add_command(label="→ 右移此按钮", command=lambda: move_button(1))
    status_var = tk.StringVar(value="正在加载配方和缓存")
    rebuild_button_bar()

    table_frame = tk.Frame(root)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
    scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
    tree = ttk.Treeview(table_frame, columns=COL_CID_LIST, show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(fill=tk.BOTH, expand=True)
    header_right_menu = tk.Menu(root, tearoff=0)
    header_right_menu.add_command(label="← 左移此列", command=lambda: craft_move_col(-1))
    header_right_menu.add_command(label="→ 右移此列", command=lambda: craft_move_col(1))
    tree.bind("<Button-3>", craft_show_right_menu)


def run_self_test():
    global recipe_map
    recipe_map = load_recipe_map()
    data = load_cached_data()
    rows = build_craft_rows(data)
    sample = next((row for row in rows if row["name"] == "ENCHANTED_SEEDS"), None)
    print(f"recipes={len(recipe_map)} craft_rows={len(rows)}")
    print(json.dumps(sample, ensure_ascii=False, indent=2) if sample else "ENCHANTED_SEEDS not found")


def main():
    global recipe_map, item_data_cache, btn_order
    ensure_data_dir()
    recipe_map = load_recipe_map()
    item_data_cache = load_cached_data()
    btn_order[:] = normalize_button_order([])
    init_ui()
    load_api_key()
    load_config()
    root.after(100, lambda: _poll_market_result("auction"))
    if item_data_cache:
        apply_filter_sort()
        status_var.set(f"已加载缓存数据 {len(item_data_cache)} 条，配方 {len(build_craft_rows(item_data_cache))} 条")
    else:
        status_var.set("无缓存数据，点击刷新加载最新数据")
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


_btn_defs = {}

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
    else:
        main()
