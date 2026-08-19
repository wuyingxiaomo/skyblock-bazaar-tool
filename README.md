# SkyBlock Bazaar Tool 3.4

Hypixel SkyBlock 市场分析工具，包含 Bazaar、Craft、Forge 和 Enchant 四个页面。

## 主要功能

- 打包版使用统一的 `bazaar.exe` 入口，通过页面按钮切换 Bazaar、Craft、Forge 和 Enchant
- 后台独立请求 Bazaar 和 Auction House 数据，切换页面不会中断请求
- Bazaar 价格、挂单量、成交量和 7 日成交量分析
- Craft 合成利润、材料成本和材料可制作数量计算
- Forge 锻造时间、小时利润和材料可制作数量计算
- Enchant 附魔书等级、铁砧升级配方和罗马数字显示
- 参数面板实时筛选、单位转换、列显示、列宽和列顺序调整
- 本地快捷键和 Windows 全局快捷键
- 所有顶部按钮都可以设置快捷键，快捷键窗口支持重置全部
- Forge 页面支持窗口置顶和完整快捷键设置
- 快捷键捕获支持单键、修饰键组合以及 `V+B` 等普通按键组合
- 记事本式物品 ID 搜索，支持向上、向下、循环和查找下一个
- 配置、缓存和请求状态保存在 exe 所在目录的 `bazaar_config` 文件夹

## v3.4 更新

- 修正 Bazaar 收购价和出售价方向：收购价使用 Hypixel Bazaar API 的 `sellPrice`，出售价使用 `buyPrice`。
- 修正 Bazaar 总成交量和 7 日成交量方向：立即收购对应 API 的 `sellVolume` / `sellMovingWeek`，立即出售对应 `buyVolume` / `buyMovingWeek`。
- 修正单件差价和利润率：单件差价为 `出售价 - 收购价`，单件利润率为 `(出售价 - 收购价) / 收购价 × 100%`。
- Craft、Forge 和 Enchant 的材料成本、利润和利润率同步使用修正后的 Bazaar 价格。
- 新增 `搜索` 按钮，默认快捷键为 `Ctrl+F`。搜索窗口按记事本式方式在当前表格中定位物品，不会修改当前筛选结果。
- 搜索支持向上、向下、循环查找、查找下一个和 Enter 键查找；匹配行会自动选中并滚动到可见位置。
- 搜索窗口显示“查找物品ID”，关闭时会保存窗口位置；Bazaar、Craft、Forge、Enchant 都支持。

## 页面切换和数据刷新

四个页面顶部都有相同的主要操作：

- `刷新全部数据`：请求 Bazaar 和 Auction House
- `刷新BZ数据`：只请求 Bazaar
- `刷新AH数据`：只请求 Auction House
- `参数设置面板`：打开当前页面的筛选和显示设置
- `保存当前设置`：保存当前页面的窗口、列、按钮、筛选和快捷键设置
- `加载保存设置`：读取之前保存的设置
- `重置全部默认`：恢复当前页面的默认设置
- `搜索`：查找当前表格中的物品 ID，默认快捷键为 `Ctrl+F`
- `窗口置顶`：切换窗口置顶状态
- `快捷键设置`：设置局部快捷键或 Windows 全局快捷键
- `输入api（可选）`：保存可选的 Hypixel API Key

使用打包版时，点击页面切换按钮会关闭当前窗口并启动同一个 `bazaar.exe` 的对应页面；运行源码时会启动对应的 Python 页面文件。后台市场请求使用独立 worker，因此切换页面不会取消正在进行的请求。

## 价格与利润计算

Hypixel Bazaar API 的字段名称以即时成交方向命名，工具中的显示含义如下：

- `sellPrice`：玩家创建收购订单时的价格，对应工具中的“收购价”。
- `buyPrice`：玩家创建出售订单时的价格，对应工具中的“出售价”。
- 收购成交量和 7 日收购成交量：使用 API 的 `sellVolume`、`sellMovingWeek`，即玩家立即收购时成交的出售挂单量。
- 出售成交量和 7 日出售成交量：使用 API 的 `buyVolume`、`buyMovingWeek`，即玩家立即出售时成交的收购挂单量。
- 单件差价：`出售价 - 收购价`。
- 单件利润率：`(出售价 - 收购价) / 收购价 × 100%`。

Craft、Forge 和 Enchant 中四种利润均使用“成品价格 - 对应材料总成本”计算；利润率以对应材料总成本为分母。

## 搜索

- 点击顶部 `搜索` 按钮或按 `Ctrl+F` 打开搜索窗口。
- 输入物品 ID 的全部或部分内容即可查找，空格会按下划线处理。
- 可选择“向上”或“向下”，并可勾选“循环查找”。
- 点击 `查找下一个` 或按 Enter 会选中下一条匹配行，并自动滚动到该行。
- 点击 `关闭` 或窗口右上角关闭会保存搜索窗口位置。

## 参数面板

参数面板由显示列、筛选条件、单位和数据源设置组成。

### 通用设置

- 每一列都有显示/隐藏勾选框。
- 数值列可以填写最小值和最大值。
- 支持 `默认`、`k`、`m`、`b` 单位，例如 `10k`、`2.5m`。
- 文字列会显示“不支持数值筛选”。
- Bazaar、Craft、Forge 可以分别勾选 `Bazaar` 和 `Auction House` 数据源。
- 勾选数据源后，主界面会实时重新筛选；两个数据源都不勾选时不会显示依赖这些数据的行。
- 参数面板中的表格支持横向、纵向滚动和拖动列宽。
- 参数面板表头右键可以选择“左移此列”或“右移此列”。
- `应用筛选并关闭` 会保留本次修改并关闭面板。
- `仅关闭` 会放弃本次面板修改，恢复打开面板前的状态。

### Bazaar 参数列

- 物品ID
- 收购价、出售价、单件差价、单件利润率%
- 收购挂单量、出售挂单量
- 总收购成交量、总出售成交量
- 7日收购成交量、7日出售成交量

### Craft 参数列

- 物品ID、物品收购价、物品出售价、AH最低一口价
- 合成配方的材料
- 材料收购价、材料出售价
- 收购价-材料收购、收购价-材料出售
- 出售价-材料收购、出售价-材料出售
- 四种对应利润率
- 物品收购/出售挂单量
- 物品总收购/出售成交量
- 物品7日收购/出售成交量
- 材料收购/出售订单合计
- 材料总收购/出售量合计
- 材料7日收购/出售量合计
- 按材料收购量、出售量和 7 日成交量计算的可制作数量

Craft 的多材料配方会按每种材料的数量计算总成本。材料可制作数量按各材料可供应数量除以配方需求量后取最小值，避免只根据某一种材料高库存做出错误判断。

### Forge 参数列

- 物品ID、物品收购价、物品出售价、AH最低一口价
- Forge 配方材料、材料收购价、材料出售价
- 收购价/出售价分别与材料收购/出售组合的四种利润
- 上述四种利润对应的利润率
- 上述四种利润对应的小时利润
- 锻造时间
- 物品和材料的挂单量、总成交量、7日成交量
- 材料可制作数量

Forge 的小时利润会将一次锻造利润除以锻造所需小时数。

### Enchant 参数列

- 附魔名称，不包含等级，例如 `ENCHANTMENT_LOOTING`
- 等级，使用 Minecraft 风格罗马数字，例如 `V`
- 合成配方材料，显示材料等级和数量，例如 `II x 2`
- 物品收购价、物品出售价
- 材料收购价、材料出售价
- 收购价/出售价与材料收购/出售组合的四种利润和利润率
- 物品和材料的挂单量、总成交量、7日成交量

Enchant 页面只使用 Bazaar 数据。每种附魔等级的不同合成方式分开显示，例如一个等级 III 附魔书可能分别显示“等级 II x 2”和“等级 I x 4”两行，并分别计算成本和利润。

## 表格和按钮操作

- 点击表头：按该列排序，再次点击切换升序/降序。
- 拖动表头边界：实时调整列宽。
- 主表格表头右键：显示“左移此列”和“右移此列”。列顺序会同步到当前页面的参数面板。
- 主表格数据行右键：复制该行物品 ID 到剪贴板。
- 顶部按钮右键：显示“左移此按钮”和“右移此按钮”。
- 主界面和参数面板共用列顺序；保存设置后，下次加载会恢复列宽和顺序。

## 配方来源

- Craft 和 Forge 配方来自 [NotEnoughUpdates-REPO items](https://github.com/NotEnoughUpdates/NotEnoughUpdates-REPO/tree/master/items)。
- Enchant 配方根据 Hypixel SkyBlock Wiki 和游戏规则手动整理。
- Enchant 附魔书数量较多，部分等级或配方可能存在错误，欢迎提交修正。

配方目录：

```text
craft_recipe\
forge_recipe\
enchanted_book_recipe\
```

正常运行不需要 NotEnoughUpdates 原始仓库。重新生成附魔书配方时，将该仓库放在项目根目录，然后运行：

```powershell
python generate_enchanted_book_recipes.py
```

## 安装和运行源码

需要 Windows、Python 3.9+、Tkinter 和网络连接：

```powershell
python -m pip install -r requirements.txt
python bazaar.py
```

## 打包版

目录版和单文件版都使用同一个 `bazaar.exe` 入口：

```text
bazaar\bazaar.exe
bazaar_onefile\bazaar.exe
```

目录版需要保留同目录的 `_internal` 文件夹；单文件版只需要 `bazaar.exe`。首次运行会在 exe 所在目录创建 `bazaar_config` 文件夹。

## API Key 和本地数据

Bazaar 公共接口通常可以不使用 API Key。API Key、页面设置和市场缓存都会保存在：

```text
bazaar_config\
  bazaar_config.json
  craft_config.json
  forge_config.json
  enchant_config.json
  bazaar_data.json
  auction_data.json
```

不要将 API Key、配置文件、Bazaar/AH 数据缓存、运行状态或构建目录提交到 GitHub。

当前版本：3.4
