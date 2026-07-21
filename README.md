# VTB ASMR 工具

这是一个基于 PySide6 的本地桌面工具，用于完成 VTB ASMR 数据抓取、百度网盘资源转存、FNOS/NAS 下载提交和压缩资源整理。

## 一键启动

双击仓库根目录的 `run.bat`。

启动脚本会：

1. 查找 Python 3.13；
2. 创建或修复 `.venv`；
3. 仅在 `pyproject.toml` 发生变化时安装项目依赖；
4. 启动 `python -m spider_vtbasmr_gui`。

也可以手动启动：

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m spider_vtbasmr_gui
```

## GUI 页面

- **基本配置**：设置抓取配置、FNOS 配置、网盘目录、NAS 目录、7z 程序和默认解压密码。保存后立即应用。
- **登录与抓取**：生成站点登录态，选择 VTB 和抓取策略并执行后台抓取。
- **资源转存**：解析抓取日志中的百度网盘链接，转存全部分享资源，并按批次提交 NAS 下载。
- **资源解压**：由 7-Zip 根据文件内容识别其支持的压缩格式，不依赖文件名或扩展名；按 Tag、年份和月份整理输出。

启动 GUI 不会自动执行登录、抓取、转存、下载或解压。

## 架构

```text
PySide6 页面
    ↓ signal / view state
页面控制器
    ↓ background task
应用服务
    ├─ spider_vtbasmr 抓取核心
    ├─ 内置 FNOS 网盘网关
    └─ 7z 进程适配
```

`src/spider_vtbasmr` 是不依赖 PySide6 的抓取核心；`src/spider_vtbasmr_gui` 是桌面应用层。核心配置管理器可显式构造，GUI 不使用或重置全局单例。

## 本地数据

运行数据统一位于 `.data/`：

```text
.data/
├─ .config/       # 抓取和 FNOS 配置
├─ config/        # GUI 配置
├─ archive/       # 抓取归档
├─ logs/          # 抓取日志
├─ save/          # 历史抓取结果
└─ storage/       # 登录态
```

GUI 配置中的工程内路径以相对路径保存，移动仓库后仍可解析。`.data/`、`.config/` 和 `.venv/` 均受 Git 忽略。

`.data` 中可能包含账号、Cookie、登录态和设备认证信息。不要提交、分享或打印这些文件。

## 配置关系

GUI 默认读取 `.data/config/config.json`，其中引用：

- `.data/.config/spider_vtbasmr_base_config.json`
- `.data/.config/spider_vtbasmr_vtb_config.json`
- `.data/.config/baidu_netdisk_fnos_api.json`

抓取基础配置控制浏览器、站点登录、日志路径和下载链接识别；VTB 配置控制 Tag URL、归档文件和结果目录；FNOS 配置提供本地 NAS 服务地址和认证。

## FNOS 手动登录

“资源转存”页面刷新 FNOS 认证时会打开独立浏览器：

- 如果现有资料已包含有效的百度网盘认证，程序验证成功后会自动关闭浏览器。
- 如果百度网盘尚未登录，浏览器会保持打开且不设置登录倒计时。请在该窗口中手动完成 FNOS 和百度网盘登录；程序捕获并验证文件列表认证成功后会自动保存配置并关闭浏览器。
- 如果不想继续，可以主动关闭浏览器窗口，任务会以“认证未完成”结束。

## 开发与测试

安装测试依赖：

```powershell
.venv\Scripts\python -m pip install -e ".[test]"
```

运行测试：

```powershell
.venv\Scripts\python -m pytest
```

无显示器环境下可设置：

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.venv\Scripts\python -m pytest
```

现有 `tests/test_*.py` 中部分文件是会访问真实站点或修改本地数据的历史功能脚本。自动化测试必须通过替身隔离浏览器、网络转存和真实解压副作用。

## 核心包调用

核心包仍可直接使用：

```python
from pathlib import Path

from spider_vtbasmr import CrawlMode, PageOrder, VtbCrawler
from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager

root = Path.cwd()
crawler = VtbCrawler(
    config_manager=ConfigManager(
        root / ".data/.config/spider_vtbasmr_base_config.json",
        project_root=root,
    ),
    vtb_config_manager=VtbConfigManager(
        root / ".data/.config/spider_vtbasmr_vtb_config.json",
        project_root=root,
    ),
)
result = crawler.crawl_vtb_list(
    crawl_mode=CrawlMode.UNTIL_ARCHIVED,
    page_order=PageOrder.ASCENDING,
)
```