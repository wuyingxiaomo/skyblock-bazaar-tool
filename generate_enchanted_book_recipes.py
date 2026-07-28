import json
import os
import re


APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "bazaar_data.json")
OUTPUT_DIR = os.path.join(APP_DIR, "enchanted_book_recipe")
PARENTS_FILE = os.path.abspath(os.path.join(APP_DIR, "..", "NotEnoughUpdates-REPO-master", "constants", "parents.json"))
BOOK_PATTERN = re.compile(r"ENCHANTMENT_([A-Z0-9_]+)_(\d+)$")
LEVEL_PATTERN = re.compile(r"^([A-Z0-9_]+);(\d+)$")

# 这些附魔没有可在铁砧中继续升级的 Enchant 配方。
NO_ENCHANT_RECIPES = {
    "BIG_BRAIN", "CHAMPION", "COMPACT", "COUNTER_STRIKE", "CULTIVATING",
    "DELICATE", "DIVINE_GIFT", "EXPERTISE",
    "HECATOMB", "LAPIDARY", "MANA_STEAL", "SMALL_BRAIN",
    "SMARTY_PANTS", "SMOLDERING", "CURSE_OF_VANISHING",
    "WITHER_HUNTER",
}

# Bazaar/仓库数据中可能存在超出游戏实际最高等级的缓存记录。
MAX_LEVEL_OVERRIDES = {
    "FIRE_ASPECT": 2,
    "SNIPE": 3,
    "TRIPLE_STRIKE": 4,
    "THUNDERLORD": 5,
    "FEATHER_FALLING": 10,
    "SYPHON": 5,
}


def load_bazaar_ids():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        value = json.load(file)
    rows = value if isinstance(value, list) else value.get("products", [])
    return {
        row.get("name") or row.get("product_id")
        for row in rows
        if isinstance(row, dict) and (row.get("name") or row.get("product_id"))
    }


def load_repo_enchantment_levels():
    """读取 NEU 的附魔升级关系；未列出的普通附魔不强行限制等级。"""
    try:
        with open(PARENTS_FILE, "r", encoding="utf-8") as file:
            parents = json.load(file)
    except (OSError, ValueError, TypeError):
        return {}
    levels = {}
    for parent, children in parents.items():
        parent_match = LEVEL_PATTERN.fullmatch(str(parent))
        if not parent_match:
            continue
        enchantment, level_text = parent_match.groups()
        levels.setdefault(enchantment, set()).add(int(level_text))
        if isinstance(children, list):
            for child in children:
                child_match = LEVEL_PATTERN.fullmatch(str(child))
                if child_match and child_match.group(1) == enchantment:
                    levels[enchantment].add(int(child_match.group(2)))
    return levels


def build_recipes(item_ids, repo_levels=None):
    repo_levels = repo_levels or {}
    levels = {}
    for item_id in item_ids:
        match = BOOK_PATTERN.fullmatch(str(item_id))
        if not match:
            continue
        enchantment, level_text = match.groups()
        level = int(level_text)
        # 等级 0 是特殊物品定义，不按普通附魔书升级规则生成。
        if level >= 1:
            levels.setdefault(enchantment, set()).add(level)

    # 只有 NEU 明确记录升级关系的附魔才按白名单过滤。
    # 普通附魔通常不出现在 parents.json 中，继续使用 Bazaar 中的等级范围。
    for enchantment, known_levels in repo_levels.items():
        if enchantment in levels:
            levels[enchantment] &= known_levels
    for enchantment in list(levels):
        if enchantment in NO_ENCHANT_RECIPES:
            levels.pop(enchantment, None)
            continue
        maximum = MAX_LEVEL_OVERRIDES.get(enchantment)
        if maximum is not None:
            levels[enchantment] = {level for level in levels[enchantment] if level <= maximum}

    recipes = []
    for enchantment, available_levels in sorted(levels.items()):
        for level in sorted(available_levels):
            if level < 2:
                continue
            output = f"ENCHANTMENT_{enchantment}_{level}"
            alternatives = []
            for material_level in range(level - 1, 0, -1):
                if material_level in available_levels:
                    alternatives.append((material_level, 2 ** (level - material_level)))
            if alternatives:
                recipes.append((output, alternatives))
    return recipes


def main():
    recipes = build_recipes(load_bazaar_ids(), load_repo_enchantment_levels())
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    expected_outputs = {output for output, _alternatives in recipes}
    for filename in os.listdir(OUTPUT_DIR):
        if not filename.lower().endswith(".json"):
            continue
        output_id = filename[:-5]
        if BOOK_PATTERN.fullmatch(output_id) and output_id not in expected_outputs:
            os.remove(os.path.join(OUTPUT_DIR, filename))
    for output, alternatives in recipes:
        path = os.path.join(OUTPUT_DIR, f"{output}.json")
        value = {
            "internalname": output,
            "displayname": output,
            "recipes": [
                {
                    "A1": f"ENCHANTMENT_{output.removeprefix('ENCHANTMENT_').rsplit('_', 1)[0]}_{material_level}:{amount}"
                }
                for material_level, amount in alternatives
            ],
        }
        with open(path, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
    print(f"tradeable_enchantment_levels={sum(1 for item_id in load_bazaar_ids() if BOOK_PATTERN.fullmatch(str(item_id)))}")
    print(f"generated_recipes={len(recipes)}")


if __name__ == "__main__":
    main()
