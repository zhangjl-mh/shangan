# 我要上岸

本项目是一个本地优先的公考备考工作台，集中管理：

- 每日时政
- 申论学习内容
- 行测学习内容

## 启动

```bash
npm install
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000)。

## 页面

- `/`：学习驾驶舱
- `/news`：每日时政
- `/shenlun`：申论内容
- `/xingce`：行测内容

## 内容工作流

业务技能位于 `agents/skills/`：

| 请求 | Skill |
| --- | --- |
| 今日扫描、每日时政、更新资讯 | `agents/skills/daily-news/SKILL.md` |
| 补全申论、补全行测、整理学习路线 | `agents/skills/study-content/SKILL.md` |

每日时政数据写入：

```txt
content/local/news/YYYY-MM-DD.json
content/local/markdown/YYYY-MM-DD-daily-news.md
content/local/scan/YYYY-MM-DD.json
```

完成数据整理后执行：

```bash
python scripts/today_scan.py --date YYYY-MM-DD
npm run typecheck
npm run build
```

页面只读取本地文件，不在浏览器中启动扫描、调用模型或抓取外部网站。
