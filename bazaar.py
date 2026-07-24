import requests
import tkinter as tk
from tkinter import ttk
import json
import os
import ctypes
import ctypes.wintypes
import threading

# ===================== 配置区 =====================
BAZAAR_URL = "https://api.hypixel.net/skyblock/bazaar"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/150.0.0.0"
}
CONFIG_FILE = "config.json"
DATA_CACHE_FILE = "bazaar_data.json"
HYPIXEL_API_KEY = ""

def prompt_api_key(parent=None, msg="", current_key=""):
    """弹出输入API Key的对话框，返回用户输入的key（空字符串表示取消）"""
    dlg = tk.Toplevel(parent) if parent else tk.Tk()
    dlg.title("请输入 API Key")
    dlg.resizable(False, False)
    dlg.attributes("-topmost", True)
    result = [None]
    def on_ok():
        key = entry.get().strip()
        result[0] = key  # 允许保存空值
        dlg.destroy()
    def on_cancel():
        dlg.destroy()
    tk.Label(dlg, text="请输入 Hypixel API Key：", font=("", 12)).pack(padx=20, pady=(15,5))
    entry = tk.Entry(dlg, width=50, font=("", 11))
    entry.insert(0, current_key)
    entry.pack(padx=20, pady=5)
    entry.focus_set()
    if msg:
        tk.Label(dlg, text=msg, fg="red", font=("", 10)).pack(padx=20, pady=2)
    tk.Label(dlg, text="⚠ 请勿泄露自己的 API Key！！！", fg="red", font=("", 12, "bold")).pack(padx=20, pady=(5,2))
    btn_frame = tk.Frame(dlg)
    btn_frame.pack(pady=(5,15))
    tk.Button(btn_frame, text="确认", command=on_ok, width=10, font=("", 11)).pack(side="left", padx=8)
    tk.Button(btn_frame, text="取消", command=on_cancel, width=10, font=("", 11)).pack(side="left", padx=8)
    entry.bind("<Return>", lambda e: on_ok())
    dlg.protocol("WM_DELETE_WINDOW", on_cancel)
    if parent:
        dlg.transient(parent)
        dlg.grab_set()
    # 居中显示
    dlg.update_idletasks()
    w, h = dlg.winfo_width(), dlg.winfo_height()
    x = (dlg.winfo_screenwidth() - w) // 2
    y = (dlg.winfo_screenheight() - h) // 2
    dlg.geometry(f"+{x}+{y}")
    if parent:
        dlg.wait_window()
    else:
        dlg.mainloop()
    return result[0]

def save_api_key(key):
    """将 API Key 保存到 config.json（不覆盖其他字段）"""
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            pass
    cfg["api_key"] = key
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_api_key():
    """从 config.json 读取 API Key"""
    global HYPIXEL_API_KEY
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("api_key"):
                HYPIXEL_API_KEY = cfg["api_key"]
                return
        except:
            pass

def open_api_dialog():
    """打开 API Key 输入弹窗"""
    global HYPIXEL_API_KEY
    was_topmost = root.attributes("-topmost")
    root.attributes("-topmost", False)
    key = prompt_api_key(root, current_key=HYPIXEL_API_KEY)
    if was_topmost:
        root.attributes("-topmost", True)
        root.lift()
    if key is not None:  # None = 取消，空字符串 = 确认清空
        HYPIXEL_API_KEY = key
        save_api_key(key)
        status_var.set("API Key 已保存" if key else "API Key 已清空")

# ==================================================

# 全局状态
sort_key = "pct"
sort_reverse = True
item_data_cache = []
is_topmost = False

# 单位换算
UNIT_SCALE = {
    "默认": 1,
    "k": 1000,
    "m": 1000000,
    "b": 1000000000
}

# 全部API字段元数据
col_meta = [
    {"cid": "name", "name": "物品ID", "is_num": False},
    {"cid": "buy", "name": "收购价", "is_num": True},
    {"cid": "sell", "name": "出售价", "is_num": True},
    {"cid": "margin", "name": "单件差价", "is_num": True},
    {"cid": "pct", "name": "单件利润率%", "is_num": True},
    {"cid": "buyOrders", "name": "收购挂单量", "is_num": True},
    {"cid": "sellOrders", "name": "出售挂单量", "is_num": True},
    {"cid": "vol_buy", "name": "总收购成交量", "is_num": True},
    {"cid": "vol_sell", "name": "总出售成交量", "is_num": True},
    {"cid": "week_buy", "name": "7日收购成交量", "is_num": True},
    {"cid": "week_sell", "name": "7日出售成交量", "is_num": True},
]
col_info = []
col_cid_list = [x["cid"] for x in col_meta]
col_name_map = {x["cid"]: x["name"] for x in col_meta}
col_isnum_map = {x["cid"]: x["is_num"] for x in col_meta}

# 控件存储容器
col_var_map = {}
filter_min_map = {}       # 参数面板中的 Entry 控件（仅面板打开时有效）
filter_max_map = {}       # 参数面板中的 Entry 控件（仅面板打开时有效）
unit_combo_map = {}       # 参数面板中的 Combobox 控件（仅面板打开时有效）
filter_min_var_map = {}   # 筛选最低值 StringVar（持久化，与控件无关）
filter_max_var_map = {}   # 筛选最高值 StringVar（持久化，与控件无关）
unit_var_map = {}         # 单位选择 StringVar（持久化，与控件无关）
col_order = []            # 列排列顺序（持久化，可拖拽重排）
col_width_map = {}        # 列宽度（持久化，拖拽调整后保存）
setting_win_geometry = None  # 参数面板位置大小（持久化）
pw_sash_positions = None    # 参数面板三栏分隔位置（持久化）
panel_scroll = {}           # 参数面板三栏滚动位置（持久化）
tree_scroll_x = 0           # 主表格横向滚动位置（持久化）
tree_scroll_y = 0           # 主表格纵向滚动位置（持久化）
btn_order = []              # 顶部按钮排列顺序（持久化）
shortcut_map = {}           # 按钮快捷键映射（持久化）{"refresh": "SHIFT+F3", ...}
shortcut_global = {}        # 快捷键是否全局（持久化）{"refresh": True, ...}
shortcut_win_geometry = None  # 快捷键设置窗口位置大小（持久化）
_prev_shortcut_map = {}     # 上一次绑定的快捷键（用于清除旧绑定）
setting_win = None
inner_check = None
inner_filter = None
inner_unit = None
canvas_check = None
canvas_filter = None
canvas_unit = None

# 数值解析工具（完整保留k/K/m/M/b/B大小写识别，无任何修改）
def parse_num(s: str) -> float:
    s = s.strip().upper()
    if not s:
        return -9999999999
    if s.endswith("K"):
        return float(s[:-1]) * 1000
    elif s.endswith("M"):
        return float(s[:-1]) * 1000000
    elif s.endswith("B"):
        return float(s[:-1]) * 1000000000
    else:
        try:
            return float(s)
        except:
            return -9999999999

def parse_max_num(s: str) -> float:
    s = s.strip().upper()
    if not s:
        return 99999999999
    if s.endswith("K"):
        return float(s[:-1]) * 1000
    elif s.endswith("M"):
        return float(s[:-1]) * 1000000
    elif s.endswith("B"):
        return float(s[:-1]) * 1000000000
    else:
        try:
            return float(s)
        except:
            return 99999999999

def format_value(val: float, unit: str) -> str:
    scale = UNIT_SCALE[unit]
    converted = val / scale
    return f"{round(converted, 2)}"

# 请求API
def fetch_data():
    global HYPIXEL_API_KEY
    params = {}
    if HYPIXEL_API_KEY:
        params["key"] = HYPIXEL_API_KEY
    try:
        res = requests.get(BAZAAR_URL, headers=HEADERS, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        if not data["success"]:
            return [], f"API错误：{data.get('cause', '未知原因')}"
        products = data["products"]
    except requests.exceptions.HTTPError as e:
        return [], f"网络请求失败：{str(e)}"
    except Exception as e:
        return [], f"网络请求失败：{str(e)}"

    item_list = []
    for item_id, info in products.items():
        q = info["quick_status"]
        buy_price = q["buyPrice"]
        sell_price = q["sellPrice"]
        buy_orders = q["buyOrders"]
        sell_orders = q["sellOrders"]
        vol_buy = q["buyVolume"]
        vol_sell = q["sellVolume"]
        week_buy = q["buyMovingWeek"]
        week_sell = q["sellMovingWeek"]

        margin = buy_price - sell_price if buy_price > 0 else 0
        pct = (margin / sell_price) * 100 if sell_price > 0 else 0

        item_list.append({
            "name": item_id,
            "buy": buy_price,
            "sell": sell_price,
            "margin": margin,
            "pct": round(pct, 2),
            "buyOrders": buy_orders,
            "sellOrders": sell_orders,
            "vol_buy": vol_buy,
            "vol_sell": vol_sell,
            "week_buy": week_buy,
            "week_sell": week_sell,
        })
    return item_list, "success"

# 筛选逻辑（跳过物品ID，输入纯数字由单位决定量级）
def filter_data(raw_list):
    cond_list = []
    for meta in col_meta:
        cid = meta["cid"]
        if not meta["is_num"]:
            continue
        unit = unit_var_map[cid].get()
        scale = UNIT_SCALE.get(unit, 1)
        min_str = filter_min_var_map[cid].get().strip()
        max_str = filter_max_var_map[cid].get().strip()
        try:
            min_val = float(min_str) * scale if min_str else -9999999999
        except ValueError:
            min_val = -9999999999
        try:
            max_val = float(max_str) * scale if max_str else 99999999999
        except ValueError:
            max_val = 99999999999
        def cond(r, c=cid, mi=min_val, ma=max_val):
            return r[c] >= mi and r[c] <= ma
        cond_list.append(cond)
    filtered = []
    for row in raw_list:
        ok = True
        for cond in cond_list:
            if not cond(row):
                ok = False
                break
        if ok:
            filtered.append(row)
    return filtered

def refresh_table():
    global item_data_cache
    tree.delete(*tree.get_children())
    status_var.set("正在请求数据...")
    root.update_idletasks()
    data, msg = fetch_data()
    if msg != "success":
        status_var.set(msg)
        return
    item_data_cache = data
    # 保存数据到本地缓存文件
    try:
        with open(DATA_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        status_var.set(f"数据缓存保存失败：{e}")
    apply_filter_sort()
    status_var.set(f"原始共{len(data)}条，筛选后{len(tree.get_children())}条（已更新缓存）")

def load_cached_data():
    """启动时加载本地缓存数据，若无缓存则返回空列表"""
    if not os.path.exists(DATA_CACHE_FILE):
        return []
    try:
        with open(DATA_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except:
        return []

def get_visible_cols():
    vis = []
    for cid in col_order:
        if col_var_map[cid].get():
            vis.append(cid)
    return vis

def apply_filter_sort():
    global item_data_cache, sort_key, sort_reverse
    # 先保存当前列宽（用户可能已拖拽调整），仅在树有数据时保存，避免空树默认宽度覆盖已加载的值
    if len(tree.get_children()) > 0:
        for cid in col_width_map:
            try:
                col_width_map[cid] = tree.column(cid, "width")
            except tk.TclError:
                pass
    filtered = filter_data(item_data_cache)
    filtered.sort(key=lambda x: x[sort_key], reverse=sort_reverse)
    tree.delete(*tree.get_children())
    unit_cache = {}
    for cid in unit_var_map:
        unit_cache[cid] = unit_var_map[cid].get()
    visible_cols = get_visible_cols()
    tree["columns"] = visible_cols
    for row in filtered:
        disp = {"name": row["name"]}
        for meta in col_meta:
            cid = meta["cid"]
            if cid == "name":
                continue
            val = row[cid]
            if meta["is_num"]:
                disp[cid] = format_value(val, unit_cache[cid])
            else:
                disp[cid] = val
        tree.insert("", tk.END, values=[disp[c] for c in visible_cols])
    arrow = " ↓" if sort_reverse else " ↑"
    for cid in visible_cols:
        txt = col_name_map[cid]
        if col_isnum_map[cid]:
            txt += f"({unit_cache[cid]})"
        if cid == sort_key:
            txt += arrow
        tree.heading(cid, text=txt, command=lambda c=cid: on_header_click(c))
        tree.column(cid, width=col_width_map.get(cid, 95), minwidth=50, stretch=False)

def on_header_click(col):
    global sort_key, sort_reverse
    if col == sort_key:
        sort_reverse = not sort_reverse
    else:
        sort_key = col
        sort_reverse = True
    apply_filter_sort()

def on_unit_change(event):
    if item_data_cache:
        apply_filter_sort()

# 鼠标滚轮绑定工具
def _bind_mousewheel(widget, canvas):
    def _on_enter(e):
        canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1*(ev.delta/120)), "units"))
    def _on_leave(e):
        canvas.unbind_all("<MouseWheel>")
    widget.bind("<Enter>", _on_enter)
    widget.bind("<Leave>", _on_leave)

# 刷新三栏滚动边界
def refresh_all_scrollregion():
    canvas_check.configure(scrollregion=canvas_check.bbox("all"))
    canvas_filter.configure(scrollregion=canvas_filter.bbox("all"))
    canvas_unit.configure(scrollregion=canvas_unit.bbox("all"))

# ===================== 参数设置面板（可拖拽调整三栏宽度） =====================
def open_param_panel():
    global setting_win, inner_check, inner_filter, inner_unit, canvas_check, canvas_filter, canvas_unit
    if setting_win and setting_win.winfo_exists():
        setting_win.lift()
        return
    setting_win = tk.Toplevel(root)
    setting_win.title("参数设置面板")
    # 恢复上次面板位置大小
    if setting_win_geometry:
        setting_win.geometry(setting_win_geometry)
    else:
        setting_win.geometry("800x800")
    setting_win.transient(root)
    setting_win.grab_set()

    def on_setting_close():
        global setting_win_geometry, pw_sash_positions, panel_scroll
        try:
            setting_win_geometry = setting_win.geometry()
        except:
            pass
        try:
            pw_sash_positions = [pw.sashpos(i) for i in range(2)]
        except:
            pass
        # 保存三栏滚动位置
        try:
            panel_scroll = {
                "check_x": canvas_check.xview()[0],
                "check_y": canvas_check.yview()[0],
                "filter_x": canvas_filter.xview()[0],
                "filter_y": canvas_filter.yview()[0],
                "unit_x": canvas_unit.xview()[0],
                "unit_y": canvas_unit.yview()[0],
            }
        except:
            pass
        save_panel_config()
        setting_win.destroy()

    # 使用 PanedWindow 实现可拖拽调整三栏宽度
    pw = ttk.PanedWindow(setting_win, orient=tk.HORIZONTAL)
    pw.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 左侧 显示列勾选
    frame_check = ttk.LabelFrame(pw, text="显示列勾选")
    pw.add(frame_check, weight=1)
    canvas_check = tk.Canvas(frame_check)
    scroll_check_y = ttk.Scrollbar(frame_check, orient="vertical", command=canvas_check.yview)
    scroll_check_x = ttk.Scrollbar(frame_check, orient="horizontal", command=canvas_check.xview)
    inner_check = ttk.Frame(canvas_check)
    inner_check.bind("<Configure>", lambda e: canvas_check.configure(scrollregion=canvas_check.bbox("all")))
    canvas_check.window_id = canvas_check.create_window((0,0), window=inner_check, anchor="nw")
    canvas_check.configure(yscrollcommand=scroll_check_y.set, xscrollcommand=scroll_check_x.set)
    scroll_check_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_check_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_check.pack(side="left", fill="both", expand=True)
    _bind_mousewheel(frame_check, canvas_check)

    # 中间 数值筛选
    frame_filter = ttk.LabelFrame(pw, text="数值筛选（最低 / 最高）")
    pw.add(frame_filter, weight=3)
    canvas_filter = tk.Canvas(frame_filter)
    scroll_filter_y = ttk.Scrollbar(frame_filter, orient="vertical", command=canvas_filter.yview)
    scroll_filter_x = ttk.Scrollbar(frame_filter, orient="horizontal", command=canvas_filter.xview)
    inner_filter = ttk.Frame(canvas_filter)
    inner_filter.bind("<Configure>", lambda e: canvas_filter.configure(scrollregion=canvas_filter.bbox("all")))
    canvas_filter.window_id = canvas_filter.create_window((0,0), window=inner_filter, anchor="nw")
    canvas_filter.configure(yscrollcommand=scroll_filter_y.set, xscrollcommand=scroll_filter_x.set)
    scroll_filter_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_filter_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_filter.pack(side="left", fill="both", expand=True)
    _bind_mousewheel(frame_filter, canvas_filter)
    inner_filter.columnconfigure(0, weight=1)
    inner_filter.columnconfigure(1, weight=1)
    inner_filter.columnconfigure(2, weight=1)

    # 右侧 单位切换
    frame_unit = ttk.LabelFrame(pw, text="单位切换")
    pw.add(frame_unit, weight=1)
    canvas_unit = tk.Canvas(frame_unit)
    scroll_unit_y = ttk.Scrollbar(frame_unit, orient="vertical", command=canvas_unit.yview)
    scroll_unit_x = ttk.Scrollbar(frame_unit, orient="horizontal", command=canvas_unit.xview)
    inner_unit = ttk.Frame(canvas_unit)
    inner_unit.bind("<Configure>", lambda e: canvas_unit.configure(scrollregion=canvas_unit.bbox("all")))
    canvas_unit.window_id = canvas_unit.create_window((0,0), window=inner_unit, anchor="nw")
    canvas_unit.configure(yscrollcommand=scroll_unit_y.set, xscrollcommand=scroll_unit_x.set)
    scroll_unit_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_unit_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_unit.pack(side="left", fill="both", expand=True)
    _bind_mousewheel(frame_unit, canvas_unit)

    def sync_visible_widgets():
        row_idx = 0
        for meta in col_meta:
            cid = meta["cid"]
            min_e = filter_min_map[cid]
            max_e = filter_max_map[cid]
            uni_cbx = unit_combo_map[cid]
            lbl = min_e.lbl_ref
            # 物品ID永久隐藏筛选、单位控件
            if not meta["is_num"]:
                lbl.grid_forget()
                min_e.grid_forget()
                max_e.grid_forget()
                uni_cbx.grid_forget()
                continue
            # 筛选和单位控件始终显示，不受勾选状态影响
            lbl.grid(row=row_idx, column=0, sticky="ew", pady=8, padx=2)
            min_e.grid(row=row_idx, column=1, sticky="ew", pady=8, padx=3)
            max_e.grid(row=row_idx, column=2, sticky="ew", pady=8, padx=3)
            uni_cbx.grid(row=row_idx, column=0, sticky="ew", pady=8, padx=2)
            row_idx += 1
        refresh_all_scrollregion()
        apply_filter_sort()

    unit_opt = ["默认", "k", "m", "b"]
    col_info.clear()
    for idx, meta in enumerate(col_meta):
        cid = meta["cid"]
        name = meta["name"]
        isnum = meta["is_num"]
        var = col_var_map[cid]
        # 左侧勾选框
        ck = ttk.Checkbutton(inner_check, text=name, variable=var, command=sync_visible_widgets)
        ck.pack(anchor="w", pady=4)
        col_info.append((cid, name, var, ck))
        # 筛选标签、自适应宽度输入框（绑定 StringVar）
        lbl = ttk.Label(inner_filter, text=name)
        min_entry = ttk.Entry(inner_filter, textvariable=filter_min_var_map[cid])
        max_entry = ttk.Entry(inner_filter, textvariable=filter_max_var_map[cid])
        min_entry.lbl_ref = lbl
        filter_min_map[cid] = min_entry
        filter_max_map[cid] = max_entry
        # 单位下拉自适应宽度（绑定 StringVar）
        cbx = ttk.Combobox(inner_unit, values=unit_opt, state="readonly", textvariable=unit_var_map[cid])
        cbx.bind("<<ComboboxSelected>>", on_unit_change)
        unit_combo_map[cid] = cbx

    # 底部按钮
    btn_frame = ttk.Frame(setting_win)
    btn_frame.pack(pady=12)
    ttk.Button(btn_frame, text="应用筛选并关闭", command=lambda: (apply_filter_sort(), on_setting_close())).pack(side="left", padx=8)
    ttk.Button(btn_frame, text="仅关闭", command=on_setting_close).pack(side="left", padx=8)

    sync_visible_widgets()

    # 延迟恢复三栏分隔位置和滚动位置（等待窗口渲染完成）
    def _restore_panel_layout():
        try:
            if pw_sash_positions:
                for i, pos in enumerate(pw_sash_positions):
                    pw.sashpos(i, pos)
        except:
            pass
        try:
            if panel_scroll:
                if "check_x" in panel_scroll:
                    canvas_check.xview_moveto(panel_scroll["check_x"])
                if "check_y" in panel_scroll:
                    canvas_check.yview_moveto(panel_scroll["check_y"])
                if "filter_x" in panel_scroll:
                    canvas_filter.xview_moveto(panel_scroll["filter_x"])
                if "filter_y" in panel_scroll:
                    canvas_filter.yview_moveto(panel_scroll["filter_y"])
                if "unit_x" in panel_scroll:
                    canvas_unit.xview_moveto(panel_scroll["unit_x"])
                if "unit_y" in panel_scroll:
                    canvas_unit.yview_moveto(panel_scroll["unit_y"])
        except:
            pass
    setting_win.after(200, _restore_panel_layout)

# ===================== 配置保存/加载/重置 =====================
def save_panel_config():
    """关闭参数面板时自动保存面板相关配置（列勾选、筛选、单位、面板布局）"""
    global setting_win_geometry, pw_sash_positions
    # 读取已有配置（保留其他字段如窗口位置、排序等）
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            pass
    # 只更新面板相关字段
    cfg["columns"] = {}
    cfg["filter_min"] = {}
    cfg["filter_max"] = {}
    cfg["units"] = {}
    cfg["setting_win_geometry"] = setting_win_geometry
    cfg["pw_sash_positions"] = pw_sash_positions
    cfg["panel_scroll"] = panel_scroll
    cfg["btn_order"] = btn_order
    cfg["shortcut_map"] = dict(shortcut_map)
    cfg["shortcut_global"] = dict(shortcut_global)
    cfg["shortcut_win_geometry"] = shortcut_win_geometry
    for cid in col_cid_list:
        cfg["columns"][cid] = col_var_map[cid].get()
        cfg["filter_min"][cid] = filter_min_var_map[cid].get()
        cfg["filter_max"][cid] = filter_max_var_map[cid].get()
        cfg["units"][cid] = unit_var_map[cid].get()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        status_var.set("参数面板配置已自动保存")
    except Exception as e:
        status_var.set(f"面板配置保存失败：{e}")

def save_config():
    global sort_key, sort_reverse, tree_scroll_x, tree_scroll_y
    # 保存当前列宽（只读取树中可见列的宽度，不可见列保留原值）
    if len(tree.get_children()) > 0:
        for cid in col_width_map:
            try:
                col_width_map[cid] = tree.column(cid, "width")
            except tk.TclError:
                pass
    try:
        tree_scroll_x = tree.xview()[0]
        tree_scroll_y = tree.yview()[0]
    except:
        pass
    win_w, win_h = root.winfo_width(), root.winfo_height()
    x, y = root.winfo_x(), root.winfo_y()
    try:
        top_scroll_pos = top_canvas.xview()[0]
    except:
        top_scroll_pos = 0
    cfg = {
        "window": {"w": win_w, "h": win_h, "x": x, "y": y},
        "sort": {"key": sort_key, "reverse": sort_reverse},
        "col_order": col_order,
        "btn_order": btn_order,
        "shortcut_map": dict(shortcut_map),
        "shortcut_global": dict(shortcut_global),
        "shortcut_win_geometry": shortcut_win_geometry,
        "is_topmost": is_topmost,
        "setting_win_geometry": setting_win_geometry,
        "pw_sash_positions": pw_sash_positions,
        "panel_scroll": panel_scroll,
        "top_scroll_pos": top_scroll_pos,
        "tree_scroll_x": tree_scroll_x,
        "tree_scroll_y": tree_scroll_y,
        "columns": {},
        "filter_min": {},
        "filter_max": {},
        "units": {},
        "col_widths": dict(col_width_map)
    }
    for cid in col_cid_list:
        cfg["columns"][cid] = col_var_map[cid].get()
        cfg["filter_min"][cid] = filter_min_var_map[cid].get()
        cfg["filter_max"][cid] = filter_max_var_map[cid].get()
        cfg["units"][cid] = unit_var_map[cid].get()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    status_var.set("配置已保存到 config.json")

def load_config():
    global sort_key, sort_reverse, col_order, setting_win_geometry, is_topmost, pw_sash_positions, panel_scroll
    global tree_scroll_x, tree_scroll_y
    if not os.path.exists(CONFIG_FILE):
        status_var.set("无保存配置文件")
        return
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        root.geometry(f"{cfg['window']['w']}x{cfg['window']['h']}+{cfg['window']['x']}+{cfg['window']['y']}")
        sort_key = cfg["sort"]["key"]
        sort_reverse = cfg["sort"]["reverse"]
        # 加载列顺序（兼容旧配置）
        if "col_order" in cfg:
            col_order[:] = cfg["col_order"]
        # 加载按钮顺序（自动补全新增的按钮）
        if "btn_order" in cfg:
            btn_order[:] = cfg["btn_order"]
            # 补全旧配置中缺失的新按钮
            for bid in _default_btn_order:
                if bid not in btn_order:
                    # 在默认位置插入（找到默认位置前一个按钮，插到它后面）
                    def_idx = _default_btn_order.index(bid)
                    if def_idx > 0:
                        prev_bid = _default_btn_order[def_idx - 1]
                        if prev_bid in btn_order:
                            btn_order.insert(btn_order.index(prev_bid) + 1, bid)
                        else:
                            btn_order.append(bid)
                    else:
                        btn_order.insert(0, bid)
            rebuild_button_bar()
        # 加载快捷键
        if "shortcut_map" in cfg:
            shortcut_map.clear()
            shortcut_map.update(cfg["shortcut_map"])
        if "shortcut_global" in cfg:
            shortcut_global.clear()
            shortcut_global.update(cfg["shortcut_global"])
        _apply_shortcuts()
        if "shortcut_win_geometry" in cfg and cfg["shortcut_win_geometry"]:
            shortcut_win_geometry = cfg["shortcut_win_geometry"]
        # 加载列宽（兼容旧配置）
        if "col_widths" in cfg:
            for cid, w in cfg["col_widths"].items():
                col_width_map[cid] = w
        # 加载参数面板位置大小
        if "setting_win_geometry" in cfg and cfg["setting_win_geometry"]:
            setting_win_geometry = cfg["setting_win_geometry"]
        # 加载参数面板三栏分隔位置
        if "pw_sash_positions" in cfg and cfg["pw_sash_positions"]:
            pw_sash_positions = cfg["pw_sash_positions"]
        # 加载参数面板三栏滚动位置
        if "panel_scroll" in cfg and cfg["panel_scroll"]:
            panel_scroll = cfg["panel_scroll"]
        # 加载主表格滚动位置
        if "tree_scroll_x" in cfg:
            tree_scroll_x = cfg["tree_scroll_x"]
        if "tree_scroll_y" in cfg:
            tree_scroll_y = cfg["tree_scroll_y"]
        # 加载置顶状态
        if "is_topmost" in cfg:
            is_topmost = cfg["is_topmost"]
            root.attributes("-topmost", is_topmost)
            _find_topmost_btn().config(text="取消置顶" if is_topmost else "窗口置顶")
        # 加载顶部按钮栏横向滚动位置
        if "top_scroll_pos" in cfg:
            root.after(100, lambda: top_canvas.xview_moveto(cfg["top_scroll_pos"]))
        for cid in col_cid_list:
            col_var_map[cid].set(cfg["columns"][cid])
            filter_min_var_map[cid].set(cfg["filter_min"][cid])
            filter_max_var_map[cid].set(cfg["filter_max"][cid])
            # 兼容旧配置中的大写单位 M/B
            u = cfg["units"][cid]
            if u == "M":
                u = "m"
            elif u == "B":
                u = "b"
            unit_var_map[cid].set(u)
        apply_filter_sort()
        # 恢复主表格滚动位置（延迟等待渲染完成）
        _tsx, _tsy = tree_scroll_x, tree_scroll_y
        def _restore_tree_scroll():
            try:
                tree.xview_moveto(_tsx)
                tree.yview_moveto(_tsy)
            except:
                pass
        root.after(200, _restore_tree_scroll)
        status_var.set("已加载保存配置")
    except Exception as e:
        status_var.set(f"加载配置失败:{str(e)}")

def reset_all_default():
    global sort_key, sort_reverse, col_order, is_topmost, pw_sash_positions, panel_scroll
    global tree_scroll_x, tree_scroll_y, btn_order, shortcut_map, shortcut_global
    global setting_win_geometry, shortcut_win_geometry
    sort_key = "pct"
    sort_reverse = True
    is_topmost = False
    pw_sash_positions = None
    panel_scroll = {}
    tree_scroll_x = 0
    tree_scroll_y = 0
    btn_order[:] = list(_default_btn_order)
    shortcut_map.clear()
    shortcut_global.clear()
    _apply_shortcuts()
    setting_win_geometry = None
    shortcut_win_geometry = None
    root.attributes("-topmost", False)
    _find_topmost_btn().config(text="窗口置顶")
    col_order[:] = list(col_cid_list)
    _default_widths = {"name":240, "buy":95, "sell":95, "margin":95, "pct":90,
        "buyOrders":100, "sellOrders":100,
        "vol_buy":120, "vol_sell":120, "week_buy":120, "week_sell":120}
    for cid in col_cid_list:
        col_var_map[cid].set(True)
        filter_min_var_map[cid].set("")
        filter_max_var_map[cid].set("")
        unit_var_map[cid].set("默认")
        col_width_map[cid] = _default_widths.get(cid, 95)
    root.geometry("1400x700")
    rebuild_button_bar()
    apply_filter_sort()
    status_var.set("已重置全部设置为默认")

# ===================== 置顶功能 =====================
def toggle_topmost():
    global is_topmost
    is_topmost = not is_topmost
    root.attributes("-topmost", is_topmost)
    _find_topmost_btn().config(text="取消置顶" if is_topmost else "窗口置顶")
    if is_topmost:
        root.lift()

# ===================== 快捷键功能 =====================
# 可设置快捷键的按钮ID列表（不含api按钮）
_SHORTCUT_ELIGIBLE = ["refresh", "param", "filter", "save", "load", "reset", "topmost"]

def _key_event_to_str(event):
    """将 tkinter 键盘事件转为快捷键字符串，如 SHIFT+F3"""
    parts = []
    if event.state & 0x1:   # Shift
        parts.append("SHIFT")
    if event.state & 0x4:   # Control
        parts.append("CTRL")
    if event.state & 0x8:   # Alt
        parts.append("ALT")
    # 获取键名
    key = event.keysym.upper()
    # 过滤鼠标按键和纯修饰键
    if key in ("SHIFT_L", "SHIFT_R", "CONTROL_L", "CONTROL_R", "ALT_L", "ALT_R"):
        return None
    try:
        if event.num > 0:  # 鼠标按键
            return None
    except (AttributeError, TypeError):
        pass
    if key == "ESCAPE":
        return "ESCAPE"
    # 排除单字母纯修饰键
    parts.append(key)
    return "+".join(parts)

def open_shortcut_dialog():
    """打开快捷键设置对话框"""
    global shortcut_win_geometry
    dlg = tk.Toplevel(root)
    dlg.title("快捷键设置")
    dlg.resizable(False, False)
    dlg.attributes("-topmost", True)
    dlg.transient(root)
    dlg.grab_set()

    # 当前编辑中的快捷键和全局状态（复制一份，取消时不影响原数据）
    editing = dict(shortcut_map)
    editing_global = dict(shortcut_global)

    frame = tk.Frame(dlg, padx=15, pady=15)
    frame.pack()

    tk.Label(frame, text='点击快捷键列设置快捷键，勾选"全局"后快捷键在窗口外也生效',
             font=("", 10), fg="#666").grid(row=0, column=0, columnspan=3, pady=(0,10))

    # 表头
    tk.Label(frame, text="按钮名称", font=("", 11, "bold"), width=20, anchor="w").grid(row=1, column=0, padx=5, pady=3)
    tk.Label(frame, text="快捷键", font=("", 11, "bold"), width=20, anchor="center").grid(row=1, column=1, padx=5, pady=3)
    tk.Label(frame, text="全局", font=("", 11, "bold"), width=6, anchor="center").grid(row=1, column=2, padx=5, pady=3)

    # 每行：按钮名称 + 快捷键显示 + 全局勾选
    row_labels = {}
    global_vars = {}
    for i, bid in enumerate(_SHORTCUT_ELIGIBLE):
        row = i + 2
        btn_text = _btn_defs.get(bid, ("?",))[0]
        tk.Label(frame, text=btn_text, font=("", 11), anchor="w", width=20).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        lbl = tk.Label(frame, text=editing.get(bid, ""), font=("", 11), width=20,
                       anchor="center", relief="groove", bg="#f0f0f0", cursor="hand2")
        lbl.grid(row=row, column=1, padx=5, pady=3)
        row_labels[bid] = lbl

        # 全局勾选
        gv = tk.BooleanVar(value=editing_global.get(bid, False))
        global_vars[bid] = gv
        cb = tk.Checkbutton(frame, variable=gv, width=4)
        cb.grid(row=row, column=2, padx=5, pady=3)

        def on_click(event, b=bid):
            _open_key_input_window(dlg, b, editing, row_labels)

        lbl.bind("<Button-1>", on_click)

    # 底部按钮
    btn_frame = tk.Frame(dlg)
    btn_frame.pack(pady=(5,10))

    def on_confirm():
        global shortcut_win_geometry
        shortcut_map.clear()
        shortcut_map.update(editing)
        shortcut_global.clear()
        _STANDARD_MODS = {"CTRL", "ALT", "SHIFT"}
        for bid in _SHORTCUT_ELIGIBLE:
            is_global = global_vars[bid].get()
            key_str = editing.get(bid, "")
            # 非修饰键组合（如 V+B）不支持全局，自动取消全局标记
            if is_global and key_str:
                parts = [p.strip().upper() for p in key_str.split("+")]
                non_std_mods = [p for p in parts[:-1] if p not in _STANDARD_MODS]
                if non_std_mods:
                    is_global = False
            shortcut_global[bid] = is_global
        _apply_shortcuts()
        # 保存窗口位置
        shortcut_win_geometry = dlg.geometry()
        dlg.destroy()

    def on_cancel():
        # 不保存窗口位置
        dlg.destroy()

    def on_reset():
        # 只重置快捷键和全局状态，不重置窗口位置
        editing.clear()
        for bid in _SHORTCUT_ELIGIBLE:
            editing[bid] = ""
            editing_global[bid] = False
            global_vars[bid].set(False)
        for bid, lbl in row_labels.items():
            lbl.config(text="", bg="#f0f0f0")

    tk.Button(btn_frame, text="确定", command=on_confirm, width=10, font=("", 11)).pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="取消", command=on_cancel, width=10, font=("", 11)).pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="重置全部", command=on_reset, width=10, font=("", 11)).pack(side=tk.LEFT, padx=8)

    # 恢复上次窗口位置，没有则居中
    if shortcut_win_geometry:
        dlg.geometry(shortcut_win_geometry)
    else:
        dlg.update_idletasks()
        w, h = dlg.winfo_width(), dlg.winfo_height()
        x = (dlg.winfo_screenwidth() - w) // 2
        y = (dlg.winfo_screenheight() - h) // 2
        dlg.geometry(f"+{x}+{y}")

def _open_key_input_window(parent_dlg, bid, editing, row_labels):
    """点击快捷键单元格后弹出的独立按键捕获窗口"""
    sub = tk.Toplevel(parent_dlg)
    btn_name = _btn_defs.get(bid, ("?",))[0]
    sub.title(f"设置快捷键 — {btn_name}")
    sub.resizable(False, False)
    sub.attributes("-topmost", True)
    sub.transient(parent_dlg)

    captured = [None]
    # 手动追踪修饰键状态，避免 Windows 上 event.state 不可靠的问题
    mod_state = {"shift": False, "ctrl": False, "alt": False}
    # 追踪非修饰键按住状态（用于支持 V+B 这类组合）
    held_non_mod = [None]  # 按住的非修饰键名

    frame = tk.Frame(sub, padx=20, pady=15)
    frame.pack()

    tk.Label(frame, text=f'请按下组合键作为 "{btn_name}" 的快捷键',
             font=("", 11)).pack(pady=(0, 5))
    tk.Label(frame, text="(支持 单键 / 修饰键+键 / 字母+字母，如 V+B)",
             font=("", 9), fg="#888").pack(pady=(0, 5))
    tk.Label(frame, text="⚠ 非修饰键组合（如 V+B）仅局部生效，全局快捷键无效",
             font=("", 9), fg="#E53935").pack(pady=(0, 10))

    display_lbl = tk.Label(frame, text="", font=("", 18, "bold"), fg="#2196F3", width=25,
                           relief="sunken", bg="#fff", anchor="center")
    display_lbl.pack(pady=(0, 15))

    warn_lbl = tk.Label(frame, text="", font=("", 9), fg="#E53935")
    warn_lbl.pack(pady=(0, 5))

    tk.Label(frame, text="按 ESC 可清空快捷键", font=("", 9), fg="#999").pack()

    _MODIFIER_KEYS = {"SHIFT_L", "SHIFT_R", "CONTROL_L", "CONTROL_R", "ALT_L", "ALT_R"}

    def _update_mod(event):
        """更新修饰键按下状态"""
        k = event.keysym.upper()
        if k in ("SHIFT_L", "SHIFT_R"):
            mod_state["shift"] = True
        elif k in ("CONTROL_L", "CONTROL_R"):
            mod_state["ctrl"] = True
        elif k in ("ALT_L", "ALT_R"):
            mod_state["alt"] = True

    def _clear_mod(event):
        """清除修饰键释放状态"""
        k = event.keysym.upper()
        if k in ("SHIFT_L", "SHIFT_R"):
            mod_state["shift"] = False
        elif k in ("CONTROL_L", "CONTROL_R"):
            mod_state["ctrl"] = False
        elif k in ("ALT_L", "ALT_R"):
            mod_state["alt"] = False
        # 如果释放的是 held_non_mod 中的键，也清除
        if held_non_mod[0] and k == held_non_mod[0]:
            held_non_mod[0] = None

    def on_sub_key(event):
        # 先更新修饰键状态（按键事件先于释放事件）
        _update_mod(event)

        key = event.keysym.upper()
        # 忽略纯修饰键（只记录状态）
        if key in _MODIFIER_KEYS:
            return
        try:
            if int(event.num) > 0:  # 鼠标按键
                return
        except (AttributeError, TypeError, ValueError):
            pass

        # ESC 特殊处理
        if key == "ESCAPE":
            captured[0] = "ESCAPE"
            display_lbl.config(text="ESCAPE", fg="#4CAF50")
            return

        # 如果已有非修饰键按住（如 V 还按着），且现在按了另一个键（如 B），组成 V+B
        if held_non_mod[0] and held_non_mod[0] != key:
            parts = []
            if mod_state["shift"]:
                parts.append("SHIFT")
            if mod_state["ctrl"]:
                parts.append("CTRL")
            if mod_state["alt"]:
                parts.append("ALT")
            parts.append(held_non_mod[0])
            parts.append(key)
            key_str = "+".join(parts)
            captured[0] = key_str
            display_lbl.config(text=key_str, fg="#4CAF50")
            warn_lbl.config(text="⚠ 此组合仅局部生效，不可全局")
            return

        # 记录此键为 held_non_mod
        held_non_mod[0] = key

        parts = []
        if mod_state["shift"]:
            parts.append("SHIFT")
        if mod_state["ctrl"]:
            parts.append("CTRL")
        if mod_state["alt"]:
            parts.append("ALT")
        parts.append(key)
        key_str = "+".join(parts)
        captured[0] = key_str
        display_lbl.config(text=key_str, fg="#4CAF50")
        # 如果是修饰键+单键，可以全局
        if not held_non_mod[0] or len(parts) <= 2:
            warn_lbl.config(text="")

    def on_sub_key_release(event):
        _clear_mod(event)

    sub.bind("<KeyPress>", on_sub_key)
    sub.bind("<KeyRelease>", on_sub_key_release)
    sub.focus_force()

    def on_ok():
        if captured[0] is not None:
            key_val = "" if captured[0] == "ESCAPE" else captured[0]
            editing[bid] = key_val
            row_labels[bid].config(text=key_val, bg="#f0f0f0")
        sub.destroy()

    def on_cancel():
        sub.destroy()

    btn_f = tk.Frame(sub)
    btn_f.pack(pady=(10, 10))
    tk.Button(btn_f, text="确认", command=on_ok, width=10, font=("", 11)).pack(side=tk.LEFT, padx=6)
    tk.Button(btn_f, text="取消", command=on_cancel, width=10, font=("", 11)).pack(side=tk.LEFT, padx=6)

    # 居中显示（相对于父窗口）
    parent_dlg.update_idletasks()
    px = parent_dlg.winfo_x()
    py = parent_dlg.winfo_y()
    pw = parent_dlg.winfo_width()
    ph = parent_dlg.winfo_height()
    sub.update_idletasks()
    sw = sub.winfo_width()
    sh = sub.winfo_height()
    sx = px + (pw - sw) // 2
    sy = py + (ph - sh) // 2
    sub.geometry(f"+{sx}+{sy}")

def _shortcut_str_to_tk(s):
    """将快捷键字符串如 SHIFT+F3 转为 tkinter 绑定格式如 <Shift-F3>
    对于非修饰键组合如 V+B，返回 None（需用自定义按键追踪处理）"""
    if not s:
        return None
    parts = [p.strip() for p in s.split("+")]
    # 最后一部分是键名
    key = parts[-1]
    modifiers = parts[:-1]
    # 检查是否有非标准修饰键（如 V+B 中的 V）
    _STANDARD_MODS = {"CTRL", "ALT", "SHIFT"}
    non_std_mods = [m for m in modifiers if m.upper() not in _STANDARD_MODS]
    if non_std_mods:
        return None  # 含非修饰键组合，不能用标准 tkinter 绑定
    # 构造 tkinter 格式
    mod_str = ""
    for m in modifiers:
        ml = m.lower()
        if ml == "ctrl":
            mod_str += "Control-"
        elif ml == "alt":
            mod_str += "Alt-"
        elif ml == "shift":
            mod_str += "Shift-"
    # 键名处理
    if len(key) == 1:
        key = key.lower()
    elif key.startswith("F") and key[1:].isdigit():
        pass  # F1-F12 直接用
    elif key == "SPACE":
        key = "space"
    elif key == "ESCAPE":
        key = "Escape"
    elif key == "RETURN":
        key = "Return"
    elif key == "TAB":
        key = "Tab"
    elif key == "BACKSPACE":
        key = "BackSpace"
    elif key == "DELETE":
        key = "Delete"
    elif key == "INSERT":
        key = "Insert"
    elif key == "HOME":
        key = "Home"
    elif key == "END":
        key = "End"
    elif key == "PAGE_UP":
        key = "Prior"
    elif key == "PAGE_DOWN":
        key = "Next"
    elif key in ("UP", "DOWN", "LEFT", "RIGHT"):
        key = {"UP": "Up", "DOWN": "Down", "LEFT": "Left", "RIGHT": "Right"}[key]
    return f"<{mod_str}{key}>"

# ===================== 全局热键支持（Windows RegisterHotKey） =====================
_global_hotkey_thread = None
_global_hotkey_stop = threading.Event()

# Windows 常量
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
PM_REMOVE = 0x0001

# 虚拟键码映射
_VK_MAP = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "SPACE": 0x20, "ESCAPE": 0x1B, "RETURN": 0x0D,
    "TAB": 0x09, "BACKSPACE": 0x08, "DELETE": 0x2E,
    "INSERT": 0x2D, "HOME": 0x24, "END": 0x23,
    "PAGE_UP": 0x21, "PAGE_DOWN": 0x22,
    "UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
}

def _shortcut_to_win32(s):
    """将快捷键字符串转为 Windows (mod, vk) 元组，失败返回 None"""
    if not s:
        return None
    parts = [p.strip() for p in s.split("+")]
    key = parts[-1].upper()
    modifiers = [p.strip().upper() for p in parts[:-1]]
    # 只允许一个非修饰键
    if len(parts) > 1 and key in ("CTRL", "ALT", "SHIFT"):
        return None
    mod = 0
    for m in modifiers:
        if m == "CTRL":
            mod |= MOD_CONTROL
        elif m == "ALT":
            mod |= MOD_ALT
        elif m == "SHIFT":
            mod |= MOD_SHIFT
        else:
            return None  # 未知修饰键
    mod |= MOD_NOREPEAT
    # 虚拟键码
    if key in _VK_MAP:
        vk = _VK_MAP[key]
    elif len(key) == 1 and key.isalpha():
        vk = ord(key)
    elif len(key) == 1 and key.isdigit():
        vk = ord(key)
    else:
        return None  # 不支持的键
    return (mod, vk)

def _stop_global_hotkey_thread():
    """停止全局热键监听线程"""
    global _global_hotkey_thread
    _global_hotkey_stop.set()
    if _global_hotkey_thread and _global_hotkey_thread.is_alive():
        _global_hotkey_thread.join(timeout=1)
    _global_hotkey_thread = None

def _global_hotkey_worker(hotkeys_to_register):
    """全局热键监听线程：在此线程中注册热键并监听 WM_HOTKEY 消息"""
    # 在此线程中注册热键（WM_HOTKEY 会发到此线程的消息队列）
    registered = {}
    for bid, (mod, vk) in hotkeys_to_register.items():
        hid = hash(bid) & 0x7FFFFFFF
        ok = ctypes.windll.user32.RegisterHotKey(None, hid, mod, vk)
        if ok:
            registered[bid] = hid

    if not registered:
        return

    # 消息循环
    msg = ctypes.wintypes.MSG()
    while not _global_hotkey_stop.is_set():
        # PeekMessageW 在此线程取此线程的 WM_HOTKEY
        if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            if msg.message == WM_HOTKEY:
                hotkey_id = msg.wParam
                for bid, hid in registered.items():
                    if hid == hotkey_id:
                        cmd_map = {
                            "refresh": refresh_table,
                            "param": open_param_panel,
                            "filter": apply_filter_sort,
                            "save": save_config,
                            "load": load_config,
                            "reset": reset_all_default,
                            "topmost": toggle_topmost,
                        }
                        cmd = cmd_map.get(bid)
                        if cmd:
                            root.after(0, cmd)
                        break
            elif msg.message == 0x0012:  # WM_QUIT
                break
        else:
            _global_hotkey_stop.wait(0.05)

    # 线程退出前注销所有热键
    for bid, hid in registered.items():
        try:
            ctypes.windll.user32.UnregisterHotKey(None, hid)
        except:
            pass

def _register_global_hotkeys():
    """收集标记为全局的快捷键，启动监听线程"""
    global _global_hotkey_thread
    _stop_global_hotkey_thread()
    _global_hotkey_stop.clear()

    # 收集需要注册的热键
    hotkeys = {}
    for bid in _SHORTCUT_ELIGIBLE:
        key_str = shortcut_map.get(bid, "")
        is_global = shortcut_global.get(bid, False)
        if not key_str or not is_global:
            continue
        result = _shortcut_to_win32(key_str)
        if not result:
            continue
        hotkeys[bid] = result

    if not hotkeys:
        return

    # 启动监听线程（热键在子线程中注册，WM_HOTKEY 也发到子线程）
    _global_hotkey_thread = threading.Thread(
        target=_global_hotkey_worker,
        args=(hotkeys,),
        daemon=True
    )
    _global_hotkey_thread.start()

# 非修饰键组合的自定义追踪状态
_held_keys = set()           # 当前按住的普通键集合
_combo_bindings = {}         # bid → (prefix_keys, final_key, cmd) 用于非修饰键组合
_combo_listeners_bound = False  # 是否已绑定全局 KeyPress/KeyRelease
_MODIFIER_KEYSYMS = {"SHIFT_L", "SHIFT_R", "CONTROL_L", "CONTROL_R", "ALT_L", "ALT_R"}

def _on_combo_key_press(event):
    """非修饰键组合追踪：按下时记录，匹配则触发"""
    if not _combo_bindings:
        return
    key = event.keysym.upper()
    if key in _MODIFIER_KEYSYMS:
        return
    _held_keys.add(key)
    # 检查是否匹配某个非修饰键组合
    _INPUT_WIDGETS_CHECK = (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text)
    if isinstance(event.widget, _INPUT_WIDGETS_CHECK):
        return
    for bid, (prefix_keys, final_key, cmd) in _combo_bindings.items():
        if key == final_key and prefix_keys.issubset(_held_keys):
            cmd()
            break

def _on_combo_key_release(event):
    """非修饰键组合追踪：释放时移除"""
    if not _combo_bindings:
        return
    key = event.keysym.upper()
    if key in _MODIFIER_KEYSYMS:
        return
    _held_keys.discard(key)

def _apply_shortcuts():
    """应用快捷键绑定到主窗口（局部）+ 注册全局热键"""
    global _prev_shortcut_map, _combo_bindings, _combo_listeners_bound
    # 先清除上一次绑定的局部快捷键
    for bid, old_key in _prev_shortcut_map.items():
        if old_key:
            old_tk = _shortcut_str_to_tk(old_key)
            if old_tk:
                try:
                    root.unbind_all(old_tk)
                except:
                    pass
    # 清除非修饰键组合绑定
    _combo_bindings.clear()
    cmd_map = {
        "refresh": refresh_table,
        "param": open_param_panel,
        "filter": apply_filter_sort,
        "save": save_config,
        "load": load_config,
        "reset": reset_all_default,
        "topmost": toggle_topmost,
    }
    _INPUT_WIDGETS = (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text)
    for bid in _SHORTCUT_ELIGIBLE:
        key_str = shortcut_map.get(bid, "")
        if not key_str:
            continue
        is_global = shortcut_global.get(bid, False)
        if is_global:
            continue  # 全局快捷键由 RegisterHotKey 处理
        tk_seq = _shortcut_str_to_tk(key_str)
        cmd = cmd_map.get(bid)
        if not cmd:
            continue
        if tk_seq:
            # 标准快捷键（单键或修饰键+键），用 bind_all
            def _make_handler(c):
                def _handler(event):
                    w = event.widget
                    if isinstance(w, _INPUT_WIDGETS):
                        return
                    c()
                return _handler
            root.bind_all(tk_seq, _make_handler(cmd))
        else:
            # 非修饰键组合（如 V+B），用自定义按键追踪
            parts = [p.strip().upper() for p in key_str.split("+")]
            # 最后一个是最终触发的键，前面的是需要按住的键
            final_key = parts[-1]
            prefix_keys = set(parts[:-1])
            # 检查是否有非标准修饰键
            _STANDARD_MODS = {"CTRL", "ALT", "SHIFT"}
            real_prefix = set()
            for p in prefix_keys:
                if p in _STANDARD_MODS:
                    pass  # 标准修饰键通过 bind_all 处理更可靠，这里暂不支持混合
                else:
                    real_prefix.add(p)
            if real_prefix:
                _combo_bindings[bid] = (real_prefix, final_key, cmd)

    # 如果有非修饰键组合，确保全局 KeyPress/KeyRelease 追踪已绑定
    if _combo_bindings and not _combo_listeners_bound:
        root.bind_all("<KeyPress>", _on_combo_key_press, add="+")
        root.bind_all("<KeyRelease>", _on_combo_key_release, add="+")
        _combo_listeners_bound = True
    # 如果没有非修饰键组合了，handler 内部会直接 return，无需解绑
    # 记录当前绑定，供下次清除
    _prev_shortcut_map = dict(shortcut_map)
    # 注册全局热键
    _register_global_hotkeys()

# ===================== 右键复制物品ID / 表头列重排 / 按钮重排 =====================
header_menu_cid = None
btn_menu_bid = None  # 当前右键的按钮ID

def move_col_left():
    global col_order
    idx = col_order.index(header_menu_cid)
    if idx > 0:
        col_order[idx], col_order[idx-1] = col_order[idx-1], col_order[idx]
        apply_filter_sort()

def move_col_right():
    global col_order
    idx = col_order.index(header_menu_cid)
    if idx < len(col_order) - 1:
        col_order[idx], col_order[idx+1] = col_order[idx+1], col_order[idx]
        apply_filter_sort()

def move_btn_left():
    global btn_order
    idx = btn_order.index(btn_menu_bid)
    if idx > 0:
        btn_order[idx], btn_order[idx-1] = btn_order[idx-1], btn_order[idx]
        rebuild_button_bar()

def move_btn_right():
    global btn_order
    idx = btn_order.index(btn_menu_bid)
    if idx < len(btn_order) - 1:
        btn_order[idx], btn_order[idx+1] = btn_order[idx+1], btn_order[idx]
        rebuild_button_bar()

def copy_item_id():
    sel = tree.selection()
    if not sel:
        return
    vis_cols = get_visible_cols()
    if "name" not in vis_cols:
        return
    name_idx = vis_cols.index("name")
    item_id = tree.item(sel[0])["values"][name_idx]
    # 下划线转空格：ENCHANTED_TITANIUM → ENCHANTED TITANIUM
    item_id = str(item_id).replace("_", " ")
    root.clipboard_clear()
    root.clipboard_append(item_id)
    status_var.set(f"已复制: {item_id}")

def show_right_menu(event):
    global header_menu_cid
    region = tree.identify_region(event.x, event.y)
    if region == "heading":
        # 右键表头 → 列重排菜单
        col = tree.identify_column(event.x)
        col_idx = int(col[1:]) - 1
        visible = get_visible_cols()
        if col_idx < len(visible):
            header_menu_cid = visible[col_idx]
            header_right_menu.tk_popup(event.x_root, event.y_root)
    else:
        # 右键数据行 → 直接复制物品ID（不弹菜单，置顶时也能用）
        row = tree.identify_row(event.y)
        if row:
            tree.selection_set(row)
            copy_item_id()

# ===================== 主窗口初始化 =====================
root = tk.Tk()
root.title("Skyblock Bazaar 精简主界面")
root.geometry("1400x700")

# 初始化勾选布尔变量和筛选/单位的 StringVar
_default_widths = {"name":240, "buy":95, "sell":95, "margin":95, "pct":90,
    "buyOrders":100, "sellOrders":100,
    "vol_buy":120, "vol_sell":120, "week_buy":120, "week_sell":120}
for meta in col_meta:
    cid = meta["cid"]
    col_var_map[cid] = tk.BooleanVar(value=True)
    filter_min_var_map[cid] = tk.StringVar(value="")
    filter_max_var_map[cid] = tk.StringVar(value="")
    unit_var_map[cid] = tk.StringVar(value="默认")
    col_width_map[cid] = _default_widths.get(cid, 95)
col_order = list(col_cid_list)

# 顶部操作栏（可横向滚动，缩小窗口时按钮不会被挤没）
top_outer = tk.Frame(root)
top_outer.pack(fill=tk.X, padx=6, pady=6)

top_scrollbar = ttk.Scrollbar(top_outer, orient=tk.HORIZONTAL)
top_canvas = tk.Canvas(top_outer, height=45, xscrollcommand=top_scrollbar.set)
top_scrollbar.config(command=top_canvas.xview)
top_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
top_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

top_frame = tk.Frame(top_canvas)
top_canvas.create_window((0,0), window=top_frame, anchor="nw")
top_frame.bind("<Configure>", lambda e: top_canvas.configure(scrollregion=top_canvas.bbox("all")))

# 按钮定义：id → (text, command)
_btn_defs = {
    "refresh":  ("刷新全部数据", refresh_table),
    "param":    ("参数设置面板", open_param_panel),
    "filter":   ("应用筛选条件", apply_filter_sort),
    "save":     ("保存当前设置", save_config),
    "load":     ("加载保存设置", load_config),
    "reset":    ("重置全部默认", reset_all_default),
    "topmost":  ("窗口置顶", toggle_topmost),
    "api":      ("输入api（可选）", open_api_dialog),
    "shortcut": ("快捷键设置", open_shortcut_dialog),
}
_default_btn_order = ["refresh", "param", "filter", "save", "load", "reset", "topmost", "shortcut", "api"]
if not btn_order:
    btn_order[:] = list(_default_btn_order)

# 按钮右键菜单
btn_right_menu = tk.Menu(root, tearoff=0)
btn_right_menu.add_command(label="← 左移此按钮", command=move_btn_left)
btn_right_menu.add_command(label="→ 右移此按钮", command=move_btn_right)

def _on_btn_right_click(event, bid):
    global btn_menu_bid
    btn_menu_bid = bid
    btn_right_menu.tk_popup(event.x_root, event.y_root)

def rebuild_button_bar():
    """按照 btn_order 重建按钮栏"""
    for w in top_frame.winfo_children():
        w.destroy()
    for bid in btn_order:
        if bid in _btn_defs:
            text, cmd = _btn_defs[bid]
            b = tk.Button(top_frame, text=text, command=cmd, font=("",11))
            b.pack(side=tk.LEFT, padx=6)
            b.bind("<Button-3>", lambda e, id=bid: _on_btn_right_click(e, id))
            if bid == "topmost":
                top_btn_ref = b
    # 状态标签
    sl = tk.Label(top_frame, textvariable=status_var, fg="#333")
    sl.pack(side=tk.LEFT, padx=30)

# 状态变量（可被 rebuild 引用）
status_var = tk.StringVar(value="点击刷新加载数据")
rebuild_button_bar()

# 引用置顶按钮（用于更新文字）
def _find_topmost_btn():
    for w in top_frame.winfo_children():
        if isinstance(w, tk.Button) and "置顶" in w.cget("text"):
            return w
    return None

# 表格区域
table_frame = tk.Frame(root)
table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
tree = ttk.Treeview(table_frame, columns=col_cid_list, show="headings",
                    yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.config(command=tree.yview)
scroll_x.config(command=tree.xview)
tree.pack(fill=tk.BOTH, expand=True)

# 表头右键菜单（列重排）
header_right_menu = tk.Menu(root, tearoff=0)
header_right_menu.add_command(label="← 左移此列", command=move_col_left)
header_right_menu.add_command(label="→ 右移此列", command=move_col_right)

tree.bind("<Button-3>", show_right_menu)

# 启动自动加载配置和数据缓存
load_api_key()
load_config()
cached = load_cached_data()
if cached:
    item_data_cache = cached
    apply_filter_sort()
    status_var.set(f"已加载缓存数据 {len(cached)} 条，点击刷新获取最新")
else:
    status_var.set("无缓存数据，点击刷新加载数据")
root.mainloop()