# 从原始资料到 AI 知识库

目标：把 `dataset/` 里的 txt / md / PDF 变成 AI 能准确回答问题的知识库，尽量不产生幻觉。

---

## 0. 三条路线，按投入排序

| 路线 | 成本 | 适合谁 | 能做什么 |
| --- | --- | --- | --- |
| A. 直接上传 | 0，10 分钟 | 所有人，先跑通 | NotebookLM / ChatGPT / Claude 直接传文件问答 |
| B. 本地 RAG | 半天 | 想长期用、数据不想出本机 | 向量检索 + 增强生成，可反复追问 |
| C. 微调 | 数天 + GPU | 想让模型"长成"某个医家的口吻 | 全量文本继续预训练 |

**新手建议顺序：A → 觉得不够准再 B。C 现阶段跳过。**

---

## 1. 先把素材变成纯文本（关键步骤）

`dataset/` 里不同来源的可用度差别很大：

| 素材 | 格式 | 处理 |
| --- | --- | --- |
| `tcm/classics/tcmoc/**/*.md` | 干净 Markdown | ✅ 直接可用，零处理 |
| `tcm/classics/tcm-ancient-books/*.txt` | 纯 txt | ✅ 直接可用，零处理 |
| `tcm/textbooks/gmzyjc/**` | txt/md | ✅ 直接可用 |
| `tcm/textbooks/tcm-skill/**` | md | ✅ 直接可用 |
| `psychology/openstax-psychology/modules/**` | Connexion XML | ⚠️ 需转换（见 1.2） |
| `local/ai-books/*.pdf` | 文字版 PDF | → MinerU（见 1.3） |
| 古籍扫描件 / 长图 | 图片型 PDF | → Umi-OCR（见 1.4） |

### 1.1 查看合并结果

```bash
scripts/build_dataset.sh
cat dataset/MANIFEST.md        # 文件数、体积、扩展名统计
find dataset -name "*.md" | head
```

### 1.2 OpenStax 心理学：用成品 PDF 更省事

`osbooks-psychology` 仓库里是教材源文件（XML），不是正文。两条路：

- **推荐**：直接从官网下载成品 PDF/EPUB —— <https://openstax.org/details/books/psychology-2e>（免费，需登录后下载），然后走 1.3 的 MinerU 流程。
- 或从源文件抽取正文：

```bash
cd dataset/psychology/openstax-psychology
python3 - <<'PY'
import re, pathlib, html
out = pathlib.Path("../../psychology-openstax.md")
parts = []
for f in sorted(pathlib.Path("modules").rglob("*.xhtml")) + sorted(pathlib.Path("modules").rglob("*.html")):
    text = f.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    parts.append(html.unescape(re.sub(r"[ \t]+", " ", text)))
out.write_text("\n\n".join(parts), encoding="utf-8")
print(out, out.stat().st_size, "bytes")
PY
```

### 1.3 文字版 PDF → Markdown（MinerU）

[MinerU](https://github.com/opendatalab/MinerU)（Magic-PDF）是目前处理双栏论文、公式图表教材效果最好的开源方案。

```bash
# 安装（推荐独立虚拟环境）
python3 -m venv ~/.venvs/mineru
source ~/.venvs/mineru/bin/activate
pip install -U "mineru[core]"

# 单个文件
mineru -p input.pdf -o output_dir -m auto

# 批量：把 dataset/local/ai-books 里的 PDF 全转一遍
mkdir -p dataset/_markdown
find dataset -name "*.pdf" -print0 | while IFS= read -r -d '' f; do
  mineru -p "$f" -o dataset/_markdown -m auto || echo "失败: $f"
done
```

产出为每页 Markdown + 内容清单 `content_list.json`，中文书籍识别准确率较高。

> 机器上没有 GPU 也能跑，用 `-m auto` 会自动选择 CPU/GPU 后端，只是慢。

### 1.4 扫描件 OCR（Umi-OCR）

无法选中文字的古籍扫描件、长图，先用 [Umi-OCR](https://github.com/hiroi-sora/Umi-OCR) 离线批量识别成文本（免费开源，支持 macOS/Windows）。批量识别后得到的 txt 与 1.3 的产出合并进 `dataset/_markdown/` 即可。

命令行替代方案（macOS/Linux）：

```bash
# 已装 tesseract 中文语言包时
brew install tesseract tesseract-lang
tesseract "扫描页.png" stdout -l chi_sim+eng --psm 6 > page.txt
```

---

## 2. 路线 A：直接上传建知识库（推荐起步）

### 2.1 NotebookLM（Google）

1. 打开 <https://notebooklm.google.com/> 新建笔记本
2. 上传 PDF / TXT / Markdown（单个笔记本上限约 50 个来源）
3. 用下面的提示词提问，它会**只基于你上传的资料**回答并给出引用

**提示词模板（中医）**：

```
你是中医学习助手。只依据我上传的资料回答，资料中没有的内容
必须明确说"资料中未提及"，禁止补充你自己的记忆或推测。
回答时标注来源文件名与篇章。
【资料版本说明】古籍原典来自 xiaopangxia/TCM-Ancient-Books 与
lab99x/tcmoc；教材知识库来自 YuanZHAO321/TCM.Skill（CC BY-NC 4.0）。
若同一问题不同资料说法不一致，分别列出并注明出处。
问题：……
```

**提示词模板（心理学）**：

```
You are a study assistant. Answer ONLY from the uploaded OpenStax
Psychology 2e materials. Cite chapter/section for every claim. If the
material does not cover it, say "not covered in the source" instead of
guessing. Question: ...
```

### 2.2 ChatGPT / Claude 直接传文件

- 适合 5–20 个文件的小规模场景，超出上下文会被截断
- 同样在提示词里写明"只依据上传文件作答 + 标注来源 + 不知就说不知"

### 2.3 为什么这样能压幻觉

1. **限定资料范围** → 模型没有"自由发挥"的空间
2. **要求标注来源** → 你可以回头验证
3. **明示版本差异** → 避免把 1985 函授版教材和新世纪规划教材的说法混着答

---

## 3. 路线 B：本地 RAG（数据不出本机）

古籍全集超过任何模型的上下文窗口（`tcmoc` 173MB、`tcm-ancient-books` 80MB），必须分块检索。

### 3.1 分块参数建议

| 参数 | 中医古籍 | 现代教材 | 心理学教材 |
| --- | --- | --- | --- |
| chunk_size | 500–800 字 | 800–1200 字 | 800–1200 字 |
| overlap | 100 字 | 150 字 | 150 字 |
| 切分边界 | 按篇章/条文（`卷`、`篇`、`条`） | 按标题层级（`#`/`##`） | 按 section |
| embedding | `BAAI/bge-large-zh-v1.5` | 同左 | `BAAI/bge-m3` 或 `text-embedding-3-small` |

**务必把元数据（书名、作者、朝代、分类编号、来源仓库）一起写入每个 chunk**，否则检索回来你不知道是哪本书说的。

### 3.2 最小可运行实现

```bash
pip install llama-index sentence-transformers
```

```python
# rag.py —— 对 dataset/ 建索引并提问
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

docs = SimpleDirectoryReader(
    "dataset",
    recursive=True,
    exclude_hidden=True,
    required_exts=[".md", ".txt"],
).load_data()

index = VectorStoreIndex.from_documents(docs)   # 默认本地存 storage/
query = index.as_query_engine(similarity_top_k=6)
print(query.query("黄帝内经里四气调神具体怎么讲的？"))
```

生产化替换项：

- 向量库：Chroma / Qdrant / Milvus（替换 `VectorStoreIndex` 底层）
- 元数据过滤：按 `source` / `category` 字段只检索 `tcm/classics` 或 `psychology`
- 引用回溯：返回时带上 chunk 的原始文件路径

### 3.3 检索效果自查

先准备 10 个**你已知答案**的问题，检查：召回的 chunk 是否真是答案所在、答案有没有被另一个版本的资料污染。不合格优先调 `similarity_top_k` 和切分边界，而不是换模型。

---

## 4. 路线 C：微调（现阶段不推荐）

只有在"要模型稳定输出特定流派的诊疗口吻"时才考虑：

```bash
pip install unsloth   # 单卡 24GB 可跑 LoRA
```

- 中医古籍继续预训练用 `full-text` 目标，教材 QA 用指令格式
- **必须只用公版 / CC 许可 / 自有内容**：`tcm/classics`、`gmzyjc`（公益开放）可用；`tcm-skill`（CC BY-NC）、`openstax`（CC BY-NC-SA）须遵守非商业与相同方式共享；`ai-books`、`restricted` 里的内容不可用于训练后再分发的模型
- 微调前先把评测集准备好，否则无法判断有没有变好

---

## 5. 常见坑

1. **版本混用**：同一条方剂在光明中医 1985 版和七版教材里剂量可能不同 → 务必在提示词/元数据里保留版本
2. **繁简与异体字**：古籍多繁体、异体字，embedding 模型对繁简不敏感 → 建议保留原文 + 额外存一列简体，检索用简体、展示用原文
3. **古籍异名**：《素问》《黄帝内经素问》《重广补注黄帝内经素问》是同一书 → 统一别名表，检索时扩展
4. **PDF 转换残留**：MinerU 对竖排古籍版式效果会下降，转完抽查 10 页
5. **LFS 指针文件**：`local/ai-books` 若同步时用了 `--no-lfs`，PDF 只是 130 字节的指针文本，无法解析
6. **把整本 PDF 直接塞进上下文**：超过窗口会被静默截断，看起来"答了"其实模型根本没读到后半本

---

## 6. 检查清单

- [ ] `scripts/validate_catalog.py` 通过
- [ ] `scripts/sync.sh` 完成，`data/` 下所需源齐全
- [ ] `scripts/build_dataset.sh` 生成 `dataset/MANIFEST.md`，文件数符合预期
- [ ] PDF 已用 MinerU/OCR 转成 md/txt 并放入 `dataset/_markdown/`
- [ ] 提示词里写明了资料版本与"只依据上传资料作答"
- [ ] 准备了 10 个已知答案的问题做过人工验证
- [ ] 知识库仅个人使用，未公开再分发受许可限制的内容
