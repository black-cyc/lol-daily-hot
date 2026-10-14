# 英雄联盟热点监控

面向英雄联盟创作者的每日热点看板。Python 流水线汇总 B 站、微博、虎扑与抖音输入，再将主题数据发布到纯静态 GitHub Pages 页面。

## 本地运行

需要 Python 3.11+。Windows 下可直接执行：

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 pipeline/run.py
py -3.12 -m http.server 8765 --directory docs
```

然后访问 `http://127.0.0.1:8765`。页面必须从静态 HTTP 服务或 GitHub Pages 访问，直接双击 `docs/index.html` 会被浏览器的 `file://` 跨域策略拦截 JSON `fetch`。

运行后会生成：

- `docs/data/YYYY-MM-DD.json`：当日完整日报
- `docs/data/latest.json`：当日完整日报副本
- `docs/data/index.json`：可切换的历史日期
- `pipeline/data/history.sqlite3`：持续积累的采集与话题历史

未配置 Kimi 或抖音时，流水线仍会成功完成；前者自动使用本地聚类，后者会在日报来源状态中标记失败。

## 环境变量

### Kimi 聚合（可选）

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `KIMI_API_KEY` | 否 | Moonshot/Kimi OpenAI 兼容 API Key |
| `KIMI_MODEL` | 否 | Kimi 控制台可用的模型名；未设置时本地聚类 |
| `KIMI_BASE_URL` | 否 | 默认 `https://api.moonshot.cn/v1` |

### 抖音云端数据接口

抖音本机 OpenCLI 登录态不能在 GitHub Actions 中使用。本项目采用可替换的合规云端 HTTP 接口：

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `DOUYIN_HOT_API_URL` | 是 | 热榜接口 URL |
| `DOUYIN_SEARCH_API_URL` | 是 | 视频检索接口 URL，流水线以 `?keyword=话题词` 调用 |
| `DOUYIN_API_TOKEN` | 是 | Bearer Token |

接口响应可为数组，或包含 `items`/`list`/`data.items` 的对象。热榜项需要 `keyword`，可选 `rank`、`hot_value`、`url`；视频项需要 `id`、`title`、`url`、`author`、`like_count`、`published_at`、`description`。`published_at` 接受 ISO 8601 或 Unix 秒级时间戳。

## GitHub Actions 与 Pages

1. 在 GitHub 新建空仓库，然后在本目录执行 `git init`、`git add .`、首次提交并推送到默认分支。
2. 仓库 **Settings -> Actions -> General** 中，将 Workflow permissions 设为 **Read and write permissions**。
3. 仓库 **Settings -> Secrets and variables -> Actions** 中添加：
   - Secret：`KIMI_API_KEY`（可选）、`DOUYIN_API_TOKEN`。
   - Variable：`KIMI_MODEL`、`KIMI_BASE_URL`（可选）、`DOUYIN_HOT_API_URL`、`DOUYIN_SEARCH_API_URL`。
4. 仓库 **Settings -> Pages** 中选择 **Deploy from a branch**，选择默认分支和 `/docs` 文件夹。
5. 在 Actions 页手动运行一次 **Update daily LOL trends** 验证凭证与数据服务；之后它每天北京时间 09:00（UTC `0:00`）运行。

工作流只在数据有变化时提交 `docs/data/` 与 `pipeline/data/history.sqlite3`。GitHub Pages 监听这次提交并自动刷新。

## 测试

```powershell
py -3.12 -m unittest discover -s pipeline/tests -v
```

测试覆盖来源失败隔离、本地聚类降级、抖音 72 小时过滤/点赞排序/去重，以及 JSON 与 SQLite 写入。
