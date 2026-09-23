# 中医 + 心理学 · 开放资料数据集（喂 AI 用）

把散落在 GitHub / 网络上的**中医古籍、中医教材、心理学开放教材**整理成一份可直接喂给大模型的数据集。

本仓库本身**不存放受版权保护的书籍文件**，它提供三样东西：

1. **`catalog/`** — 经过连通性验证的资料源总目录 + 57 本目标书籍的逐本映射表
2. **`scripts/`** — 一键同步、合并成统一目录、校验目录的脚本
3. **`docs/`** — 从原始 PDF 到 AI 知识库的完整流水线

> 版权边界：只自动同步公版古籍、明确公益开放的教材、CC 许可的开放教材。现代商业出版物（徐文兵、荣格、《身体从未忘记》《被讨厌的勇气》等）一律**只列书目、不搬文件**。

---

## 30 分钟上手（初学者路径）

```bash
# 0. 前置：git、python3；建议装 git-lfs 和 MinerU（见 docs/feeding-ai.md）
git clone https://github.com/ouyang6559/tcm-psych-dataset.git
cd tcm-psych-dataset

# 1. 看看有哪些源（不会下载任何东西）
scripts/sync.sh --list

# 2. 同步全部开放源（约 570MB：古籍 255MB + 教材 238MB + 心理学 88MB）
scripts/sync.sh

# 3. 只同步一个先试试（11.6MB，最快见效）
scripts/sync.sh --only tcm-skill

# 4. 合并成统一数据集 + 自动转 UTF-8 + 生成清单
scripts/build_dataset.sh
cat dataset/MANIFEST.md

# 5. OpenStax 心理学 CNXML → Markdown（16 章 + 前言，含 38 个表格）
python3 scripts/cnxml2md.py dataset/psychology/openstax-psychology \
        -o dataset/_markdown/psychology-openstax.md

# 6. 组装 NotebookLM 首批上传组（合并 + 去重 + 每本书加来源头）
python3 scripts/build_notebook_batch.py
open notebook-batch/MANIFEST.md     # 21 个源、上传顺序、排除原因

# 7. 按 docs/feeding-ai.md §2 喂给 NotebookLM / ChatGPT / 本地 RAG
```

生成的数据集结构：

```
dataset/
├── MANIFEST.md                    # 文件数、体积、扩展名统计（目录列到第 3 层）
├── _markdown/
│   └── psychology-openstax.md      # OpenStax《心理学（第二版）》全文（转换生成）
├── tcm/
│   ├── classics/tcm-ancient-books # 701 项古籍，纯 txt（已转 UTF-8）← 首选语料
│   ├── classics/tcmoc             # 分类规范的 Markdown 古籍 ← 最干净
│   └── textbooks/                 # 光明中医教材 + TCM.Skill 教材知识库
├── psychology/openstax-psychology # OpenStax 源文件（CNXML + media）
└── local/ai-books                 # 你已有的 22 个 PDF（走 LFS）
```

> **编码注意**：`tcm-ancient-books` 上游 701 个 txt 全是 GB18030，`build_dataset.sh` 会自动转 UTF-8（`scripts/normalize_encoding.py`），不要手工从 `data/` 拷贝回去。当前实测规模：**13,694 个文件 / 1.4GB**。

---

## 一、资料源目录

完整机器可读版：[`catalog/sources.json`](catalog/sources.json)
人读表格版：[`catalog/sources.md`](catalog/sources.md)

**状态分布**

| 状态 | 数量 | 含义 |
| --- | --- | --- |
| 🔄 自动同步 | 7 | `open` + `local`，`scripts/sync.sh` 默认拉取 |
| ⚠️ 需 `--with-restricted` | 2 | 版权存疑，需自行确认后再拉 |
| 📇 仅索引 / 🌐 网页参考 | 7 | 不同步文件 |

**资料源一览**

| 资料源 | 推荐 | 平台 | 状态 | 范围 |
| --- | --- | --- | --- | --- |
| [TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books) | ★★★★★ | GitHub | 自动同步 | 近 700 项公版中医古籍，纯 txt |
| [TCMOC 中医开源医典](https://github.com/lab99x/tcmoc) | ★★★★★ | GitHub | 自动同步 | 按《中国中医古籍总目》12 大类整理的 Markdown 古籍 |
| [光明中医教材](https://github.com/6830920/gmzyjc) | ★★★★★ | GitHub | 自动同步（已归档） | 21 门课程、近 800 万字公益教材 |
| [OpenStax Psychology 2e](https://github.com/openstax/osbooks-psychology) | ★★★★★ | GitHub | 自动同步 | 同行评审的开放心理学教材源文件 |
| [OpenTCM](https://gitee.com/opentcm) | ★★★★★ | Gitee | 仅索引 | 古籍数据库、检索、电子书工具集 |
| [TCM.Skill](https://github.com/YuanZHAO321/TCM.Skill) | ★★★★☆ | GitHub | 自动同步 | 四部规划教材知识库，CC BY-NC 4.0 |
| [倪海厦中医资料](https://github.com/Lance-myk/Traditional-Chinese-Medicine-nihaisha) | ★★★★☆ | GitHub | 需 `--with-restricted` | 人纪/天纪讲义视频，520MB，版权待确认 |
| [NiHaisha-Agent](https://github.com/Lance-myk/NiHaisha-Agent) | ★★★★☆ | GitHub | 需 `--with-restricted` | 基于倪海厦资料的 AI 知识库，参考其 RAG 组织 |
| [光明中医 Gitee 镜像](https://gitee.com/zhyh1105/gmzyjc) | ★★★★☆ | Gitee | 默认跳过（重复） | 与 GitHub 源重复 218MB，`--only gitee-gmzyjc` 才拉 |
| [ai-books](https://github.com/ouyang6559/ai-books) | ★★★★☆ | GitHub | 自动同步（LFS） | 你已有的 22 个 PDF |
| [books-2](https://github.com/KnowNo/books-2) | ★★★☆☆ | GitHub | 仅索引 | 中文书目清单，0.2MB |
| [zh-books](https://github.com/learnuidev/zh-books) | ★★★☆☆ | GitHub | 仅索引 | 中文电子书，441MB |
| [iBook-ebook](https://github.com/zhoulujun/iBook-ebook) | ★★★☆☆ | GitHub | 仅索引 | 心理/认知/情商书目，567MB |
| [Books](https://github.com/holyshell/Books) | ★★★☆☆ | GitHub | 仅索引 | 中文 PDF/EPUB 集合，429MB |
| [NSSD 国家哲社文献中心](https://www.ncpssd.org) | ★★★★☆ | 网页 | 参考 | 哲社期刊论文官方平台 |
| 国医典藏（中国中医科学院） | ★★★★☆ | 网页 | 参考 | 地址待核实后补入 |

**状态说明**

- `open` — 版权清晰（公版 / 公益开放 / CC 许可），`scripts/sync.sh` 默认同步
- `skip_default` — 地址有效但与其他源重复，默认不拉（当前：gitee 镜像）
- `restricted` — 版权存疑或体积过大，需显式 `--with-restricted` 才同步
- `index-only` — 只有书目价值，**不同步文件**（多为现代出版物）
- `reference` / `local` — 网页参考 / 本地已有仓库

**明确排除**：annas-archive.org、Z-Lib 各镜像站。理由见 `catalog/sources.json` 的 `excluded` 字段。

---

## 二、57 本目标书逐本映射

完整版：[`catalog/books.json`](catalog/books.json)（机器可读）/ [`catalog/books.md`](catalog/books.md)（表格）

| 状态 | 数量 | 含义 |
| --- | --- | --- |
| ✅ available | 8 | 有公版原文可直接用于 AI（黄帝内经各篇章原典等） |
| 🔶 related | 12 | 有相关资料但不是你指定的版本（教材知识库、公益教材等） |
| ❌ not_found | 37 | 未找到可确认合法授权的电子版（多为现代商业出版物） |

**关键提示**：`related` 不等于"就是那本书"。例如《中医诊断学》拿到的是 TCM.Skill 的七版教材知识库，不是李灿东/方朝义那个 ISBN 的原版；《中医儿科学》拿到的是 1985 年光明中医函授版，不是新世纪第五版。喂 AI 时请在提示词里注明实际来源与版本，避免模型把两个版本混为一谈。

---

## 三、目录结构

```
tcm-psych-dataset/
├── README.md                  # 本文件：总览与快速开始
├── LICENSE                    # 脚本与目录文件：MIT
├── NOTICE.md                  # 上游内容版权声明（务必先读）
├── catalog/
│   ├── sources.json           # 资料源目录（唯一事实来源）
│   ├── sources.md             # 由脚本生成的人读表格
│   ├── books.json             # 57 本书映射表（唯一事实来源）
│   └── books.md               # 由脚本生成的人读表格
├── scripts/
│   ├── sync.sh                # 同步开放源 → data/（分级: open/restricted/index-only）
│   ├── build_dataset.sh       # 合并 data/ → dataset/ + MANIFEST
│   ├── cnxml2md.py            # OpenStax CNXML → Markdown
│   ├── normalize_encoding.py  # GB18030 → UTF-8 统一转码
│   ├── build_notebook_batch.py # 组装 NotebookLM 首批上传组
│   ├── render_catalog.py      # 从 JSON 生成 Markdown 表格
│   └── validate_catalog.py    # 结构 + URL 校验
├── docs/
│   └── feeding-ai.md          # PDF → Markdown → AI 知识库完整流水线
├── data/                      # 同步下来的内容（不入库）
├── dataset/                   # 合并后的统一数据集（不入库）
└── notebook-batch/            # 首批上传组（生成物，不入库）
```

`data/`、`dataset/`、`notebook-batch/` 都在 `.gitignore` 中，本仓库保持轻量（几百 KB），不会变成 2GB 的聚合仓。

---

## 四、常用操作

```bash
scripts/sync.sh --list                     # 列出所有源及状态
scripts/sync.sh                            # 同步全部 open 源（跳过 skip_default 的重复镜像）
scripts/sync.sh --only tcmoc,tcm-skill     # 只同步指定源
scripts/sync.sh --only gitee-gmzyjc        # 显式拉取被 skip_default 跳过的镜像
scripts/sync.sh --with-restricted          # 追加同步版权存疑的源
scripts/sync.sh --force                    # 强制重新克隆
scripts/sync.sh --no-lfs                   # 跳过 LFS 大文件

scripts/build_dataset.sh                   # 合并成 dataset/（含 UTF-8 转码）
scripts/build_dataset.sh --clean           # 清空后重建
NO_NORMALIZE=1 scripts/build_dataset.sh    # 跳过编码归一化

python3 scripts/validate_catalog.py              # 校验目录结构
python3 scripts/validate_catalog.py --check-urls # 追加网络可达性检查
python3 scripts/build_notebook_batch.py          # 生成 notebook-batch/（21 个上传源）
python3 scripts/build_notebook_batch.py --no-pdf # 只要文本、不复制 PDF
python3 scripts/render_catalog.py                # 改了 JSON 后重新生成 md 表格
python3 scripts/normalize_encoding.py dataset/ --check   # 检查是否还有非 UTF-8 文件
python3 scripts/cnxml2md.py dataset/psychology/openstax-psychology \
        -o dataset/_markdown/psychology-openstax.md   # OpenStax 转 Markdown
```

---

## 五、推荐工作流

```
scripts/sync.sh                 同步开放源（txt/md 直接可用）
        │
        ├─ txt/md ──────────────────────────────┐
        │                                       │
        └─ PDF（ai-books / OpenStax PDF）       │
                │                               │
                ├─ 文字版 → MinerU → Markdown   │
                └─ 扫描件 → Umi-OCR → 文本      │
                        │                       │
                        └───────┬───────────────┘
                                ▼
                  scripts/build_dataset.sh
                                │
                                ▼
                       dataset/ + MANIFEST.md
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
          NotebookLM      ChatGPT/Claude     本地 RAG
          （上传建知识库）  （直接传文件）    （分块+向量库）
```

细节见 **[`docs/feeding-ai.md`](docs/feeding-ai.md)**：含 MinerU 安装命令、扫描件 OCR 方案、分块参数建议、提示词模板、本地 RAG 最小实现。

---

## 许可

- 本仓库的**脚本与目录文件**：MIT（见 `LICENSE`）
- **同步下来的所有内容**：版权归各自上游，见 `NOTICE.md`。公版古籍可自由使用；CC 许可内容须遵守署名与相同方式共享；标注 `restricted` / `index-only` 的内容请自行确认版权后再使用。
