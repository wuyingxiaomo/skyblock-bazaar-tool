import ctypes
import ctypes.wintypes
import json
import math
import json
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
CONFIG_FILE = os.path.join(APP_DIR, "forge_config.json")
DATA_CACHE_FILE = os.path.join(APP_DIR, "bazaar_data.json")
RECIPE_DIR = os.path.join(RESOURCE_DIR, "forge_recipe")
BAZAAR_URL = "https://api.hypixel.net/skyblock/bazaar"
HEADERS = {"User-Agent": "Mozilla/5.0"}
UNIT_SCALE = {"默认": 1, "k": 1000, "m": 1000000, "b": 1000000000}

COL_META = [
    ("name", "物品ID", False),
    ("item_buy", "物品收购价", True),
    ("item_sell", "物品出售价", True),
    ("item_ah", "AH最低一口价", True),
    ("recipe", "Forge配方材料", False),
    ("mat_buy", "材料收购价", True),
    ("mat_sell", "材料出售价", True),
    ("buy_mat_buy", "收购价-材料收购", True),
    ("buy_mat_sell", "收购价-材料出售", True),
    ("sell_mat_buy", "出售价-材料收购", True),
    ("sell_mat_sell", "出售价-材料出售", True),
    ("hour_buy_mat_buy", "收购价-材料收购小时利润", True),
    ("hour_buy_mat_sell", "收购价-材料出售小时利润", True),
    ("hour_sell_mat_buy", "出售价-材料收购小时利润", True),
    ("hour_sell_mat_sell", "出售价-材料出售小时利润", True),
    ("rate_buy_mat_buy", "收购价/材料收购利润率%", True),
    ("rate_buy_mat_sell", "收购价/材料出售利润率%", True),
    ("rate_sell_mat_buy", "出售价/材料收购利润率%", True),
    ("rate_sell_mat_sell", "出售价/材料出售利润率%", True),
    ("duration", "锻造时间", True),
    ("item_buyOrders", "物品收购挂单量", True),
    ("item_sellOrders", "物品出售挂单量", True),
    ("item_vol_buy", "物品总收购成交量", True),
    ("item_vol_sell", "物品总出售成交量", True),
    ("item_week_buy", "物品7日收购成交量", True),
    ("item_week_sell", "物品7日出售成交量", True),
    ("mat_buyOrders", "材料收购订单数（合计）", True),
    ("mat_sellOrders", "材料出售订单数（合计）", True),
    ("mat_vol_buy", "材料总收购量（各材料合计）", True),
    ("mat_vol_sell", "材料总出售量（各材料合计）", True),
    ("mat_week_buy", "材料7日收购量（各材料合计）", True),
    ("mat_week_sell", "材料7日出售量（各材料合计）", True),
    ("mat_craft_buy", "材料可制作数量（收购量）", True),
    ("mat_craft_sell", "材料可制作数量（出售量）", True),
    ("mat_craft_week_buy", "材料可制作数量（7日收购）", True),
    ("mat_craft_week_sell", "材料可制作数量（7日出售）", True),
]
COL_IDS = [item[0] for item in COL_META]
COL_NAMES = {item[0]: item[1] for item in COL_META}
COL_NUMERIC = {item[0]: item[2] for item in COL_META}
DISPLAY_NO_UNIT_CIDS = {"duration"}
DEFAULT_WIDTHS = {cid: (240 if cid == "name" else 300 if cid == "recipe" else 120) for cid in COL_IDS}

root = None
tree = None
top_canvas = None
top_frame = None
status_var = None
header_menu = None
header_menu_cid = [None]
button_menu = None
button_menu_id = [None]
setting_win = None

api_key = ""
item_data_cache = []
forge_map = {}
auction_index = {}
auction_loading = False
bazaar_loading = False
col_order = list(COL_IDS)
col_widths = dict(DEFAULT_WIDTHS)
col_visible = {cid: True for cid in COL_IDS}
filter_min = {cid: "" for cid in COL_IDS}
filter_max = {cid: "" for cid in COL_IDS}
units = {cid: "默认" for cid in COL_IDS}
filter_sources = {"bazaar": True, "auction": True}
sort_key = "hour_sell_mat_sell"
sort_reverse = True
btn_order = []
is_topmost = False
shortcut_map = {}
shortcut_global = {}
shortcut_win_geometry = None
_prev_shortcut_map = {}
_global_hotkey_thread = None
_global_hotkey_stop = threading.Event()
_combo_bindings = {}
_combo_listeners_bound = False
_held_keys = set()
setting_win_geometry = None
panel_scroll = {"x": 0.0, "y": 0.0}
panel_col_widths = {"check": 150, "field": 220, "min": 130, "max": 130, "unit": 100}
panel_column_order = ["check", "field", "min", "max", "unit"]


def read_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_config(value):
    ensure_data_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)


def load_api_key():
    global api_key
    for path in (CONFIG_FILE, os.path.join(APP_DIR, "craft_config.json"), os.path.join(APP_DIR, "bazaar_config.json")):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as file:
                value = json.load(file)
            if value.get("api_key"):
                api_key = value["api_key"]
                return
        except Exception:
            pass


def save_api_key(value):
    config = read_config()
    config["api_key"] = value
    write_config(config)


def open_api_dialog():
    global api_key
    dialog = tk.Toplevel(root)
    dialog.title("输入 API Key")
    dialog.transient(root)
    dialog.grab_set()
    entry = ttk.Entry(dialog, width=58)
    entry.insert(0, api_key)
    entry.pack(padx=20, pady=(20, 8))
    ttk.Label(dialog, text="API Key 可选，留空可清除").pack(pady=4)
    buttons = ttk.Frame(dialog)
    buttons.pack(pady=(5, 18))

    def confirm():
        nonlocal entry
        api_key = entry.get().strip()
        save_api_key(api_key)
        dialog.destroy()

    ttk.Button(buttons, text="确定", command=confirm).pack(side=tk.LEFT, padx=8)
    ttk.Button(buttons, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=8)
    entry.focus_set()


def parse_input(value):
    if not isinstance(value, str) or ":" not in value:
        return None
    item_id, amount = value.rsplit(":", 1)
    try:
        amount = float(amount)
    except ValueError:
        return None
    return item_id.strip(), amount


def load_forge_map():
    result = {}
    if not os.path.isdir(RECIPE_DIR):
        return result
    for filename in os.listdir(RECIPE_DIR):
        if not filename.lower().endswith(".json"):
            continue
        try:
            with open(os.path.join(RECIPE_DIR, filename), "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, ValueError):
            continue
        output_id = data.get("internalname") or os.path.splitext(filename)[0]
        for recipe in data.get("recipes", []):
            if not isinstance(recipe, dict) or str(recipe.get("type", "")).lower() != "forge":
                continue
            materials = {}
            for raw in recipe.get("inputs", []):
                parsed = parse_input(raw)
                if parsed:
                    materials[parsed[0]] = materials.get(parsed[0], 0) + parsed[1]
            if materials:
                result[recipe.get("overrideOutputId") or output_id] = {
                    "materials": materials,
                    "duration": float(recipe.get("duration", 0) or 0),
                    "count": float(recipe.get("count", 1) or 1),
                }
    return result


def load_cached_data():
    if not os.path.exists(DATA_CACHE_FILE):
        return []
    try:
        with open(DATA_CACHE_FILE, "r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, list) else []
    except Exception:
        return []


def fetch_data():
    params = {"key": api_key} if api_key else {}
    try:
        response = requests.get(BAZAAR_URL, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            return [], f"API错误：{payload.get('cause', '未知原因')}"
    except Exception as exc:
        return [], f"网络请求失败：{exc}"
    rows = []
    for item_id, info in payload.get("products", {}).items():
        quick = info.get("quick_status", {})
        buy = quick.get("buyPrice", 0) or 0
        sell = quick.get("sellPrice", 0) or 0
        rows.append({
            "name": item_id,
            "buy": buy,
            "sell": sell,
            "buyOrders": quick.get("buyOrders", 0) or 0,
            "sellOrders": quick.get("sellOrders", 0) or 0,
            "vol_buy": quick.get("buyVolume", 0) or 0,
            "vol_sell": quick.get("sellVolume", 0) or 0,
            "week_buy": quick.get("buyMovingWeek", 0) or 0,
            "week_sell": quick.get("sellMovingWeek", 0) or 0,
        })
    return rows, "success"


def format_duration(seconds):
    seconds = int(round(seconds or 0))
    if seconds < 60:
        return f"{seconds}秒"
    minutes, second = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}分{second}秒" if second else f"{minutes}分"
    hours, minute = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}小时{minute}分" if minute else f"{hours}小时"
    days, hour = divmod(hours, 24)
    return f"{days}天{hour}小时" if hour else f"{days}天"


def format_value(cid, value):
    if value is None:
        return "-"
    if cid == "duration":
        return format_duration(value)
    scale = UNIT_SCALE.get(units.get(cid, "默认"), 1)
    return f"{value / scale:.2f}".rstrip("0").rstrip(".")


def build_rows(raw_data):
    if not raw_data and not auction_index:
        return []
    market = {
        row["name"]: {**row, "_source": "bazaar"}
        for row in raw_data
        if row.get("name")
    }
    market["SKYBLOCK_COIN"] = {
        "buy": 1,
        "sell": 1,
        "buyOrders": None,
        "sellOrders": None,
        "vol_buy": None,
        "vol_sell": None,
        "week_buy": None,
        "week_sell": None,
        "_source": "synthetic",
    }
    material_ids = {mid for recipe in forge_map.values() for mid in recipe["materials"]}
    for item_id in set(forge_map) | material_ids:
        if item_id in market:
            continue
        auction = lookup_bin(auction_index, item_id)
        if auction:
            price = auction["lowest_bin"]
            market[item_id] = {
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
    for output_id, recipe in forge_map.items():
        item = market.get(output_id)
        if not item:
            continue
        materials = recipe["materials"]
        bazaar_materials = [
            (mid, amount, market[mid])
            for mid, amount in materials.items()
            if mid in market and market[mid].get("_source", "bazaar") == "bazaar"
        ]
        mat_buy = (
            sum(amount * source.get("buy", 0) for _mid, amount, source in bazaar_materials)
            if bazaar_materials else None
        )
        mat_sell = (
            sum(amount * source.get("sell", 0) for _mid, amount, source in bazaar_materials)
            if bazaar_materials else None
        )
        item_buy = item.get("buy")
        item_sell = item.get("sell")
        row = {
            "name": output_id,
            "item_buy": item_buy,
            "item_sell": item_sell,
            "item_ah": (lookup_bin(auction_index, output_id) or {}).get("lowest_bin"),
            "recipe": " + ".join(f"{mid} x {amount:g}" for mid, amount in materials.items()),
            "mat_buy": mat_buy,
            "mat_sell": mat_sell,
            "duration": recipe["duration"],
        }
        for key, base in (("buy_mat_buy", (item_buy, mat_buy)), ("buy_mat_sell", (item_buy, mat_sell)), ("sell_mat_buy", (item_sell, mat_buy)), ("sell_mat_sell", (item_sell, mat_sell))):
            row[key] = base[0] - base[1] if base[1] is not None else None
        for key, profit_key, cost in (("rate_buy_mat_buy", "buy_mat_buy", mat_buy), ("rate_buy_mat_sell", "buy_mat_sell", mat_sell), ("rate_sell_mat_buy", "sell_mat_buy", mat_buy), ("rate_sell_mat_sell", "sell_mat_sell", mat_sell)):
            row[key] = row[profit_key] / cost * 100 if cost else None
        hours = recipe["duration"] / 3600 if recipe["duration"] > 0 else 0
        for profit_key in ("buy_mat_buy", "buy_mat_sell", "sell_mat_buy", "sell_mat_sell"):
            row[f"hour_{profit_key}"] = row[profit_key] / hours if hours and row[profit_key] is not None else None
        for prefix, source in (("item", item),):
            for key in ("buyOrders", "sellOrders", "vol_buy", "vol_sell", "week_buy", "week_sell"):
                row[f"{prefix}_{key}"] = source.get(key) if source.get("_source", "bazaar") == "bazaar" else None
        metric_keys = ("buyOrders", "sellOrders", "vol_buy", "vol_sell", "week_buy", "week_sell")
        material_totals = {key: 0 for key in metric_keys} if bazaar_materials else None
        if material_totals is not None:
            for _mid, _amount, source in bazaar_materials:
                for key in metric_keys:
                    value = source.get(key)
                    if value is None:
                        material_totals = None
                        break
                    # 这里合计的仍是各 Bazaar 材料的市场原始指标。
                    material_totals[key] += value
                if material_totals is None:
                    break
        for key in metric_keys:
            row[f"mat_{key}"] = (
                material_totals[key]
                if material_totals is not None
                else None
            )
        for output_field, source_field in (
            ("mat_craft_buy", "vol_buy"),
            ("mat_craft_sell", "vol_sell"),
            ("mat_craft_week_buy", "week_buy"),
            ("mat_craft_week_sell", "week_sell"),
        ):
            capacities = []
            for _mid, amount, source in bazaar_materials:
                if amount <= 0:
                    capacities = []
                    break
                value = source.get(source_field)
                if value is None:
                    capacities = []
                    break
                capacities.append(value / amount)
            row[output_field] = math.floor(min(capacities)) if capacities else None
        rows.append(row)
    return rows


def get_visible_columns():
    return [cid for cid in col_order if col_visible.get(cid, True)]


def row_matches_filter_sources(row):
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


def parse_bound(value, default):
    try:
        return float(value) if str(value).strip() else default
    except ValueError:
        return default


def filter_rows(rows):
    result = []
    for row in rows:
        if not row_matches_filter_sources(row):
            continue
        valid = True
        for cid, _name, numeric in COL_META:
            if not numeric:
                continue
            source = "auction" if cid == "item_ah" else "bazaar"
            if not filter_sources.get(source, True):
                continue
            if row.get(cid) is None:
                if str(filter_min[cid]).strip() or str(filter_max[cid]).strip():
                    valid = False
                    break
                continue
            scale = UNIT_SCALE.get(units.get(cid, "默认"), 1)
            low = parse_bound(filter_min[cid], -float("inf")) * scale
            high = parse_bound(filter_max[cid], float("inf")) * scale
            if row[cid] < low or row[cid] > high:
                valid = False
                break
        if valid:
            result.append(row)
    return result


def apply_filter_sort(save_current_widths=True):
    if save_current_widths and tree.get_children():
        for cid in col_widths:
            try:
                col_widths[cid] = tree.column(cid, "width")
            except tk.TclError:
                pass
    rows = filter_rows(build_rows(item_data_cache))
    rows.sort(key=lambda row: (row.get(sort_key) is not None, row.get(sort_key) or 0), reverse=sort_reverse)
    tree.delete(*tree.get_children())
    visible = get_visible_columns()
    # 保持完整逻辑列，displaycolumns 只负责控制显示和顺序。
    tree["columns"] = COL_IDS
    tree["displaycolumns"] = visible
    for row in rows:
        tree.insert("", tk.END, values=[row.get(cid) if not COL_NUMERIC[cid] else format_value(cid, row.get(cid)) for cid in COL_IDS])
    arrow = " ↓" if sort_reverse else " ↑"
    for cid in COL_IDS:
        title = COL_NAMES[cid]
        if COL_NUMERIC[cid] and cid not in DISPLAY_NO_UNIT_CIDS:
            title += f"({units.get(cid) or '默认'})"
        if cid == sort_key:
            title += arrow
        tree.heading(cid, text=title, command=lambda selected=cid: on_header_click(selected))
        tree.column(cid, width=col_widths.get(cid, 120), minwidth=50, stretch=False)
    status_var.set(f"Forge配方{len(forge_map)}条，显示{len(rows)}条")


def on_header_click(cid):
    global sort_key, sort_reverse
    if cid == sort_key:
        sort_reverse = not sort_reverse
    else:
        sort_key, sort_reverse = cid, True
    apply_filter_sort()


def move_column(delta):
    cid = header_menu_cid[0]
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
    visible = get_visible_columns()
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


def show_header_menu(event):
    if tree.identify_region(event.x, event.y) == "heading":
        index = int(tree.identify_column(event.x)[1:]) - 1
        visible = get_visible_columns()
        if 0 <= index < len(visible):
            header_menu_cid[0] = visible[index]
            header_menu.tk_popup(event.x_root, event.y_root)
        return
    copy_item_id(event.y)


def save_config():
    global col_widths
    if tree.get_children():
        for cid in col_widths:
            try:
                col_widths[cid] = tree.column(cid, "width")
            except tk.TclError:
                pass
    config = read_config()
    config.update({
        "window": {"w": root.winfo_width(), "h": root.winfo_height(), "x": root.winfo_x(), "y": root.winfo_y()},
        "sort": {"key": sort_key, "reverse": sort_reverse},
        "col_order": list(col_order),
        "col_widths": dict(col_widths),
        "columns": dict(col_visible),
        "filter_min": dict(filter_min),
        "filter_max": dict(filter_max),
        "units": dict(units),
        "filter_sources": dict(filter_sources),
        "setting_win_geometry": setting_win_geometry,
        "panel_scroll": dict(panel_scroll),
        "panel_col_widths": dict(panel_col_widths),
        "panel_column_order": list(panel_column_order),
        "btn_order": list(btn_order),
        "is_topmost": is_topmost,
        "shortcut_map": dict(shortcut_map),
        "shortcut_global": dict(shortcut_global),
        "shortcut_win_geometry": shortcut_win_geometry,
    })
    write_config(config)
    status_var.set("Forge 配置已保存")


def load_config():
    global sort_key, sort_reverse, filter_sources, setting_win_geometry, panel_scroll, panel_col_widths, panel_column_order
    global is_topmost, shortcut_win_geometry
    config = read_config()
    window = config.get("window", {})
    if window:
        try:
            root.geometry(f"{int(window['w'])}x{int(window['h'])}+{int(window['x'])}+{int(window['y'])}")
        except (KeyError, TypeError, ValueError):
            pass
    sorting = config.get("sort", {})
    if sorting.get("key") in COL_IDS:
        sort_key = sorting["key"]
    sort_reverse = bool(sorting.get("reverse", sort_reverse))
    stored_order = config.get("col_order", col_order)
    if isinstance(stored_order, list):
        col_order[:] = [cid for cid in stored_order if cid in COL_IDS]
        col_order.extend(cid for cid in COL_IDS if cid not in col_order)
    for cid, width in config.get("col_widths", {}).items():
        if cid in col_widths and isinstance(width, (int, float)):
            col_widths[cid] = width
    for cid in COL_IDS:
        if cid in config.get("columns", {}):
            col_visible[cid] = bool(config["columns"][cid])
        if cid in config.get("filter_min", {}):
            filter_min[cid] = str(config["filter_min"][cid])
        if cid in config.get("filter_max", {}):
            filter_max[cid] = str(config["filter_max"][cid])
        if config.get("units", {}).get(cid) in UNIT_SCALE:
            units[cid] = config["units"][cid]
    stored_sources = config.get("filter_sources", {})
    if isinstance(stored_sources, dict):
        for source in filter_sources:
            if source in stored_sources:
                filter_sources[source] = bool(stored_sources[source])
    setting_win_geometry = config.get("setting_win_geometry") or None
    if isinstance(config.get("panel_scroll"), dict):
        panel_scroll.update(config["panel_scroll"])
    if isinstance(config.get("panel_col_widths"), dict):
        for key, width in config["panel_col_widths"].items():
            if key in panel_col_widths and isinstance(width, (int, float)):
                panel_col_widths[key] = width
    if isinstance(config.get("panel_column_order"), list):
        panel_column_order[:] = [key for key in config["panel_column_order"] if key in panel_col_widths]
        panel_column_order.extend(key for key in panel_col_widths if key not in panel_column_order)
    btn_order[:] = normalize_button_order(config.get("btn_order", []))
    shortcut_map.clear()
    shortcut_map.update(config.get("shortcut_map", {}))
    shortcut_global.clear()
    shortcut_global.update(config.get("shortcut_global", {}))
    shortcut_win_geometry = config.get("shortcut_win_geometry") or None
    is_topmost = bool(config.get("is_topmost", False))
    root.attributes("-topmost", is_topmost)
    rebuild_button_bar()
    button = find_topmost_button()
    if button:
        button.config(text="取消置顶" if is_topmost else "窗口置顶")
    apply_shortcuts()
    apply_filter_sort(save_current_widths=False)


def reset_all_default():
    global sort_key, sort_reverse, filter_sources, is_topmost, shortcut_win_geometry
    sort_key, sort_reverse = "hour_sell_mat_sell", True
    filter_sources = {"bazaar": True, "auction": True}
    is_topmost = False
    shortcut_map.clear()
    shortcut_global.clear()
    shortcut_win_geometry = None
    root.attributes("-topmost", False)
    col_order[:] = list(COL_IDS)
    col_widths.update(DEFAULT_WIDTHS)
    for cid in COL_IDS:
        col_visible[cid] = True
        filter_min[cid] = ""
        filter_max[cid] = ""
        units[cid] = "默认"
    rebuild_button_bar()
    apply_shortcuts()
    apply_filter_sort(save_current_widths=False)
    status_var.set("已重置 Forge 全部设置为默认")


def find_topmost_button():
    for widget in top_frame.winfo_children():
        if isinstance(widget, tk.Button) and "置顶" in widget.cget("text"):
            return widget
    return None


def toggle_topmost():
    global is_topmost
    is_topmost = not is_topmost
    root.attributes("-topmost", is_topmost)
    button = find_topmost_button()
    if button:
        button.config(text="取消置顶" if is_topmost else "窗口置顶")
    if is_topmost:
        root.lift()


# 顶部所有按钮都可以设置快捷键。
SHORTCUT_ELIGIBLE = [
    "refresh", "refresh_bazaar", "refresh_auction", "param", "save", "load",
    "reset", "topmost", "shortcut", "bazaar", "craft", "enchant", "api",
]
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
    mod = 0x4000
    for modifier in parts[:-1]:
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
        "topmost": toggle_topmost,
        "shortcut": open_shortcut_dialog,
        "bazaar": open_bazaar,
        "craft": open_craft,
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
    if key in MODIFIER_KEYSYMS or isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text)):
        return
    _held_keys.add(key)
    for prefix, final, command in _combo_bindings.values():
        if key == final and prefix.issubset(_held_keys):
            command()
            break


def on_combo_release(event):
    _held_keys.discard(event.keysym.upper())


def apply_shortcuts():
    global _prev_shortcut_map, _combo_listeners_bound
    commands = shortcut_commands()
    for old_value in _prev_shortcut_map.values():
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
        command = commands[bid]
        sequence = shortcut_to_tk(value)
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
    btn_name = button_defs.get(bid, ("?",))[0]
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
    for index, bid in enumerate(SHORTCUT_ELIGIBLE, 2):
        tk.Label(frame, text=button_defs[bid][0], width=20, anchor="w").grid(row=index, column=0, sticky="w", padx=5, pady=3)
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


def normalize_button_order(value):
    order = [bid for bid in (list(value) if isinstance(value, list) else []) if bid != "filter"]
    defaults = ["refresh", "refresh_bazaar", "refresh_auction", "param", "save", "load", "reset", "topmost", "shortcut", "bazaar", "craft", "enchant", "api"]
    for bid in defaults:
        if bid not in order:
            if bid == "bazaar":
                order.append(bid)
            elif bid == "refresh_bazaar":
                order.insert(order.index("refresh") + 1 if "refresh" in order else len(order), bid)
            elif bid == "refresh_auction":
                order.insert(order.index("refresh_bazaar") + 1 if "refresh_bazaar" in order else len(order), bid)
            elif bid == "param":
                order.insert(order.index("refresh_auction") + 1 if "refresh_auction" in order else len(order), bid)
            elif bid == "craft":
                order.insert(order.index("bazaar") + 1 if "bazaar" in order else len(order), bid)
            elif bid == "enchant":
                order.insert(order.index("craft") + 1 if "craft" in order else len(order), bid)
            else:
                order.append(bid)
    # 导航按钮固定放在操作按钮之后，顺序与 Bazaar/Craft 的末尾导航一致。
    for bid in ("bazaar", "craft", "enchant", "api"):
        if bid in order:
            order.remove(bid)
    order.extend(("bazaar", "craft", "enchant", "api"))
    return order


def rebuild_button_bar():
    for widget in top_frame.winfo_children():
        widget.destroy()
    for bid in btn_order:
        if bid not in button_defs:
            continue
        label, command = button_defs[bid]
        button = tk.Button(top_frame, text=label, command=command, font=("", 11))
        button.pack(side=tk.LEFT, padx=6)
        button.bind("<Button-3>", lambda event, selected=bid: show_button_menu(event, selected))
    tk.Label(top_frame, textvariable=status_var, fg="#333").pack(side=tk.LEFT, padx=30)


def show_button_menu(event, bid):
    button_menu_id[0] = bid
    button_menu.tk_popup(event.x_root, event.y_root)


def move_button(delta):
    bid = button_menu_id[0]
    if bid not in btn_order:
        return
    index = btn_order.index(bid)
    target = index + delta
    if 0 <= target < len(btn_order):
        btn_order[index], btn_order[target] = btn_order[target], btn_order[index]
        rebuild_button_bar()


def open_bazaar():
    command = [sys.executable, "--page", "bazaar"] if getattr(sys, "frozen", False) else [sys.executable, os.path.join(SOURCE_APP_DIR, "bazaar.py")]
    subprocess.Popen(command, cwd=APP_DIR)
    root.destroy()


def open_craft():
    command = [sys.executable, "--page", "craft"] if getattr(sys, "frozen", False) else [sys.executable, os.path.join(SOURCE_APP_DIR, "craft.py")]
    subprocess.Popen(command, cwd=APP_DIR)
    root.destroy()


def open_enchant():
    command = [sys.executable, "--page", "enchant"] if getattr(sys, "frozen", False) else [sys.executable, os.path.join(SOURCE_APP_DIR, "enchant.py")]
    subprocess.Popen(command, cwd=APP_DIR)
    root.destroy()


def open_param_panel():
    global setting_win, setting_win_geometry, panel_scroll, panel_col_widths, panel_column_order, col_order, filter_sources
    if setting_win and setting_win.winfo_exists():
        setting_win.lift()
        return
    setting_win = tk.Toplevel(root)
    setting_win.title("Forge 参数设置")
    setting_win.geometry(setting_win_geometry or "1100x750")
    setting_win.transient(root)
    setting_win.grab_set()

    panel_order = list(col_order)
    columns = list(panel_column_order)
    snapshot = {
        "order": list(panel_order),
        "panel_columns": list(columns),
        "columns": dict(col_visible),
        "filter_min": dict(filter_min),
        "filter_max": dict(filter_max),
        "units": dict(units),
        "filter_sources": dict(filter_sources),
    }

    body = ttk.Frame(setting_win)
    body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
    canvas = tk.Canvas(body, highlightthickness=0)
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
        if not inner.winfo_exists():
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
        canvas.configure(scrollregion=canvas.bbox("all"))

    def stop_resize(_event=None):
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
            for widget, key, span in row_widgets[row_cid]:
                widget.grid_configure(row=row, column=columns.index(key), columnspan=span)
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
        index = panel_order.index(cid)
        target = index + delta
        if 0 <= target < len(panel_order):
            panel_order[index], panel_order[target] = panel_order[target], panel_order[index]
            col_order[:] = panel_order
            regrid_panel()
            def refresh_after_move():
                try:
                    apply_filter_sort(save_current_widths=False)
                    root.update_idletasks()
                except tk.TclError:
                    pass
            root.after_idle(refresh_after_move)

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

    for index, key in enumerate(columns):
        header = tk.Label(inner, text=header_names[key], anchor="w", relief="raised", cursor="sb_h_double_arrow")
        header.grid(row=0, column=index, sticky="ew", padx=1, pady=(1, 5))
        header.bind("<ButtonPress-1>", lambda event, selected=key: start_resize(event, selected))
        header.bind("<Button-3>", lambda event, selected=key: show_panel_column_menu(event, selected), add="+")
        header_widgets[key] = header

    meta_by_cid = {cid: (name, numeric) for cid, name, numeric in COL_META}
    live_vars = []
    for row, cid in enumerate(panel_order, 1):
        name, numeric = meta_by_cid[cid]
        row_widgets[cid] = []
        visible_var = tk.BooleanVar(value=col_visible[cid])
        visible_trace = visible_var.trace_add("write", lambda *_args, c=cid, v=visible_var: (col_visible.__setitem__(c, v.get()), apply_filter_sort(save_current_widths=False)))
        live_vars.append((visible_var, visible_trace))
        check = ttk.Checkbutton(inner, variable=visible_var)
        check.grid(row=row, column=columns.index("check"), sticky="w", padx=5, pady=5)
        row_widgets[cid].append((check, "check", 1))
        field = ttk.Label(inner, text=name, anchor="w")
        field.grid(row=row, column=columns.index("field"), sticky="w", padx=5, pady=5)
        row_widgets[cid].append((field, "field", 1))
        if numeric:
            min_var = tk.StringVar(value=filter_min[cid])
            max_var = tk.StringVar(value=filter_max[cid])
            unit_var = tk.StringVar(value=units.get(cid, "默认"))
            for variable, target, key in ((min_var, filter_min, "min"), (max_var, filter_max, "max"), (unit_var, units, "unit")):
                trace_id = variable.trace_add("write", lambda *_args, c=cid, v=variable, d=target: (d.__setitem__(c, v.get()), apply_filter_sort(save_current_widths=False)))
                live_vars.append((variable, trace_id))
            minimum = ttk.Entry(inner, textvariable=min_var)
            maximum = ttk.Entry(inner, textvariable=max_var)
            unit = ttk.Combobox(inner, values=list(UNIT_SCALE), state="readonly", textvariable=unit_var)
            minimum.grid(row=row, column=columns.index("min"), sticky="ew", padx=5, pady=5)
            maximum.grid(row=row, column=columns.index("max"), sticky="ew", padx=5, pady=5)
            unit.grid(row=row, column=columns.index("unit"), sticky="ew", padx=5, pady=5)
            row_widgets[cid].extend(((minimum, "min", 1), (maximum, "max", 1), (unit, "unit", 1)))
        else:
            unsupported = ttk.Label(inner, text="不支持筛选", foreground="#888")
            dash = ttk.Label(inner, text="—", foreground="#888")
            unsupported.grid(row=row, column=columns.index("min"), columnspan=2, sticky="w", padx=5, pady=5)
            dash.grid(row=row, column=columns.index("unit"), sticky="w", padx=5, pady=5)
            row_widgets[cid].extend(((unsupported, "min", 2), (dash, "unit", 1)))
        for widget, _key, _span in row_widgets[cid]:
            bind_row_menu(widget, cid)
    apply_column_widths()

    source_vars = {source: tk.BooleanVar(value=filter_sources.get(source, True)) for source in ("bazaar", "auction")}

    def commit_sources():
        for source, variable in source_vars.items():
            filter_sources[source] = bool(variable.get())

    def refresh_from_source_toggle():
        commit_sources()
        apply_filter_sort(save_current_widths=False)

    def restore_snapshot():
        panel_order[:] = snapshot["order"]
        col_order[:] = panel_order
        columns[:] = snapshot["panel_columns"]
        panel_column_order[:] = columns
        col_visible.update(snapshot["columns"])
        filter_min.update(snapshot["filter_min"])
        filter_max.update(snapshot["filter_max"])
        units.update(snapshot["units"])
        filter_sources.update(snapshot["filter_sources"])
        regrid_panel()
        apply_filter_sort(save_current_widths=False)

    def close_panel(discard=False):
        global setting_win, setting_win_geometry, panel_scroll
        if discard:
            restore_snapshot()
        for variable, trace_id in live_vars:
            try:
                variable.trace_remove("write", trace_id)
            except tk.TclError:
                pass
        stop_resize()
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


def restore_and_close(snapshot):
    global setting_win, filter_sources
    col_visible.update(snapshot[0])
    filter_min.update(snapshot[1])
    filter_max.update(snapshot[2])
    units.update(snapshot[3])
    filter_sources.update(snapshot[4])
    apply_filter_sort(save_current_widths=False)
    setting_win.destroy()


def refresh_table():
    refresh_bazaar_data()
    refresh_auction_data()


def close_app():
    stop_global_hotkeys()
    root.destroy()


def refresh_bazaar_data():
    global bazaar_loading, item_data_cache
    if bazaar_loading:
        return
    bazaar_loading = True
    status_var.set("正在后台请求 Bazaar...")

    def worker():
        data, message = fetch_bazaar_data(api_key)

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
        auctions, message = fetch_auctions(api_key)
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
    global root, tree, top_canvas, top_frame, status_var, header_menu, button_menu, setting_win
    root = tk.Tk()
    root.title("Skyblock Forge 主界面")
    root.geometry("1700x800")
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
    status_var = tk.StringVar(value="正在加载 Forge 配方")
    button_defs.update({
        "refresh": ("刷新全部数据", refresh_table),
        "refresh_bazaar": ("刷新BZ数据", refresh_bazaar_data),
        "refresh_auction": ("刷新AH数据", refresh_auction_data),
        "param": ("参数设置面板", open_param_panel),
        "save": ("保存当前设置", save_config),
        "load": ("加载保存设置", load_config),
        "reset": ("重置全部默认", reset_all_default),
        "topmost": ("窗口置顶", toggle_topmost),
        "shortcut": ("快捷键设置", open_shortcut_dialog),
        "bazaar": ("Bazaar", open_bazaar),
        "craft": ("Craft", open_craft),
        "enchant": ("Enchant", open_enchant),
        "api": ("输入api（可选）", open_api_dialog),
    })
    button_menu = tk.Menu(root, tearoff=0)
    button_menu.add_command(label="← 左移此按钮", command=lambda: move_button(-1))
    button_menu.add_command(label="→ 右移此按钮", command=lambda: move_button(1))
    btn_order[:] = normalize_button_order([])
    rebuild_button_bar()
    table_frame = tk.Frame(root)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
    scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
    tree = ttk.Treeview(table_frame, columns=COL_IDS, show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(fill=tk.BOTH, expand=True)
    header_menu = tk.Menu(root, tearoff=0)
    header_menu.add_command(label="← 左移此列", command=lambda: move_column(-1))
    header_menu.add_command(label="→ 右移此列", command=lambda: move_column(1))
    tree.bind("<Button-3>", show_header_menu)


def run_self_test():
    global forge_map
    forge_map = load_forge_map()
    print(f"forge_recipes={len(forge_map)}")
    for key in list(forge_map)[:3]:
        print(key, format_duration(forge_map[key]["duration"]), forge_map[key]["materials"])


def main():
    global forge_map, item_data_cache
    ensure_data_dir()
    forge_map = load_forge_map()
    item_data_cache = load_cached_data()
    init_ui()
    load_api_key()
    load_config()
    root.after(100, lambda: _poll_market_result("auction"))
    if item_data_cache:
        apply_filter_sort(save_current_widths=False)
    else:
        status_var.set(f"已加载 Forge 配方 {len(forge_map)} 条，无缓存数据")
    root.protocol("WM_DELETE_WINDOW", close_app)
    root.mainloop()


button_defs = {}


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
    else:
        main()
