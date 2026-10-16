# NEU 配方与市场缓存核对报告

本次对比更新后的 `NotEnoughUpdates-REPO-master/items` 与更新前的 Craft/Forge 物品库，并使用 `third/bazaar/bazaar_config` 中已有的 BZ/AH 缓存核对市场物品。没有重新请求市场数据。

“新增物品”指相对更新前物品库快照新增的 ID，不是对两次历史 API 快照的比较；无法据此断言这些物品都是本次游戏更新首次加入。AH 只包含缓存抓取时有拍卖的物品。

AH 共解析 45,463 条拍卖的物品 NBT，提取出 2,836 种物品 ID，全部解析成功。普通物品、附魔、宠物稀有度和符文等级按 ID 区分；BZ 附魔书和狩猎碎片使用 NEU 元数据及 attribute_shards.json 中的映射。

## 核对结果

| 项目 | 数量 |
| --- | ---: |
| 更新前物品 JSON（Craft + Forge） | 8,498 |
| 新 NEU 物品 JSON | 8,937 |
| 新增物品 ID / NEU 移除 ID | 444 / 5 |
| 当前 BZ 缓存物品 | 2,201 |
| 新增且在 BZ 缓存中出现 | 242 |
| 新增且在 AH 缓存中出现 | 66 |
| 新增且有 Craft/Forge 配方的市场物品 | 11 |
| 新增市场物品中，NEU 没有普通合成或锻造配方 | 297 |
| 上述 297 个中，已另补 Enchant II–V 配方的物品 | 12 |
| 其余没有可导入本工具的配方（BZ / AH） | 285（228 / 57） |

“未记录配方”表示当前 NEU 没有普通 Craft 或 Forge 配方，不代表游戏中一定无法合成。掉落、NPC 商店、交易、宠物升级、符文合并等途径没有伪装成 Craft 配方。

## 本次配方更新

### 新增 11 个 Craft 配方

这些是新增的有效配方；其中部分物品之前已有元数据，只是没有配方。材料数量按一次合成列出，应用计算价格时会除以产出数量。

| 物品 ID | 一次合成材料 | 产出 | 当前缓存来源 |
| --- | --- | ---: | --- |
| `BRINE_TONIC` | LUSHLILAC × 32 + SEA_BRINE × 1 + WET_WATER × 32 | 1 | BZ |
| `CONTRABAND` | BUSTED_BELT_BUCKLE × 8 + OLD_LEATHER_BOOT × 1 + RUSTY_COIN × 64 + WATER_ORB × 1 | 1 | AH（有一口价） |
| `CORRUPTION;1` | CORRUPTED_FRAGMENT × 64 + ENCHANTED_PAPER × 3 | 1 | BZ |
| `HOTSPOT_ARTIFACT` | HOTSPOT_RING × 1 + HOTSPOT_WATER_ORB × 1 | 1 | AH（有一口价） |
| `HOTSPOT_RING` | BUSTED_BELT_BUCKLE × 4 + ENCHANTED_CLAY_BALL × 32 + HOTSPOT_TALISMAN × 1 | 1 | AH（有一口价） |
| `HOTSPOT_TALISMAN` | ENCHANTED_CLAY_BALL × 4 + RUSTY_COIN × 4 | 1 | AH（仅竞拍） |
| `LARGE_BAIT_SACK` | ENCHANTED_RAW_FISH × 128 + MEDIUM_BAIT_SACK × 1 | 1 | 当前缓存未出现 |
| `MARSHROOM` | ENCHANTED_VINESAP × 4 + STRETCHING_STICKS × 64 + WET_WATER × 16 | 1 | BZ |
| `MEDIUM_BAIT_SACK` | ENCHANTED_RAW_FISH × 8 + SMALL_BAIT_SACK × 1 | 1 | 当前缓存未出现 |
| `NOTHING_IN_A_BOTTLE` | LIVING_METAL × 8 + METAL_HEART × 1 | 1 | AH（有一口价） |
| `SMALL_BAIT_SACK` | RAW_FISH × 8 | 1 | 当前缓存未出现 |

`CORRUPTION;1` 会在 Craft 中转换为 `ENCHANTMENT_CORRUPTION_1`，以匹配 BZ 价格。其他通过普通合成制作的附魔书同样转换 ID；铁砧合并配方继续独立放在 Enchant。

### 更新 5 个已有 Craft 配方

| 物品 ID | 原配方 | 新配方 |
| --- | --- | --- |
| `BLOOD_DONOR_ARTIFACT` | BLOOD_DONOR_RING × 1 + HEMOBOMB × 128 → 1 | BLOOD_DONOR_RING × 1 + HEMOBOMB × 32 → 1 |
| `EXPORTABLE_CARROTS` | 原默认：HALF_EATEN_CARROT × 120 + SCRIBE_CRUX × 1 + VOLT_CRUX × 1 → 48 | 新默认：NEARLY_WHOLE_CARROT × 1 + SCRIBE_CRUX × 1 + VOLT_CRUX × 1 → 64；原半根胡萝卜配方仍保留在文件的其他配方中 |
| `FAMILY_SIZED_POT_OF_HONEYCOMB` | ENCHANTED_HELIX_LOG × 16 + ENCHANTED_HONEYCOMB × 8 → 1 | ENCHANTED_HELIX_LOG × 32 + ENCHANTED_HONEYCOMB × 8 → 8 |
| `JUMBO_POT_OF_HONEYCOMB` | ENCHANTED_HONEYCOMB × 16 + HELIXIS × 1 → 1 | 同样材料 → 8 |
| `MAGMA_LORD_GAUNTLET` | MAGMA_LORD_FRAGMENT × 6 → 1 | MAGMA_LORD_FRAGMENT × 5 → 1；NEU 显示名现为 Magma Lord Necklace |

### 新增 4 个 Forge 配方

| 物品 ID | 材料 | 产出 | 时间 |
| --- | --- | ---: | --- |
| `POWDER_OF_ONE` | REFINED_MITHRIL × 1 + REFINED_TITANIUM × 1 | 1 | 1 小时 |
| `POWDER_OF_THE_FEW` | POWDER_OF_ONE × 1 + GEMSTONE_MIXTURE × 4 + REFINED_MINERAL × 32 | 1 | 1 小时 |
| `POWDER_OF_THE_MANY` | POWDER_OF_THE_FEW × 1 + GLACITE_AMALGAMATION × 4 + GLOSSY_GEMSTONE × 32 | 1 | 6 小时 |
| `PRECURSOR_DRONE;4` | PRECURSOR_APPARATUS × 1 + SKYBLOCK_COIN × 300000 | 1 | 72 小时 |

现有 120 个 Forge 配方的材料和时间未变，新增后共 124 个。

### 新增 12 个 Enchant 配方文件

KARMA、PETALFALL、STEALTH 各补 II、III、IV、V，共 12 个成品等级、30 个合并方式。例如 V 级分别列出 IV × 2、III × 4、II × 8、I × 16。

依据：三种附魔的 NEU lore 均写有 Combinable in Anvil，并标明 Bazaar I–V；Karma VI 来自 Forest's Favor，Stealth VI 来自 Distant Echo，因此没有按常规合并生成 VI。未重写其他人工校正过的附魔规则。

### 移除旧记录

`STEALTH;1` 已被新 NEU 移除普通合成配方，保留物品元数据；不再使用 PAPER + MANGCORE 的旧配方。

以下 5 个文件已不在新 NEU 中，已从本地有效目录移除；旧内容仍可由 Git 历史恢复，也在本次任务的系统临时目录保留副本。

- `BRRASMASS_BEASTSLAYER_NPC`
- `PHOENIX;3`
- `PHOENIX;4`
- `PRECURSOR_DRONE;0`
- `VANGUARD_NPC`

其中 `PRECURSOR_DRONE;0` 的旧普通合成配方不再使用；新 NEU 提供的是 `PRECURSOR_DRONE;4` 的 Forge 配方。Phoenix 新记录为 `PHOENIX;7` / `PHOENIX;8`。

## 新增 BZ 物品中未记录 Craft/Forge 配方的清单

共 240 个，其中 12 个附魔成品等级已补入 Enchant。以下分组均使用 BZ 物品 ID；碎片同时给出 NEU ID，避免别名误报。

### 普通物品（35 个）

| BZ ID | 名称 / NEU ID | 处理 |
| --- | --- | --- |
| `BEHEMOTH_POT_OF_HONEYCOMB` | Behemoth Pot of Honeycomb | 未记录 Craft/Forge 配方 |
| `BOTTLED_MISCHIEF` | Bottled Mischief | 未记录 Craft/Forge 配方 |
| `DISTANT_ECHO` | Distant Echo | 未记录 Craft/Forge 配方 |
| `ESSENCE_SAFARI` | Safari Essence | 未记录 Craft/Forge 配方 |
| `EXTREMELY_MILD_ADHESIVE` | Extremely Mild Adhesive | 未记录 Craft/Forge 配方 |
| `FIGHTING_BOOSTER_UNCOMMON` | Uncommon Fighting Booster Upgrade | 未记录 Craft/Forge 配方 |
| `FORAGING_FORTUNE_BOOSTER_UNCOMMON` | Uncommon Foraging Fortune Booster Upgrade | 未记录 Craft/Forge 配方 |
| `FORAGING_WISDOM_BOOSTER_UNCOMMON` | Uncommon Foraging Wisdom Booster Upgrade | 未记录 Craft/Forge 配方 |
| `FORESTS_FAVOR` | Forest's Favor | 未记录 Craft/Forge 配方 |
| `FROGS_SPIRIT_SCROLL` | Frog's Spirit | 未记录 Craft/Forge 配方 |
| `GENERATOR_UPGRADE_STONE_ACACIA_12` | Acacia Minion XII Upgrade Stone | 未记录 Craft/Forge 配方 |
| `GENERATOR_UPGRADE_STONE_BIRCH_12` | Birch Minion XII Upgrade Stone | 未记录 Craft/Forge 配方 |
| `GENERATOR_UPGRADE_STONE_DARK_OAK_12` | Dark Oak Minion XII Upgrade Stone | 未记录 Craft/Forge 配方 |
| `GENERATOR_UPGRADE_STONE_JUNGLE_12` | Jungle Minion XII Upgrade Stone | 未记录 Craft/Forge 配方 |
| `GENERATOR_UPGRADE_STONE_OAK_12` | Oak Minion XII Upgrade Stone | 未记录 Craft/Forge 配方 |
| `GENERATOR_UPGRADE_STONE_SPRUCE_12` | Spruce Minion XII Upgrade Stone | 未记录 Craft/Forge 配方 |
| `GIANT_SLOTH_CLAW` | Giant Sloth Claw | 未记录 Craft/Forge 配方 |
| `HELIX_LOG` | Helix Log | 未记录 Craft/Forge 配方 |
| `HONEYCOMB` | Honeycomb | 未记录 Craft/Forge 配方 |
| `HUNTING_WISDOM_BOOSTER_COMMON` | Common Hunting Wisdom Booster | 未记录 Craft/Forge 配方 |
| `HUNTING_WISDOM_BOOSTER_UNCOMMON` | Uncommon Hunting Wisdom Booster Upgrade | 未记录 Craft/Forge 配方 |
| `ISOPOD_HUSK` | Isopod Husk | 未记录 Craft/Forge 配方 |
| `LARGE_SLOTH_CLAW` | Large Sloth Claw | 未记录 Craft/Forge 配方 |
| `MEDIUM_SLOTH_CLAW` | Medium Sloth Claw | 未记录 Craft/Forge 配方 |
| `MIRIA_COUPON` | Miria's Coupon | 未记录 Craft/Forge 配方 |
| `MIRIA_PRIZE` | Miria's Prize | 未记录 Craft/Forge 配方 |
| `MORNING_DEW` | Morning Dew | 未记录 Craft/Forge 配方 |
| `RAINBOW_FEATHER` | Rainbow Feather | 未记录 Craft/Forge 配方 |
| `REINFORCED_NETTING` | Reinforced Netting | 未记录 Craft/Forge 配方 |
| `RUBY_VEILSHROOM` | Ruby Veilshroom | 未记录 Craft/Forge 配方 |
| `SEA_BRINE` | Sea Brine | 未记录 Craft/Forge 配方 |
| `SMALL_SLOTH_CLAW` | Small Sloth Claw | 未记录 Craft/Forge 配方 |
| `SUBLIME_SILK` | Sublime Silk | 未记录 Craft/Forge 配方 |
| `SWEEP_BOOSTER_UNCOMMON` | Uncommon Sweep Booster Upgrade | 未记录 Craft/Forge 配方 |
| `WATER_HYACINTH` | Water Hyacinth | 未记录 Craft/Forge 配方 |

### 附魔书（14 个）

| BZ ID | 名称 / NEU ID | 处理 |
| --- | --- | --- |
| `ENCHANTMENT_KARMA_1` | KARMA 1 | 未记录 Craft/Forge 配方 |
| `ENCHANTMENT_KARMA_2` | KARMA 2 | 已补 Enchant 配方 |
| `ENCHANTMENT_KARMA_3` | KARMA 3 | 已补 Enchant 配方 |
| `ENCHANTMENT_KARMA_4` | KARMA 4 | 已补 Enchant 配方 |
| `ENCHANTMENT_KARMA_5` | KARMA 5 | 已补 Enchant 配方 |
| `ENCHANTMENT_PETALFALL_1` | PETALFALL 1 | 未记录 Craft/Forge 配方 |
| `ENCHANTMENT_PETALFALL_2` | PETALFALL 2 | 已补 Enchant 配方 |
| `ENCHANTMENT_PETALFALL_3` | PETALFALL 3 | 已补 Enchant 配方 |
| `ENCHANTMENT_PETALFALL_4` | PETALFALL 4 | 已补 Enchant 配方 |
| `ENCHANTMENT_PETALFALL_5` | PETALFALL 5 | 已补 Enchant 配方 |
| `ENCHANTMENT_STEALTH_2` | STEALTH 2 | 已补 Enchant 配方 |
| `ENCHANTMENT_STEALTH_3` | STEALTH 3 | 已补 Enchant 配方 |
| `ENCHANTMENT_STEALTH_4` | STEALTH 4 | 已补 Enchant 配方 |
| `ENCHANTMENT_STEALTH_5` | STEALTH 5 | 已补 Enchant 配方 |

### 狩猎碎片（131 个）

| BZ ID | 名称 / NEU ID | 处理 |
| --- | --- | --- |
| `SHARD_BLUE_JAY` | ATTRIBUTE_SHARD_AIRBORNE_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BLUEBIRD` | ATTRIBUTE_SHARD_AIRBORNE_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WILD_HOG` | ATTRIBUTE_SHARD_ANIMAL_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HOWLING_SPIRIT` | ATTRIBUTE_SHARD_ANIMAL_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SPRAWL` | ATTRIBUTE_SHARD_ANIMAL_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GIANT_WATER_BUG` | ATTRIBUTE_SHARD_AQUATIC_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DUMPSTER_DIVER` | ATTRIBUTE_SHARD_AQUATIC_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HIDEONWALL` | ATTRIBUTE_SHARD_ARCANE_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BRINELING` | ATTRIBUTE_SHARD_ARCANE_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DUPLICO` | ATTRIBUTE_SHARD_ARCANE_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BLACK_WIDOW` | ATTRIBUTE_SHARD_ARTHROPOD_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_PANGOLIN` | ATTRIBUTE_SHARD_ATOMIZED_WHISPERS;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DRYBARK` | ATTRIBUTE_SHARD_AXE_COOLDOWN;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BLOODBAT` | ATTRIBUTE_SHARD_BARTENDER_DISCOUNT;1 | 未记录 Craft/Forge 配方 |
| `SHARD_AREITA` | ATTRIBUTE_SHARD_BATTLE_ARACHNID;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BADGER` | ATTRIBUTE_SHARD_BATTLE_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_CHEEKY_TIKI` | ATTRIBUTE_SHARD_BAYOU_TREASURE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_KEELED_SLUG` | ATTRIBUTE_SHARD_BONUS_PEST_CHANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MAGGOT` | ATTRIBUTE_SHARD_BOOT_FISHER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SEPIALOT` | ATTRIBUTE_SHARD_BUCKET_GREED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_LITTERBUG` | ATTRIBUTE_SHARD_BUCKLE_FISHER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WOODCHUCKER` | ATTRIBUTE_SHARD_BUILDER_DISCOUNT;1 | 未记录 Craft/Forge 配方 |
| `SHARD_FOLF` | ATTRIBUTE_SHARD_CATACOMBS_CAP;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BONZO` | ATTRIBUTE_SHARD_CATACOMBS_EXPLORER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_ROCKMITE` | ATTRIBUTE_SHARD_CAVERNOUS_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_CAVERNFISH` | ATTRIBUTE_SHARD_CAVE_FISHING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BUNBUN` | ATTRIBUTE_SHARD_CHOCOLATE_SPEED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_PRIMORDIAL` | ATTRIBUTE_SHARD_COCOON_CHANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WUMPA` | ATTRIBUTE_SHARD_COLD_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DUSTYBIT` | ATTRIBUTE_SHARD_COMBAT_TRAP;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BAYOU_SLUDGE` | ATTRIBUTE_SHARD_COMPOST_SPEED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WIKI_TIKI` | ATTRIBUTE_SHARD_CONSTRUCT_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SHRIEKY_TIKI` | ATTRIBUTE_SHARD_CONSTRUCT_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_LAVA_LEECH` | ATTRIBUTE_SHARD_CRIMSON_ESSENCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HEWVER` | ATTRIBUTE_SHARD_CRITTER_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_LOCUST` | ATTRIBUTE_SHARD_CROP_SPEED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HIVETHIEF` | ATTRIBUTE_SHARD_CUBIC_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GEMZIE` | ATTRIBUTE_SHARD_DEVOURING_SPREAD;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GROUNDHOG` | ATTRIBUTE_SHARD_DIURNAL_ANIMAL;1 | 未记录 Craft/Forge 配方 |
| `SHARD_RABBIT_GODMOTHER` | ATTRIBUTE_SHARD_DIVINE_RABBIT_LUCK;1 | 未记录 Craft/Forge 配方 |
| `SHARD_TREASURE_HOARDER` | ATTRIBUTE_SHARD_DWARVEN_TRAINING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GOLDOLOT` | ATTRIBUTE_SHARD_ECHO_OF_BUCKETS;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DOOMSPIRAL` | ATTRIBUTE_SHARD_ECHO_OF_TRACKING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_RABBIT_GODFATHER` | ATTRIBUTE_SHARD_EGG_FINDER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HIDEYHO` | ATTRIBUTE_SHARD_ELUSIVE_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_QUEEN_ANT` | ATTRIBUTE_SHARD_ELUSIVE_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MOSQUITO` | ATTRIBUTE_SHARD_ENCHANTED_FARMER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_TROODON` | ATTRIBUTE_SHARD_ESSENCE_OF_FOSSILS;1 | 未记录 Craft/Forge 配方 |
| `SHARD_PACKRAT_SKULL` | ATTRIBUTE_SHARD_FIESTA_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MITE` | ATTRIBUTE_SHARD_FILTER_UPGRADE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_TORRID` | ATTRIBUTE_SHARD_FIRST_SWEEP;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GIANT_ISOPOD` | ATTRIBUTE_SHARD_FISHERS_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_OSEDAX` | ATTRIBUTE_SHARD_FLEXIBLE_FISHER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_ANTEATER` | ATTRIBUTE_SHARD_FLOOR_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_FLORA` | ATTRIBUTE_SHARD_FLORA;1 | 未记录 Craft/Forge 配方 |
| `SHARD_PARAKEET` | ATTRIBUTE_SHARD_FLYING_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SILKBREEZE` | ATTRIBUTE_SHARD_FORAGERS_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_TREEFROG` | ATTRIBUTE_SHARD_FORAGING_FROG;1 | 未记录 Craft/Forge 配方 |
| `SHARD_FOXTROT` | ATTRIBUTE_SHARD_FORAGING_SPEED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_FLUFFLING` | ATTRIBUTE_SHARD_FORAGING_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WOODPECKER` | ATTRIBUTE_SHARD_FOREST_FELLING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_PUCK` | ATTRIBUTE_SHARD_FOREST_SERENDIPITY;1 | 未记录 Craft/Forge 配方 |
| `SHARD_FLY` | ATTRIBUTE_SHARD_FORTUNATE_FARMER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_FLITTER` | ATTRIBUTE_SHARD_FORTUNATE_MINER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BILLYGOAT` | ATTRIBUTE_SHARD_FROZEN_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_STRONGARM` | ATTRIBUTE_SHARD_FROZEN_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_POLARIS` | ATTRIBUTE_SHARD_FROZEN_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_EMBER` | ATTRIBUTE_SHARD_GALATEA_TRAINING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DIVE_GHAST` | ATTRIBUTE_SHARD_GHASTLY_DISTRACTION;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SCATHA` | ATTRIBUTE_SHARD_GLOSSY_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HIDEONSUN` | ATTRIBUTE_SHARD_GOLD_BOX;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MANTIS_SHRIMP` | ATTRIBUTE_SHARD_GREAT_TREASURE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GIMMIEGOLD` | ATTRIBUTE_SHARD_GREEDY_GOBLIN;1 | 未记录 Craft/Forge 配方 |
| `SHARD_TIMESTALK_CLONE` | ATTRIBUTE_SHARD_GREENHOUSE_SPEED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_VULTURE` | ATTRIBUTE_SHARD_HELIX_SHARPENING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_RABBIT_MAFIOSO` | ATTRIBUTE_SHARD_HITMAN_COOLDOWN;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HONEYBUZZ` | ATTRIBUTE_SHARD_HONEY_HAUL;1 | 未记录 Craft/Forge 配方 |
| `SHARD_POLLENDART` | ATTRIBUTE_SHARD_HONEY_LUCK;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HONEYHOG` | ATTRIBUTE_SHARD_HONEY_SPEED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WETWING` | ATTRIBUTE_SHARD_HUMANOID_RULER_NEW;1 | 未记录 Craft/Forge 配方 |
| `SHARD_TEPID` | ATTRIBUTE_SHARD_LAKE_FISHING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BEEHEEMOTH` | ATTRIBUTE_SHARD_LATHERING_GREED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_RABBIT_CAT` | ATTRIBUTE_SHARD_LEGENDARY_RABBIT_LUCK;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HONEYMITE` | ATTRIBUTE_SHARD_MITE_SPAWNER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_ZOMBUDDY` | ATTRIBUTE_SHARD_MUTATION_SERENDIPITY;1 | 未记录 Craft/Forge 配方 |
| `SHARD_RABBIT_NEIGHBOR` | ATTRIBUTE_SHARD_MYTHIC_RABBIT_LUCK;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MINOS_HUNTER` | ATTRIBUTE_SHARD_MYTHOLOGICAL_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_BLUE_CRAB` | ATTRIBUTE_SHARD_OUTSTANDING_FISHER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MOTH` | ATTRIBUTE_SHARD_PEST_COOLDOWN;1 | 未记录 Craft/Forge 配方 |
| `SHARD_CRICKET` | ATTRIBUTE_SHARD_PEST_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_ABYSSAL_MINER` | ATTRIBUTE_SHARD_PICKAXE_COOLDOWN;1 | 未记录 Craft/Forge 配方 |
| `SHARD_QUEEN_SNAKE` | ATTRIBUTE_SHARD_QUEENLY_ECHO;1 | 未记录 Craft/Forge 配方 |
| `SHARD_ANT` | ATTRIBUTE_SHARD_QUEEN_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_CHOCOBUN` | ATTRIBUTE_SHARD_RABBIT_YOUTH;1 | 未记录 Craft/Forge 配方 |
| `SHARD_STONEWORM` | ATTRIBUTE_SHARD_REFINED_LUCK;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MURKBAT` | ATTRIBUTE_SHARD_REKINDLE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_NILBOG` | ATTRIBUTE_SHARD_ROYAL_RICHES;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SCRAPPY` | ATTRIBUTE_SHARD_SCRAP_CHANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HAGGARD` | ATTRIBUTE_SHARD_SKELETAL_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MURDERWING` | ATTRIBUTE_SHARD_SKY_HIGH;1 | 未记录 Craft/Forge 配方 |
| `SHARD_PARAGON` | ATTRIBUTE_SHARD_SLAYER_DISCOUNT;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WOLVERINE` | ATTRIBUTE_SHARD_SLAYER_PROGRESS;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SNOOZLE` | ATTRIBUTE_SHARD_SLEEPY_SPREAD;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MOUNTAIN_GOAT` | ATTRIBUTE_SHARD_SOCIAL_WISDOM;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SOLSNATCHER` | ATTRIBUTE_SHARD_SOUL_SNATCHER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SPECIAL_ZEALOT` | ATTRIBUTE_SHARD_SPECIAL_UPGRADES;1 | 未记录 Craft/Forge 配方 |
| `SHARD_MACAW` | ATTRIBUTE_SHARD_SPLENDOR;1 | 未记录 Craft/Forge 配方 |
| `SHARD_RAT` | ATTRIBUTE_SHARD_SPRAYONATOR_SERENDIPITY;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SOLAR` | ATTRIBUTE_SHARD_STARLYN_TRAINING;1 | 未记录 Craft/Forge 配方 |
| `SHARD_CHUCKWALLA` | ATTRIBUTE_SHARD_SUBTERRANEAN_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SHYWORM` | ATTRIBUTE_SHARD_SUBTERRANEAN_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DRIFTLING` | ATTRIBUTE_SHARD_SUBTERRANEAN_RULER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_THUNDER` | ATTRIBUTE_SHARD_THUNDER_SPEED;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SNEAKY_TIKI` | ATTRIBUTE_SHARD_TIKI_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WATER_SNAKE` | ATTRIBUTE_SHARD_TITANOBOA_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_TIMIL` | ATTRIBUTE_SHARD_TORRHUS_DIVER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_FIREFOX` | ATTRIBUTE_SHARD_TORRHUS_MASTERY;1 | 未记录 Craft/Forge 配方 |
| `SHARD_STINGRAY` | ATTRIBUTE_SHARD_TORRHUS_SERENDIPITY;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GRIZZLY_BEAR` | ATTRIBUTE_SHARD_TOUGH_CLAWS;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GHOST_CRAB` | ATTRIBUTE_SHARD_TREASURE_FISHER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_NOZZLENOSE` | ATTRIBUTE_SHARD_UNDERWATER_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_WOODLOUSE` | ATTRIBUTE_SHARD_VISITOR_CHEESE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_PARCHED` | ATTRIBUTE_SHARD_VISITOR_COMPOST;1 | 未记录 Craft/Forge 配方 |
| `SHARD_DUNG_BEETLE` | ATTRIBUTE_SHARD_VISITOR_DUNG;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HONEYBUG` | ATTRIBUTE_SHARD_VISITOR_HONEY;1 | 未记录 Craft/Forge 配方 |
| `SHARD_RED_PANDA` | ATTRIBUTE_SHARD_VISITOR_PLANT;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SEA_WITCH` | ATTRIBUTE_SHARD_WITCHS_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_HIDEONFLOOR` | ATTRIBUTE_SHARD_WOODLAND_FORTUNE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_STAG_BEETLE` | ATTRIBUTE_SHARD_WOODLAND_RESISTANCE;1 | 未记录 Craft/Forge 配方 |
| `SHARD_SHUDDERSQUID` | ATTRIBUTE_SHARD_YETI_TRACKER;1 | 未记录 Craft/Forge 配方 |
| `SHARD_GAZER` | ATTRIBUTE_SHARD_ZEALOT_TRACKER;1 | 未记录 Craft/Forge 配方 |

### 兔子（60 个）

| BZ ID | 名称 / NEU ID | 处理 |
| --- | --- | --- |
| `FACTION_RABBIT_ALLEY` | Alley | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_ANCHOR` | Anchor | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_ASTER` | Aster | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_AVALANCHE` | Avalanche | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_CANYON` | Canyon | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_CHASM` | Chasm | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_CLOVER` | Clover | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_COBBLE` | Cobble | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_COCONUT` | Coconut | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_CRAG` | Crag | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_DAISY` | Daisy | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_DUNE` | Dune | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_EAGLE` | Eagle | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_GLACIER` | Glacier | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_GRAFFITI` | Graffiti | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_GRANITE` | Granite | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_HAYBALE` | Haybale | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_HAZEL` | Hazel | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_HORIZON` | Horizon | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_ICEFUR` | Icefur | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_IRIS` | Iris | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_JUNIPER` | Juniper | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_LAGOON` | Lagoon | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_LAVENDER` | Lavender | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_MARIGOLD` | Marigold | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_MAYOR` | Mayor | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_MINISTER` | Minister | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_MISTRAL` | Mistral | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_MOCKTAIL` | Mocktail | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_MOSS` | Moss | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_NECTAR` | Nectar | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_NEON` | Neon | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_OASIS` | Oasis | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_PALM` | Palm | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_PEON` | Peon | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_ROOT` | Root | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_ROSEBUD` | Rosebud | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SANDY` | Sandy | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SCREE` | Scree | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SEABUN` | Seabun | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SEASHELL` | Seashell | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SHORTCUT` | Shortcut | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SILO` | Silo | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SKYRISE` | Skyrise | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SPEEDY` | Speedy | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SPLASH` | Splash | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_STARFISH` | Starfish | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SUBWAY` | Subway | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SUMMIT` | Summit | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SUNSET` | Sunset | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_SURF` | Surf | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_TAN` | Tan | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_TAXI` | Taxi | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_TIMBER` | Timber | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_TRAFFIC` | Traffic | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_TUNDRA` | Tundra | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_TUNNEL` | Tunnel | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_TWIGY` | Twigy | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_VALLEY` | Valley | 未记录 Craft/Forge 配方 |
| `FACTION_RABBIT_WALKER` | Walker | 未记录 Craft/Forge 配方 |

## 新增 AH 物品中未记录 Craft/Forge 配方的清单（57 个）

此处 ID 来自拍卖物品 NBT，不是用显示名模糊推断。宠物按稀有度区分，符文按等级区分；“仅竞拍”表示缓存中没有该 ID 的一口价拍卖。

| NEU ID | 名称 | 缓存拍卖类型 | 其他获取关系 |
| --- | --- | --- | --- |
| `AXE_FADING_BLUE_RUNE;1` | ◆ Fading Blue Rune I | 有一口价 | 未记录 |
| `AXE_FADING_BLUE_RUNE;2` | ◆ Fading Blue Rune II | 有一口价 | 未记录 |
| `AXE_FADING_BLUE_RUNE;3` | ◆ Fading Blue Rune III | 有一口价 | 未记录 |
| `BIOHAZARD_CONTROL` | Hazard Control Skin | 有一口价 | 未记录 |
| `BLACK_CAT_PLUSHIE` | Black Cat Plushie | 有一口价 | 未记录 |
| `BLOOD_MOON_FISH_ORB` | Blood Moon Fishing Deployable Skin | 有一口价 | 未记录 |
| `CANDY_CORN_SUPERIOR_DRAGON` | Candy Corn Superior Dragon Skin | 有一口价 | 未记录 |
| `CRIMSON_SPOOKY` | Spooky Skin | 有一口价 | 未记录 |
| `CROWN_OF_AVARICE_ROYAL` | Grand Royal Skin | 有一口价 | 未记录 |
| `DEAD_MANS_CHESTPLATE` | Dead Man's Chestplate | 有一口价 | 未记录 |
| `DYE_SLUDGE` | Sludge Dye | 有一口价 | 未记录 |
| `DYE_SPIRIT` | Spirit Dye | 有一口价 | 未记录 |
| `GLACITE_GUARDIAN_CYAN` | Cyan Guardian Glacite Helmet Skin | 有一口价 | 未记录 |
| `GLACITE_GUARDIAN_DARK` | Dark Guardian Glacite Helmet Skin | 有一口价 | 未记录 |
| `GLACITE_GUARDIAN_GLACIAL` | Glacial Guardian Glacite Helmet Skin | 有一口价 | 未记录 |
| `GLACITE_GUARDIAN_LIGHT` | Light Guardian Glacite Helmet Skin | 有一口价 | 未记录 |
| `GLACITE_GUARDIAN_PURPLE` | Purple Guardian Glacite Helmet Skin | 有一口价 | 未记录 |
| `GRUNGLE` | Drone Mod: Grungle | 有一口价 | 未记录 |
| `HARVEST_BARN_SKIN` | Harvest Barn Skin | 有一口价 | 未记录 |
| `INFINIPOT` | InfiniPot™ | 有一口价 | 未记录 |
| `MINING_OFF_CAMERA` | Drone Mod: Mining Off Camera | 有一口价 | 未记录 |
| `PET_ITEM_FORAGING_SKILL_BOOST_RARE` | Foraging Exp Boost | 有一口价 | 未记录 |
| `PET_ITEM_FORAGING_SKILL_BOOST_UNCOMMON` | Foraging Exp Boost | 有一口价 | 未记录 |
| `PET_SKIN_AMMONITE_SHELLED` | Shelled Ammonite Skin | 有一口价 | 未记录 |
| `PET_SKIN_ENDER_DRAGON_SMOL` | Smol Ender Dragon Skin | 有一口价 | 未记录 |
| `PET_SKIN_FLYING_FISH_BOWL_MYSTIC` | Mystic Bowl Flying Fish Skin | 有一口价 | 未记录 |
| `PET_SKIN_FLYING_FISH_BOWL_TIDAL` | Tidal Bowl Flying Fish Skin | 有一口价 | 未记录 |
| `PET_SKIN_FROG_BURNING` | Burning Frog Skin | 有一口价 | 未记录 |
| `PET_SKIN_FROG_FOSSIL` | Fossil Frog Skin | 有一口价 | 未记录 |
| `PET_SKIN_FROG_ZOMBIE` | Zombie Frog Skin | 有一口价 | 未记录 |
| `PET_SKIN_GRIFFIN_FAIRY` | Fairy Griffin Skin | 有一口价 | 未记录 |
| `PET_SKIN_MITHRIL_GOLEM_GHOST` | Ghost Mithril Golem Skin | 有一口价 | 未记录 |
| `PET_SKIN_OCELOT_SPARKLING` | Sparkling Ocelot Skin | 有一口价 | 未记录 |
| `PET_SKIN_SEAL_PUP` | Pup Seal Skin | 有一口价 | 未记录 |
| `PET_SKIN_SKELETON_WITHERING` | Withering Skeleton Skin | 有一口价 | 未记录 |
| `PET_SKIN_SLOTH_TUXEDO` | Plushie Tuxedo Sloth Skin | 有一口价 | 未记录 |
| `PHOENIX;7` | [Lvl {LVL}] Phoenix | 有一口价 | 未记录 |
| `PHOENIX;8` | [Lvl {LVL}] Phoenix | 有一口价 | katgrade |
| `POWDER_OF_THE_PEOPLE` | Powder of the People | 有一口价 | 未记录 |
| `PRIMORDIAL_HUNTER` | Hunter Skin | 有一口价 | 未记录 |
| `PUMPKIN_FLUX` | Pumpkin Power Orb Skin | 有一口价 | 未记录 |
| `REFRACTIVE_PAINT_PALETTE` | Refractive Paint Palette | 有一口价 | 未记录 |
| `RUBBER_SNORKEL` | Rubber Snorkel | 有一口价 | 未记录 |
| `SALEM_FIREPLACE` | Salem Fireplace | 有一口价 | 未记录 |
| `SALEM_LARGE_SOFA` | Salem Large Sofa | 仅竞拍 | 未记录 |
| `SALEM_SMALL_SOFA` | Salem Small Sofa | 有一口价 | 未记录 |
| `SCATHA_IN_A_BOTTLE` | Scatha-in-a-Bottle | 有一口价 | 未记录 |
| `SLOTH;0` | [Lvl {LVL}] Sloth | 有一口价 | 未记录 |
| `SLOTH;1` | [Lvl {LVL}] Sloth | 有一口价 | katgrade |
| `SLOTH;4` | [Lvl {LVL}] Sloth | 有一口价 | katgrade |
| `TORRHUS_ARTIFACT` | Torrhus Artifact | 有一口价 | 未记录 |
| `TORRHUS_RING` | Torrhus Ring | 仅竞拍 | 未记录 |
| `TORRHUS_SAFARI_ENTRANCE_TRAVEL_SCROLL` | Travel Scroll to Critter Safari Entrance | 有一口价 | 未记录 |
| `VIAL_OF_SPRING_WATER` | Vial of Spring Water | 有一口价 | 未记录 |
| `WINDING_IVY` | Winding Ivy | 有一口价 | 未记录 |
| `WISP_SPIRIT` | Wisp Spirit Skin | 有一口价 | 未记录 |
| `ZOMBIE_EYE_PERSONALITY` | Zombie Eye Minion Skin | 有一口价 | 未记录 |

其中包括 `POWDER_OF_THE_PEOPLE`、`TORRHUS_RING`、`TORRHUS_ARTIFACT`、`SCATHA_IN_A_BOTTLE` 等。未根据名称、物品系列或相似材料推测配方。

## 同步范围与使用

两份源码目录的 Craft、Forge、Enchant 配方及 Craft 附魔书 ID 转换代码已同步。当前有效普通 Craft 配方为 2,504 个、Forge 为 124 个、Enchant 为 540 个成品等级（1,582 个合并方式）。Craft 文件夹还保存 NEU 的无配方物品元数据，因此 JSON 文件数不等于配方数。

BZ/AH 本身直接显示 API 请求到的市场数据，不需要另加物品白名单。此次没有复制用户配置、API Key 或市场缓存到 Git 源码目录，也没有重新打包 EXE；打包版需要重新生成后才能包含新代码和全部新配方。
