# spider_vtbasmr

基于 Playwright 的 `vtbasmr.xyz` 抓取工程，用于自动登录、抓取 tag 页、抓取详情页、保存结构化数据、维护抓取归档、生成日志，以及修复历史数据中缺失的下载链接。

## 项目目标

当前工程主要完成以下能力：

- 自动登录站点并保存 `storage_state`
- 抓取 tag 页面
  - tag 名称
  - 作品封面列表
  - 分页列表
- 抓取详情页
  - 标题
  - 发布时间
  - 摘要
  - tags
  - 隐藏内容文本
  - 下载链接
  - 提取码 / 解压密码
- 按 VTB 配置执行抓取
- 按归档状态控制抓取模式
- 保存抓取结果到本地 JSON
- 保存抓取日志
- 修复历史 JSON / 日志里缺失的 `download_links`

## 目录结构

```text
.
├─ .config/
│  ├─ config.json
│  └─ vtb.json
├─ .data/
│  ├─ archive/
│  ├─ log/
│  ├─ save/
│  └─ storage/
├─ src/spider_vtbasmr/
│  ├─ browser/
│  ├─ main/
│  ├─ manager/
│  └─ scraper/
├─ tests/
├─ pyproject.toml
├─ requirements.txt
└─ README.md
```

### `src/spider_vtbasmr/browser`

浏览器能力封装。

- [playwright_browser_client.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/browser/playwright_browser_client.py)
  - 启动浏览器
  - 读取已登录状态
  - 保存 `storage_state`
  - 关闭浏览器会话

### `src/spider_vtbasmr/manager`

流程编排和配置管理。

- [config_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/config_manager.py)
  - 读取 `.config/config.json`
- [vtb_config_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/vtb_config_manager.py)
  - 读取 `.config/vtb.json`
- [login_action.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/login_action.py)
  - 执行站点登录动作
- [login_state_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/login_state_manager.py)
  - 生成登录态文件
- [archive_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/archive_manager.py)
  - 读取 / 保存已抓取归档
- [save_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/save_manager.py)
  - 保存封面信息和详情信息到同一个 JSON
- [log_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/log_manager.py)
  - 保存日志记录
- [vtb_crawl_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/vtb_crawl_manager.py)
  - 单个 tag 的完整抓取主流程

### `src/spider_vtbasmr/scraper`

页面抓取逻辑。

- [tag_page_scraper.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/scraper/tag_page_scraper.py)
  - 抓取 tag 页封面列表和分页
- [detail_page_scraper.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/scraper/detail_page_scraper.py)
  - 抓取详情页内容
  - 自动处理“立即查看”交互
  - 自动提取下载链接
  - 当页面锚点提取失败时，会从 `hidden_content_text` 兜底提取下载链接

### `src/spider_vtbasmr/main`

批量执行入口。

- [batch_until_archived_crawler.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/main/batch_until_archived_crawler.py)
  - 遍历全部 VTB 配置
  - 先删除对应 log 文件
  - 再以 `CrawlMode.UNTIL_ARCHIVED` 执行抓取

### `tests`

当前项目没有使用 `pytest` 组织测试，而是用“可直接运行的脚本”作为功能入口和验证脚本。

- [test_login_state_manager.py](/d:/Project/MyGithub/spider_vtbasmr/tests/test_login_state_manager.py)
  - 生成登录态
- [test_tag_page_scraper.py](/d:/Project/MyGithub/spider_vtbasmr/tests/test_tag_page_scraper.py)
  - 抓取单个 tag 页
- [test_detail_page_scraper.py](/d:/Project/MyGithub/spider_vtbasmr/tests/test_detail_page_scraper.py)
  - 抓取单个详情页
- [test_vtb_crawl_manager.py](/d:/Project/MyGithub/spider_vtbasmr/tests/test_vtb_crawl_manager.py)
  - 抓取单个 tag
- [test_fix_saved_detail_download_links.py](/d:/Project/MyGithub/spider_vtbasmr/tests/test_fix_saved_detail_download_links.py)
  - 修复指定 tag 的保存数据和日志里缺失的 `download_links`
- [test_batch_until_archived_crawler.py](/d:/Project/MyGithub/spider_vtbasmr/tests/test_batch_until_archived_crawler.py)
  - 批量执行全部 VTB 配置抓取

## 运行依赖

当前工程的运行时第三方依赖只有一项：

- `playwright>=1.53.0`

标准库已使用但不需要额外安装，包括：

- `json`
- `pathlib`
- `dataclasses`
- `threading`
- `enum`
- `urllib.parse`
- `typing`
- `re`
- `sys`

## 环境要求

- Python `>=3.11`
- 推荐本机已安装 Microsoft Edge
  - 当前默认配置为 `browser.channel = "msedge"`
- 如果不使用本机 Edge，则需要安装 Playwright 托管浏览器

## 安装

安装项目：

```bash
python -m pip install -e .
```

或者只安装依赖：

```bash
python -m pip install -r requirements.txt
```

如果你希望使用 Playwright 托管浏览器，而不是本机 Edge：

```bash
playwright install chromium
```

## 配置说明

### 1. `.config/config.json`

全局配置，主要用于登录和下载链接匹配。

当前包含以下配置项：

- `browser.channel`
  - 浏览器通道，例如 `msedge`
- `login_info.url`
  - 登录地址
- `login_info.username`
  - 登录账号
- `login_info.password`
  - 登录密码
- `login_info.success_prefix`
  - 登录成功后 URL 前缀校验
- `login_info.state_file_path`
  - 登录态文件保存路径
- `download_link_info`
  - 下载链接前缀映射
  - key 会作为 `link_type`

示例：

```json
{
  "browser": {
    "channel": "msedge"
  },
  "login_info": {
    "url": "https://vtbasmr.xyz/login?redirect_to=https://vtbasmr.xyz/",
    "username": "your_username",
    "password": "your_password",
    "success_prefix": "https://vtbasmr.xyz/",
    "state_file_path": ".data/storage/login_state"
  },
  "download_link_info": {
    "baidu_netdisk": "https://pan.baidu.com/s"
  }
}
```

### 2. `.config/vtb.json`

VTB 抓取配置。

每个 tag 一份配置，包含：

- `name`
- `url`
- `archive_file_path`
- `save_dir_path`
- `log_file_path`

示例：

```json
{
  "利香": {
    "name": "利香",
    "url": "https://vtbasmr.xyz/tag/%e5%88%a9%e9%a6%99",
    "archive_file_path": ".data/archive/利香.txt",
    "save_dir_path": ".data/save/利香",
    "log_file_path": ".data/log/利香.json"
  }
}
```

## 数据输出说明

### 保存数据

详情页数据保存路径规则：

```text
{save_dir_path}/{年}/{月}/{post_id}.json
```

例如：

```text
.data/save/利香/2021/11/64.json
```

每个文件会同时保存：

- `post_id`
- `cover_item`
- `detail_page_result`

### 日志数据

日志文件是一个 JSON 数组，每一项包含：

- `tag_name`
- `published_at`
- `saved_detail_file_path`
- `download_links`

### 归档数据

归档文件按行保存已抓取过的 id。

## 抓取模式

[vtb_crawl_manager.py](/d:/Project/MyGithub/spider_vtbasmr/src/spider_vtbasmr/manager/vtb_crawl_manager.py) 支持三种模式：

- `CrawlMode.ALL`
  - 从第一页到最后一页，全部抓取
- `CrawlMode.SKIP_ARCHIVED`
  - 遍历全部页面，已归档的详情页跳过
- `CrawlMode.UNTIL_ARCHIVED`
  - 从第一页开始抓，遇到已归档项后停止

当前主批量入口使用的是：

- `CrawlMode.UNTIL_ARCHIVED`

## 常用运行方式

### 1. 生成登录态

```bash
python tests/test_login_state_manager.py
```

默认会读取 `.config/config.json` 中的登录配置，并保存到：

- `.data/storage/login_state`

### 2. 抓取单个 tag 页面

```bash
python tests/test_tag_page_scraper.py
```

### 3. 抓取单个详情页

```bash
python tests/test_detail_page_scraper.py
```

### 4. 抓取单个 VTB

```bash
python tests/test_vtb_crawl_manager.py
```

默认测试脚本中使用：

- `CrawlMode.UNTIL_ARCHIVED`

### 5. 批量抓取全部 VTB 配置

```bash
python tests/test_batch_until_archived_crawler.py
```

运行时会：

- 读取 `.config/vtb.json` 中全部配置
- 先删除每个 tag 对应的 log 文件
- 再以 `CrawlMode.UNTIL_ARCHIVED` 执行抓取

### 6. 修复历史数据中缺失的下载链接

```bash
python tests/test_fix_saved_detail_download_links.py
```

该脚本会：

- 从 `vtb.json` 读取指定 `tag_name` 的 `save_dir_path`
- 修复保存文件里缺失的 `download_links`
- 同时修复对应 log 文件里缺失的 `download_links`

## 下载链接提取规则

详情页下载链接提取分两层：

1. 优先从 `.erphpdown-content-view a` 中提取
2. 如果页面锚点没有命中，则从 `hidden_content_text` 中正则提取 URL

只有当链接前缀命中 `.config/config.json` 中 `download_link_info` 里的任意一项时，才会被识别为有效下载链接。

最终输出字段包括：

- `link_type`
- `link_url`
- `link_text`

## 当前实现约束

- 当前项目依赖已生成的登录态文件
- 详情页抓取需要真实浏览器上下文，因为存在“立即查看”之类的前端交互
- 浏览器默认复用同一个已登录会话，以减少重复启动成本
- archive 采用“整轮完成后再写入”的策略
- log 当前会在单轮抓取结束时写出
- `tests/` 中脚本是“可直接执行的功能脚本”，不是单元测试框架风格

## 常见问题

### 1. Playwright 启动时报 `WinError 5: 拒绝访问`

这通常不是项目代码问题，而是当前运行环境限制了 Playwright 创建子进程。

建议：

- 直接在本机普通 PowerShell 里运行脚本
- 不要在受限沙箱环境里运行 Playwright
- 如果不使用本机 Edge，可尝试先执行：

```bash
playwright install chromium
```

### 2. 某些历史详情页 `download_links` 为空

这是老页面结构和新页面结构不一致导致的。当前工程已经支持：

- 新抓取时从 `hidden_content_text` 兜底提取
- 用修复脚本批量补历史数据和日志

### 3. 登录态失效

重新执行：

```bash
python tests/test_login_state_manager.py
```

## 安全提示

- 不要把真实账号密码提交到仓库
- 不要把 `storage_state` 登录态文件分享给他人
- 登录态文件具备直接复用身份的风险
