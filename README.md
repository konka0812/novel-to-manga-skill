# 小说转漫画 Skill（novel-to-manga-skill）

把小说整理成可生产、可断点续跑、角色和场景一致、分镜有少年漫节奏的漫画工程。

这个 Skill 不只是提示词合集，而是一套固定目录 + 阶段停靠 + ID 引用 + 设定图参考 + 逐页日志的生产流程：

```text
小说拆解 → 设定图 → 章节分镜 → 逐页漫画 → PDF 成书
```

适合把一部合法持有、有权使用的小说改编成日式页漫、国风页漫或条漫。

## 能力

- **单章生产**：默认一次只做一章，避免一口气把整本书跑爆。
- **设定图先行**：先做人物三视图、表情集、场景锚点图，再生成漫画页。
- **角色一致性**：漫画页强制传入参考图，并把参考图用途写进提示词。
- **分镜工程化**：每格有 ID、景别、机位、台词、旁白、连续性备注。
- **动态分镜**：拒绝每页都排成整齐 2x2 或四条等宽横格，优先用大小格错落、斜切格、出血格和满页 splash。
- **断点续跑**：所有产物落盘，`生成日志.md` 记录完成、失败、无字页。
- **页级重生**：改单页提示词后可只重出单页，旧图自动保留备份。

## 安装到 Codex Skills

```powershell
git clone https://github.com/konka0812/novel-to-manga-skill.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force .\novel-to-manga-skill "$env:USERPROFILE\.codex\skills\novel-to-manga"
```

macOS / Linux:

```bash
git clone https://github.com/konka0812/novel-to-manga-skill.git
mkdir -p ~/.codex/skills
cp -R novel-to-manga-skill ~/.codex/skills/novel-to-manga
```

然后让 Codex 读取：

```text
把这本小说转成漫画，先做第 1 章
```

## 推荐模型

**优先使用：`gpt-image-2.0`。**

- 页漫单页推荐：`1024x1536`
- 质量：`high`
- 单页只做一次图像生成任务，不要一次生成多页
- 如果你的图像后端只暴露旧别名 `gpt-image-2`，可以回退使用它；但 Skill 默认提示词和文档应优先写 `gpt-image-2.0`
- 需要角色一致性时，务必传入设定图/三视图/场景机位图作为参考图

如果使用 Codex 内置 imagegen，可以直接由 Agent 调用图像生成工具。  
如果使用 OpenAI 兼容 API，可配置下面这些环境变量：

| 变量 | 说明 |
|---|---|
| `IMAGE_API_KEY` | 图像 API Key |
| `IMAGE_API_BASE` | OpenAI 兼容 API 根地址，默认 `https://api.openai.com/v1` |
| `IMAGE_MODEL` | 默认 `gpt-image-2.0` |

不要把 API Key 或私有网关地址写进提示词、日志、工程目录或 Git 提交。

## 快速开始

```powershell
python .\scripts\init_project.py "你的小说名"
# 把小说原文放进：
# <你的小说名>-漫画工程/原著/原文.txt
```

然后按四个阶段推进：

| 阶段 | 产出 | 是否停靠确认 |
|---|---|---|
| S1 全书拆解 | `01-设定/设定总表.md` | 是 |
| S2 设定图 | 人物 / 场景 PNG | 是 |
| S3 单章分镜 | `02-分镜/CH001/分镜脚本.md` | 是 |
| S4 单章出页 | `03-漫画页/CH001/*.png` | 出完本章即停 |

## 工程结构

```text
<小说名>-漫画工程/
├── 原著/
├── 01-设定/
│   ├── 设定总表.md
│   └── 设定图/
│       ├── 人物/
│       └── 场景/
├── 02-分镜/
│   └── CH001/
│       ├── 分镜脚本.md
│       └── prompts/
├── 03-漫画页/
│   └── CH001/
├── 04-成书/
└── 生成日志.md
```

## 使用内置 API 脚本

可选。如果你已经有 OpenAI 兼容图像 API，可这样生成单页：

```powershell
$env:IMAGE_API_KEY = "<your-api-key>"
$env:IMAGE_API_BASE = "https://api.openai.com/v1"

python .\scripts\generate_image.py `
  --prompt-file .\02-分镜\CH001\prompts\CH001-P001.txt `
  --out .\03-漫画页\CH001\CH001-P001.png `
  --model gpt-image-2.0 `
  --size 1024x1536 `
  --quality high `
  --ref .\01-设定\设定图\人物\CHARACTERS-全员.png `
  --ref .\01-设定\设定图\场景\LOC-教室-机位图.png
```

参考图建议：

1. 全员设定图，作为角色一致性总锚。
2. 当前场景全景图或机位图。
3. 出场角色三视图 / 状态变体图。

参考图数量不设硬上限（API 支持多图），按清单必传项全传，按锚点强度排序：
角色专属设定图 > 全员图 > 场景/机位图。真正的约束是请求体体积与锚点保真——
参考图传入前统一压缩（工具脚本已内置），单页超过 6 张后若出现角色漂移，
优先裁切合并低区分度锚，而不是砍清单项。

## 分镜规则亮点

`references/storyboard-guide.md` 内置了少年漫页漫节奏：

- 每页至少一次尺寸对比：大格承载情绪，小格压缩节奏。
- 动作页使用斜切格、速度线、出血格、贯通横格。
- 每页最后一格留钩子，翻页第一格揭示。
- 满页 splash 只留给章节最重情绪点。
- 禁止默认 2x2 网格，也禁止四格等宽等高从上排到下。

## 维护纪律

同类规则散在 SKILL.md、references 指南、README 与内置脚本四处：修改任一处时，
其余各处必须同批改完再提交，避免文档与脚本行为不一致。

## 版权与安全

- 只处理你合法持有、有权改编的小说。
- 不要把受版权保护的整本小说上传到公开仓库。
- 分析产物应是转化性设定文档，不要整段复制原文。
- 生成日志、提示词和示例中不要包含 API Key、私有网关地址或其他凭据。

## License

MIT。欢迎二次修改，但请保留版权声明。
