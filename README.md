# SkyBlock Bazaar

一个基于 Tkinter 的 Hypixel SkyBlock Bazaar 数据查看工具。

## 功能

- 获取并显示 Hypixel Bazaar 商品数据
- 按价格、利润率、订单量和成交量筛选、排序
- 支持 `k`、`m`、`b` 等单位显示和筛选
- 自定义表格列、按钮顺序和窗口置顶状态
- 支持局部快捷键和 Windows 全局快捷键
- 支持本地数据缓存

## 运行环境

- Windows
- Python 3.9 或更高版本
- 需要联网访问 Hypixel API

## 安装

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 PowerShell 阻止虚拟环境脚本，可以直接使用虚拟环境中的 Python：

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 启动

```powershell
python bazaar.py
```

也可以使用虚拟环境中的 Python：

```powershell
.venv\Scripts\python.exe bazaar.py
```

## API Key

Bazaar 公共接口通常可以不使用 API Key。程序保留了可选的 API Key 输入功能；如果填写，密钥会保存到本地 `config.json`。

不要将包含 API Key 的 `config.json` 上传到 GitHub。

## 本地文件

程序运行后可能生成以下文件：

- `config.json`：窗口、筛选、快捷键和可选 API Key 配置
- `bazaar_data.json`：Bazaar 数据缓存

这两个文件属于本地运行数据，已加入 `.gitignore`，不会被提交到 Git。

## 许可

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
