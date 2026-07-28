"""Skyblock Enchant 主界面。

复用 Craft 的表格、筛选、配置和市场请求界面，但只加载附魔书配方目录，
不会把附魔书配方加入 Craft 的 recipe_map。
"""

import os
import json
import math
import re
import subprocess
import sys

import craft as app
from runtime_paths import DATA_DIR, RESOURCE_DIR, SOURCE_DIR


APP_DIR = DATA_DIR
SOURCE_APP_DIR = SOURCE_DIR
app.APP_TITLE = "Skyblock Enchant 主界面"
app.REQUIRE_AH_PRICE = False
app.USE_AH_FALLBACK = False
app.CONFIG_FILE = os.path.join(APP_DIR, "enchant_config.json")
app.LEGACY_CONFIG_FILE = os.path.join(APP_DIR, "enchant_legacy_config.json")
app.RECIPE_DIRS = [os.path.join(RESOURCE_DIR, "enchanted_book_recipe")]

# Enchant 使用专用的物品/等级/配方字段；等级保留数值用于排序和筛选，显示时转换成罗马数字。
_craft_meta = app.COL_META
app.COL_META = [
    _craft_meta[0],
    {"cid": "level", "name": "等级", "is_num": True},
    next(meta for meta in _craft_meta if meta["cid"] == "recipe"),
    *[meta for meta in _craft_meta if meta["cid"] not in {"name", "recipe", "item_ah"}],
]
app.COL_CID_LIST = [meta["cid"] for meta in app.COL_META]
app.COL_NAME_MAP = {meta["cid"]: meta["name"] for meta in app.COL_META}
app.COL_ISNUM_MAP = {meta["cid"]: meta["is_num"] for meta in app.COL_META}
app.DEFAULT_WIDTHS = {cid: width for cid, width in app.DEFAULT_WIDTHS.items() if cid in app.COL_CID_LIST}
app.DEFAULT_WIDTHS["level"] = 75
app.col_order = [meta["cid"] for meta in app.COL_META]
app.col_width_map = {cid: width for cid, width in app.col_width_map.items() if cid in app.COL_CID_LIST}
app.col_width_map.setdefault("level", 75)
app.DISPLAY_NO_UNIT_CIDS = {"level"}


_ENCHANTMENT_LEVEL_RE = re.compile(r"^(ENCHANTMENT_.+)_([0-9]+)$")


def to_roman(value):
    value = int(value)
    numerals = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    result = []
    for number, numeral in numerals:
        count, value = divmod(value, number)
        result.append(numeral * count)
    return "".join(result) or "I"


def _parse_enchant_output(item_id):
    match = _ENCHANTMENT_LEVEL_RE.fullmatch(str(item_id))
    if not match:
        return None
    return match.group(1), int(match.group(2))


def load_enchant_recipe_map():
    result = {}
    for recipe_dir in app.RECIPE_DIRS:
        if not os.path.isdir(recipe_dir):
            continue
        for filename in os.listdir(recipe_dir):
            if not filename.lower().endswith(".json"):
                continue
            try:
                with open(os.path.join(recipe_dir, filename), "r", encoding="utf-8") as file:
                    item_data = json.load(file)
            except (OSError, ValueError, TypeError):
                continue
            output_id = item_data.get("internalname") or os.path.splitext(filename)[0]
            parsed_output = _parse_enchant_output(output_id)
            if not parsed_output:
                continue
            raw_recipes = item_data.get("recipes")
            if not isinstance(raw_recipes, list):
                raw_recipes = [item_data.get("recipe")]
            alternatives = []
            for raw_recipe in raw_recipes:
                parsed = app.parse_recipe_object(raw_recipe)
                if parsed:
                    alternatives.append(parsed["materials"])
            if alternatives:
                base_id, level = parsed_output
                result[output_id] = {"base_id": base_id, "level": level, "recipes": alternatives}
    return result


def _variant_metric(materials, market, price_key):
    if not all(material_id in market for material_id in materials):
        return None
    return sum(amount * (market[material_id].get(price_key, 0) or 0) for material_id, amount in materials.items())


def _variant_capacity(materials, market, field):
    capacities = []
    for material_id, amount in materials.items():
        if material_id not in market or amount <= 0:
            return None
        capacities.append((market[material_id].get(field, 0) or 0) / amount)
    return math.floor(min(capacities)) if capacities else None


def _variant_metric_sum(materials, market, field):
    if not all(material_id in market for material_id in materials):
        return None
    return sum(amount * (market[material_id].get(field, 0) or 0) for material_id, amount in materials.items())


def _format_enchant_recipe(materials):
    parts = []
    for material_id, amount in materials.items():
        parsed = _parse_enchant_output(material_id)
        if parsed:
            parts.append(f"{to_roman(parsed[1])} x {app.format_quantity(amount)}")
        else:
            parts.append(f"{material_id} x {app.format_quantity(amount)}")
    return " + ".join(parts)


def build_enchant_rows(raw_data):
    market = {row.get("name"): row for row in raw_data if row.get("name")}
    rows = []
    for output_id, recipe_info in app.recipe_map.items():
        item = market.get(output_id)
        if not item:
            continue
        for materials in recipe_info["recipes"]:
            item_buy = item.get("buy", 0) or 0
            item_sell = item.get("sell", 0) or 0
            mat_buy = _variant_metric(materials, market, "buy")
            mat_sell = _variant_metric(materials, market, "sell")
            values = {
                "name": recipe_info["base_id"],
                "level": recipe_info["level"],
                "recipe": _format_enchant_recipe(materials),
                "item_buy": item_buy,
                "item_sell": item_sell,
                "mat_buy": mat_buy,
                "mat_sell": mat_sell,
            }
            buy_pairs = {
                "buy_mat_buy": (item_buy, mat_buy),
                "buy_mat_sell": (item_buy, mat_sell),
                "sell_mat_buy": (item_sell, mat_buy),
                "sell_mat_sell": (item_sell, mat_sell),
            }
            for profit_field, (output_price, material_cost) in buy_pairs.items():
                values[profit_field] = output_price - material_cost if material_cost is not None else None
                values["rate_" + profit_field] = (
                    values[profit_field] / material_cost * 100
                    if material_cost is not None and material_cost > 0 else None
                )
            for field in ("buyOrders", "sellOrders", "vol_buy", "vol_sell", "week_buy", "week_sell"):
                values["mat_" + field] = _variant_metric_sum(materials, market, field)
            values["mat_craft_buy"] = _variant_capacity(materials, market, "vol_buy")
            values["mat_craft_sell"] = _variant_capacity(materials, market, "vol_sell")
            values["mat_craft_week_buy"] = _variant_capacity(materials, market, "week_buy")
            values["mat_craft_week_sell"] = _variant_capacity(materials, market, "week_sell")
            for field in ("item_buyOrders", "item_sellOrders", "item_vol_buy", "item_vol_sell", "item_week_buy", "item_week_sell"):
                source_field = field.removeprefix("item_")
                values[field] = item.get(source_field, 0) or 0
            rows.append(values)
    return rows


_craft_format_value = app.format_value


def format_enchant_value(value, unit, cid=None):
    if cid == "level" and value is not None:
        return to_roman(value)
    return _craft_format_value(value, unit, cid)


app.load_recipe_map = load_enchant_recipe_map
app.build_craft_rows = build_enchant_rows
app.format_value = format_enchant_value

_craft_load_config = app.load_config


def load_config():
    _craft_load_config()
    if "level" in app.col_order:
        app.col_order.remove("level")
    insert_at = app.col_order.index("name") + 1 if "name" in app.col_order else 0
    app.col_order.insert(insert_at, "level")
    app.apply_filter_sort(save_current_widths=False)


app.load_config = load_config


def open_craft():
    command = [sys.executable, "--page", "craft"] if getattr(sys, "frozen", False) else [sys.executable, os.path.join(SOURCE_APP_DIR, "craft.py")]
    subprocess.Popen(command, cwd=APP_DIR)
    app.root.destroy()


app._btn_defs["craft"] = ("Craft", open_craft)
_craft_normalize_button_order = app.normalize_button_order


def refresh_table():
    app.refresh_bazaar_data()
    app.refresh_auction_data()


_craft_poll_market_result = app._poll_market_result


def poll_market_result(source):
    return _craft_poll_market_result(source)


app.refresh_table = refresh_table
app._poll_market_result = poll_market_result


def normalize_button_order(value):
    order = []
    for bid in _craft_normalize_button_order(value):
        if bid not in {"enchant", "filter"} and bid not in order:
            order.append(bid)
    if "craft" not in order:
        insert_at = order.index("bazaar") + 1 if "bazaar" in order else len(order)
        order.insert(insert_at, "craft")
    return order


app.normalize_button_order = normalize_button_order


def main():
    app.main()


if __name__ == "__main__":
    main()
