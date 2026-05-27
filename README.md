# 我要上岸

公考智能备考驾驶舱。应用可运行在本机或单实例服务器，读取 Codex / Claude Code Skills 或后续 Python Pipeline 写入的文件 JSON 内容，并提供阅读、筛选、画像编辑与浏览器 PDF 导出能力。

## 先用这几个命令

安装并启动页面：

```bash
npm install
python -m pip install -r requirements.txt
npm run dev
```

在 Codex / Claude Code 中说：

```txt
今日扫描
```

该工作流会整理当天权威时政，并扫描符合画像的官方岗位，最终写入页面读取的 JSON 和 Markdown 文件。

已有当日资讯 JSON 后，也可以直接执行本地收口与官方岗位附件同步：

```bash
npm run scan:today
```

指定日期：

```bash
npm run scan:today -- --date 2026-05-27
```

若不存在 `data/profile.local.json`，命令会先运行 `scripts/ensure_profile.py`，在终端询问学历、专业、毕业年份、学位、政治面貌、目标地区等岗位筛选信息，保存本地画像后继续岗位扫描。也可以单独执行：

```bash
npm run agent:profile
```

## 当前实现

- `/`：水墨风驾驶舱首页，读取画像、时政、岗位和学习路线摘要。
- `/shenlun`：申论学习路线、资料、建议与输出成果布局。
- `/xingce`：行测模块及本地路线承载页。
- `/job`：岗位判断工作台，展示匹配度、风险、备考建议、待遇/住房/户口口径及官方信源，支持筛选与个人跟踪状态。
- `/news`：按日期展示本地时政报告，以左侧标题、右侧详情阅读，支持来源/主题筛选、关键词搜索及 Markdown 下载。
- `/profile`：编辑并保存本地用户画像。

页面没有内容时只显示空状态，不展示演示岗位或虚构信源。

## 快速启动

```bash
npm install
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000)。

构建检查：

```bash
npm run typecheck
npm run build
```

初始化学习内容：

```bash
npm run content:seed
```

该命令会将版本管理中的申论、行测基础知识库首次生成到 `content/local/`；若本地已有 Skills 生成的内容，则保留已有文件而不覆盖。

`scan:today` 会先检查或交互创建本地画像，再运行 `scripts/import_national_jobs.py`，从国家公务员局、石家庄市人社局与中国雄安官网的官方岗位附件同步能够确认的全部岗位，读取可核验的最低进面分，并核查下一招录年度国考专题是否发布，最后对当日时政及岗位 JSON 做校验并生成报告。其他事业单位、国企等岗位由 `agents/skills/today-scan/SKILL.md` 按官方原文全渠道追加核验。

该命令不会调用模型。`ensure_profile.py` 仅在本地创建画像；`import_national_jobs.py` 仅访问登记的官方附件并进行确定性筛选；`today_scan.py` 不联网，仅校验 Agent / Skill 已整理的时政与岗位 JSON，并输出 Markdown 与本次扫描清单。前端页面本身始终不发起采集任务。

石家庄与雄安的年度岗位表为不可变的官方附件，核验下载后会保存于 `content/official/job/source-files/`。若官方站点临时发生 TLS 或网络故障，同一年度扫描可读取该官方原始快照复现筛选结果；公告原文 URL 始终保留在岗位记录中。

## 数据边界

前端不采集招聘或时政信息，不调用模型，也不触发 Agent。它仅写入用户自己的本地状态：

```txt
data/profile.local.json
data/job-tracking.local.json
```

Skills 或 Pipeline 负责生成业务内容：

```txt
content/local/shenlun/roadmap.json
content/local/xingce/roadmap.json
content/local/news/YYYY-MM-DD.json
content/local/job/eligible-jobs.json
```

产品运行时没有 mock 或 official 示例数据回退。

申论模块另提供经公开来源整理、可版本管理的基础知识库：

```txt
content/library/shenlun/roadmap.json
```

读取顺序为 `content/local/shenlun/roadmap.json` 优先，其次为基础知识库。基础知识库不是示例数据：其中考试事实依据标注官方大纲来源，题型技巧标注公开培训机构或公开辅导资料来源；后续 Skills 可生成个性化 `local` 路线覆盖展示。

## 申论学习中心

`/shenlun` 当前覆盖：

```txt
考试依据与三类试卷能力地图
七阶段学习路线
六步通用作答流程
归纳概括、综合分析、提出对策、贯彻执行、申发论述五类题型技法
三遍材料阅读法与要点加工
常见应用文文种
大作文立意、结构与论证方法
主题表达素材
八周系统计划与三周冲刺计划
考场时间安排与复盘清单
官方及机构公开参考来源
Markdown / PDF 导出
```

申论知识库 Schema 位于：

```txt
agents/schema/shenlun-roadmap.schema.json
```

## 行测训练中心

`/xingce` 基础知识库位于 `content/library/xingce/roadmap.json`，覆盖官方大纲列示的政治理论、常识判断、言语理解与表达、数量关系、判断推理、资料分析六个板块，并提供方法、速算关系、训练路线和考场节奏。其 Schema 位于：

```txt
agents/schema/xingce-roadmap.schema.json
```

与申论相同，`content/local/xingce/roadmap.json` 存在时优先展示个性化本地内容。

## 岗位范围

岗位页承载当前采集到、且已由 Skills 依据本地画像判断为符合报考条件的岗位。目标地区属于用户本地画像信息，不在公开仓库文档或示例数据中固化。

允许的岗位类别包括公务员、事业单位、教师、医疗卫生、军队文职、社区工作者与官方发布的国有企业正式岗位。国企岗位应排除劳务派遣、外包与无法回溯官方信源的转载信息。

岗位数据协议位于：

```txt
agents/schema/eligible-jobs.schema.json
```

权威岗位渠道清单位于：

```txt
data/job-sources.json
```

每次由 Skills 扫描后，应在本地岗位报告中记录实际访问渠道、命中公告和排除原因；页面展示已确认符合画像的真实岗位，并以 `报名中`、`即将报名`、`已截止`、`已结束` 准确区分当前是否可报。

每条岗位必须带官方来源 URL 和采集时间。符合画像的岗位即使报名已经结束，也保留为历史参考并准确标记状态，便于后续比较。岗位详情支持整理：

```txt
岗位代码、公告工作内容、经标注的职责归纳、学历/专业/资格、报名与考试时间
公告备注和报考要点
同岗位或高度可比岗位的历年进面/入围分、报录比、招录人数
官方待遇信息，或清楚标记为非官方承诺的薪资推算区间
```

进面分、报录比只采用官方公告、官方公示或用人单位正式发布的可追溯信息；薪资未公布金额时，页面可按地区与岗位类别显示宽区间推算，但必须标记为非招录机关待遇承诺，不拼凑论坛数据。

### 2026-05-27 岗位扫描结果

本轮从官方附件中筛选出 `40` 个可供判断的历史岗位：国家公务员局国考岗位 `9` 个、石家庄指定区县事业单位岗位 `14` 个、雄安新区事业单位岗位 `17` 个。全部岗位均已准确标注为已结束；页面用于比较方向、分数与风险，不把历史岗位伪装成当前可报名岗位。

截至 `2026-05-27`，国家公务员局 `2027年度考试录用公务员` 专题入口尚未发布，因此当前没有可导入的官方下一年度国考职位表。页面会在后续扫描时继续检查该入口。

### 岗位数据隐私边界

部署所需的 `content/local/job/` 岗位结果、扫描清单和导出 Markdown 可随项目提交；生成流程不写入姓名、毕业年份或画像哈希等私密字段。原始画像 `data/profile.local.json` 与个人报名跟踪 `data/job-tracking.local.json` 始终不进入版本控制。

## 画像与重新生成

用户可以在页面保存画像，也可以由 Skills 通过问询生成 `data/profile.local.json`。页面不会自动运行 Agent；需要刷新岗位时执行“今日扫描”工作流。

## 时政数据

时政数据协议位于：

```txt
agents/schema/daily-news.schema.json
```

每条热点应保留原文 URL、来源和发布时间。页面提供当前报告的 Markdown 下载，且可以利用浏览器打印能力导出 PDF。

当前已生成按日期归档的本地日报：

```txt
content/local/news/2026-05-26.json
content/local/markdown/2026-05-26-daily-news.md
content/local/news/2026-05-27.json
content/local/markdown/2026-05-27-daily-news.md
```

本期资讯链接在 `2026-05-27` 已逐条访问核验。若当天尚没有取得可核验的权威原文，页面继续显示最近一份已核验日报，不以占位资讯冒充今日数据。

### 2026-05-27 已核验每日时政

本期已收录 5 条当天发布、可访问的权威资讯：

| 主题 | 来源 |
| --- | --- |
| 中宣部召开党的创新理论传播工程推进会 | [人民日报（人民网）](https://politics.people.com.cn/n1/2026/0527/c461001-40727945.html) |
| 最高法发布防范和惩治家庭内部侵害未成年人合法权益典型案例 | [人民日报（人民网）](https://society.people.com.cn/n1/2026/0527/c1008-40727979.html) |
| 公安部网安局重拳整治网络谣言 | [人民日报（人民网）](https://society.people.com.cn/n1/2026/0527/c1008-40727981.html) |
| 国家防总办公室持续组织部署防汛救灾工作 | [人民日报（人民网）](https://society.people.com.cn/n1/2026/0527/c1008-40727953.html) |
| 中国是跨国公司面向未来布局的“必选地” | [人民日报（人民网）](https://finance.people.com.cn/n1/2026/0527/c1004-40727951.html) |

## 今日扫描 Skill

本项目内置扫描技能：

```txt
agents/skills/today-scan/SKILL.md
```

在本项目协作中说“今日扫描”时，工作流为：

```txt
python scripts/ensure_profile.py 检查画像；没有画像则终端问询并保存
↓
读取画像与岗位官方渠道清单
↓
检索当日权威时政，验证原文链接并生成新闻 JSON
↓
python scripts/import_national_jobs.py 同步国考、石家庄与雄安官方附件，并检查下一年度国考入口
↓
扫描岗位官方入口，保留所有确认符合画像的岗位及关键参考来源
↓
python scripts/today_scan.py --date YYYY-MM-DD
↓
前端读取最新文件展示
```

确定性收口脚本会生成：

```txt
content/local/markdown/YYYY-MM-DD-daily-news.md
content/local/markdown/YYYY-MM-DD-job-scan.md
content/local/scan/YYYY-MM-DD.json
```

## 项目 Skills

项目内的数据生产规则现已拆分为可单独调用的业务 Skills，并保留一键组合入口：

| 请求 | Skill |
| --- | --- |
| 今日扫描，同时刷新时政和岗位 | `agents/skills/today-scan/SKILL.md` |
| 每日时政、今日资讯、按日期核验新闻 | `agents/skills/daily-news/SKILL.md` |
| 岗位检索、岗位判断、下一年度国考监测 | `agents/skills/job-scan/SKILL.md` |
| 申论/行测内容、题型技巧与学习路线补全 | `agents/skills/study-content/SKILL.md` |
| 本地画像创建与更新 | `agents/skills/profile-intake/SKILL.md` |

本机开发环境通过 `~/Skills/shangan-workbench` 作为 Codex / Claude Code 的发现入口，并将其链接到当前项目的 `.agents/skills/` 与 `.claude/skills/`。这些链接是本机生成配置，不进入 Git；可部署的业务规则始终保存在上表所列的项目目录中。

## 部署与文件数据架构

应用可以从本机运行迁移到单实例服务器运行，但继续遵守“同一应用读取 JSON 文件”的边界，不增加数据库，也不让浏览器直接访问模型或外部采集任务。

```txt
Codex / Skills（离线或运维触发）
          ↓ 写入
服务器持久化目录：content/local + data
          ↓ Next.js Server Components / Route Handler 读取或保存
浏览器页面（展示、筛选、画像/报名跟踪编辑、导出）
```

开发环境默认读取项目内的 `content/local/` 与 `data/`。部署时建议将两个目录映射到服务器持久化磁盘，并在服务进程中配置：

```env
GONGKAO_CONTENT_DIR=/srv/gongkao/content/local
GONGKAO_DATA_DIR=/srv/gongkao/data
```

这仍然是文件数据架构，不是数据服务拆分。原因是部署发布常会替换应用代码目录；如果画像和 Agent 生成内容只写进发布包，重启或下一次发布可能丢失数据。该方案适合单用户、单实例部署；若未来横向扩容到多个实例，文件一致性需要重新评估。

重要边界：当前产品按“单用户、无登录”设计。部署在可被公众访问的服务器时，`/profile` 与画像保存接口会暴露个人信息的查看和修改能力。上线前必须在应用之外限制访问范围，例如仅内网/VPN 访问，或由反向代理提供访问控制；否则不能存放真实画像数据。

## Token 与安全

未来 Python 自动化路线可在 `.env` 中配置模型 Token；前端不读取或暴露 Token。公开时政、学习内容和已清理私密字段的岗位展示数据可随项目提交；本地画像与报名跟踪文件由 `.gitignore` 排除，避免个人状态进入仓库。
