#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本地 dataset/ 组装成可直接上传 NotebookLM 的“首批”文件组。

设计要点（为什么是“挑”而不是“全给”）：
  1. NotebookLM 单笔记本源数有限（常见 50 个），所以 13,694 个文件必须先合并；
  2. 上游语料存在大量重复，重复源会让模型互相打架：
       - tcmoc/books 下 671 个 .txt 与 tcm-ancient-books 670 个字节级相同 → 只用 .md；
       - tcm-skill/sources 26 本书与 tcm-ancient-books 同名 → 教材部分才用 tcm-skill；
  3. 每个合并文件内按书切分，并给每本书加“来源头”（书名/上游/许可/版本提示），
     这样 NotebookLM 引用时能回指到具体书，而不是指向一个拼盘文件；
  4. 超大、非中医/心理、以及 gmzyjc（课程代号尚未完成映射）留给批次 B。

用法:
    python3 scripts/build_notebook_batch.py                 # 批次 A（默认）
    python3 scripts/build_notebook_batch.py --no-pdf        # 只生成文本，不复制 PDF
    python3 scripts/build_notebook_batch.py --out /tmp/nb   # 指定输出目录

输出:
    <out>/01-....md ...  可直接上传的合并文件
    <out>/<原名>.pdf     中医类 PDF（原样复制，NotebookLM 直接读）
    <out>/MANIFEST.md    上传顺序、每源大小、排除清单、首个提问模板
"""

import argparse
import datetime
import glob
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET = os.path.join(ROOT, "dataset")

# 单个合并文件的软上限：超过就提示拆分；硬上限直接报错（上传大概率失败）
SOFT_CAP = 25 * 1024 * 1024
HARD_CAP = 45 * 1024 * 1024

# NotebookLM 单笔记本源数（不同账号档位不同，按保守值校验）
SOURCE_LIMIT = 50


def upstream(relpath):
    """按路径给出上游仓库与许可/版本提示。"""
    r = relpath
    if r.startswith("_markdown/"):
        return "OpenStax 官方 CNXML，经 scripts/cnxml2md.py 转换 · CC BY 4.0"
    if "tcmoc" in r:
        return "GitHub lab99x/tcmoc（精校 Markdown，按上游声明 CC BY-NC 3.0）"
    if "tcm-ancient-books" in r:
        return "GitHub lab99x/tcm-ancient-books（古籍扫描 OCR 文本 · 公版书 · 非权威校本，引用请核原文）"
    if "tcm-skill" in r:
        return "GitHub thomasxtp/TCM.Skill（现代教材文本 · 有版权 · 仅供本地/私人研习，不随仓库分发）"
    if "ai-books" in r:
        return "github.com/ouyang6559/ai-books（本地 PDF，私人藏书，版权归属上游作者）"
    return "本地资料"


def title_of(relpath):
    """从文件名推出书名/篇名。"""
    name = os.path.basename(relpath)
    stem, _ = os.path.splitext(name)
    # tcm-ancient-books: 457-伤寒论.txt
    if len(stem) > 4 and stem[:3].isdigit() and stem[3] == "-":
        return stem[4:]
    # tcm-skill 教材: 《中医基础理论》.txt / 《中药学》七版.txt
    if stem.startswith("《"):
        return stem
    # tcmoc: (6.1.1-02438.3).本草-本草经-本经辑本.《神农本草经》(三卷).吴普.魏.md
    if "《" in stem:
        title = "《" + stem.split("《", 1)[1]
        if "》" in title:
            title = title[: title.index("》") + 1]
            tail = stem.split("》", 1)[1]
            if tail.endswith(".md") or tail.endswith(".txt"):
                tail = tail[: tail.rfind(".")]
            parts = [p for p in tail.split(".") if p]
            if parts:
                title += "（注者: " + "·".join(parts) + "）"
        return title
    # references: 02-脏象.md
    if stem[:2].isdigit() and stem[2:3] == "-":
        return stem[3:]
    return stem


# 批次配置：每个条目 = 一个 NotebookLM 源（一个合并文件或一个 PDF）
#   out   : 输出文件名（开头序号 = 建议上传顺序）
#   tier  : a = 首批，b = 次批（结构上先支持，内容后续补）
#   books : [(相对 dataset 的路径，可带 glob；None = 用文件名推导书名)]
BATCH = [
    # ---------- 心理学 ----------
    dict(
        out="01-心理学-OpenStax-Psychology-2e.md",
        tier="a",
        why="唯一一部可整书投喂的心理学正文（16 章+前言，217 万字符）；37 本现代心理书只有书目线索，见 books.json",
        books=[
            ("_markdown/psychology-openstax.md", "OpenStax Psychology 2e（心理学导论）"),
        ],
    ),
    # ---------- 现代教材（tcm-skill 独有的 10 部 + 索引层） ----------
    dict(
        out="02-教材-中医基础理论与诊断.md",
        tier="a",
        why="初学者入口：中基+中诊，外加 50 个证型/方证索引 md（references），是全套语料的检索骨架",
        books=[
            ("tcm/textbooks/tcm-skill/sources/《中医基础理论》.txt", None),
            ("tcm/textbooks/tcm-skill/sources/《中医诊断学》.txt", None),
            ("tcm/textbooks/tcm-skill/references/*.md", None),
        ],
    ),
    dict(
        out="03-教材-中药与方剂.md",
        tier="a",
        why="用药与遣方的核心两科；七版教材文本完整，方剂辞典提供术语对齐",
        books=[
            ("tcm/textbooks/tcm-skill/sources/《中药学》七版.txt", None),
            ("tcm/textbooks/tcm-skill/sources/《中药学》.txt", None),
            ("tcm/textbooks/tcm-skill/sources/《方剂学》七版.txt", None),
            ("tcm/textbooks/tcm-skill/sources/方剂辞典.txt", None),
        ],
    ),
    dict(
        out="04-教材-中医内科学.md",
        tier="a",
        why="临床主科，两版内科学互校可减少单版讹误",
        books=[
            ("tcm/textbooks/tcm-skill/sources/《中医内科学》七版.txt", None),
            ("tcm/textbooks/tcm-skill/sources/《中医内科学》.txt", None),
        ],
    ),
    dict(
        out="05-教材-针灸养生与饮食.md",
        tier="a",
        why="外治+养生+食疗，配合本批 PDF 的针灸/足疗书形成可操作层",
        books=[
            ("tcm/textbooks/tcm-skill/sources/《针灸学》.txt", None),
            ("tcm/textbooks/tcm-skill/sources/《中医养生学》.txt", None),
            ("tcm/textbooks/tcm-skill/sources/《中医饮食营养学》.txt", None),
        ],
    ),
    # ---------- 古籍核心（全部取自 tcm-ancient-books，避免与 tcm-skill 重复） ----------
    dict(
        out="06-经典-黄帝内经-素问与灵枢.md",
        tier="a",
        why="理论总源头；素问取古籍库，灵枢原文只有 tcm-skill 有（古籍库只有集注/类纂）",
        books=[
            ("tcm/classics/tcm-ancient-books/437-黄帝内经素问.txt", None),
            ("tcm/textbooks/tcm-skill/sources/黄帝内经灵枢.txt", None),
        ],
    ),
    dict(
        out="07-经典-伤寒论与金匮要略.md",
        tier="a",
        why="辨证论治主干：条文原文 + 注解本 + 桂林古本对照 + 金匮原文与浅注",
        books=[
            ("tcm/classics/tcm-ancient-books/457-伤寒论.txt", None),
            ("tcm/classics/tcm-ancient-books/461-注解伤寒论.txt", None),
            ("tcm/classics/tcm-ancient-books/100-桂林古本伤寒杂病论.txt", None),
            ("tcm/classics/tcm-ancient-books/499-金匮要略方论.txt", None),
            ("tcm/classics/tcm-ancient-books/498-金匮要略浅注.txt", None),
            ("tcm/textbooks/tcm-skill/sources/金匮要略.txt", None),
        ],
    ),
    dict(
        out="08-经典-历代本草三十种.md",
        tier="a",
        why="用药理论层；全部取 tcmoc 精校 Markdown（其 671 个 .txt 与古籍库字节级重复，已排除）",
        books=[("tcm/classics/tcmoc/books/*.md", None)],
    ),
    dict(
        out="09-经典-难经与脉学.md",
        tier="a",
        why="诊法专篇：难经（问难）+ 脉经 + 濒湖脉学，体量小但提问频率高",
        books=[
            ("tcm/classics/tcm-ancient-books/421-八十一难经.txt", None),
            ("tcm/classics/tcm-ancient-books/504-脉经.txt", None),
            ("tcm/classics/tcm-ancient-books/506-濒湖脉学.txt", None),
            ("tcm/textbooks/tcm-skill/sources/难经.txt", None),
        ],
    ),
    dict(
        out="10-经典-针灸.md",
        tier="a",
        why="针灸取穴与配穴的两大主干，与 05 教材、内针 PDF 互相印证",
        books=[
            ("tcm/classics/tcm-ancient-books/299-针灸大成.txt", None),
            ("tcm/classics/tcm-ancient-books/301-针灸甲乙经.txt", None),
        ],
    ),
    dict(
        out="11-经典-温病与方书.md",
        tier="a",
        why="温病条辨补伤寒之外的另一路辨证，方书四部支撑‘选方’类提问",
        books=[
            ("tcm/classics/tcm-ancient-books/526-温病条辨.txt", None),
            ("tcm/classics/tcm-ancient-books/087-医方集解.txt", None),
            ("tcm/classics/tcm-ancient-books/084-汤头歌诀.txt", None),
            ("tcm/classics/tcm-ancient-books/091-成方切用.txt", None),
            ("tcm/classics/tcm-ancient-books/601-医学心悟.txt", None),
        ],
    ),
    dict(
        out="12-经典-临证名著.md",
        tier="a",
        why="医宗金鉴+景岳全书+千金方等综合典籍，覆盖内/外/妇/儿杂病与医理汇通",
        books=[
            ("tcm/classics/tcm-ancient-books/575-医宗金鉴.txt", None),
            ("tcm/classics/tcm-ancient-books/637-景岳全书.txt", None),
            ("tcm/classics/tcm-ancient-books/532-备急千金要方.txt", None),
            ("tcm/classics/tcm-ancient-books/570-丹溪心法.txt", None),
            ("tcm/classics/tcm-ancient-books/595-医学实在易.txt", None),
            ("tcm/classics/tcm-ancient-books/587-石室秘录.txt", None),
            ("tcm/classics/tcm-ancient-books/204-医林改错.txt", None),
        ],
    ),
    dict(
        out="13-养生与情志-身心调摄.md",
        tier="a",
        why="与心理学主线衔接：养生/导引/性命修炼文本，是中医‘情志—身形’叙事的原文底座",
        books=[
            ("tcm/classics/tcm-ancient-books/547-养生秘旨.txt", None),
            ("tcm/classics/tcm-ancient-books/548-养生导引法.txt", None),
            ("tcm/classics/tcm-ancient-books/554-养生类要.txt", None),
            ("tcm/classics/tcm-ancient-books/536-性命要旨.txt", None),
        ],
    ),
]

# PDF：原样复制（NotebookLM 直接读 PDF）。only < 45MB 且与中医/心理相关。
PDFS = [
    ("自创41首屡试屡验方.pdf", "a", "验方合集，适合‘某症用何方’的检索型提问"),
    ("三代家传骨伤秘验方.pdf", "a", "骨伤验方，与 12 医宗金鉴骨伤篇、足疗 PDF 互证"),
    ("黄帝内针 用针指南.pdf", "a", "内针取穴操作；46MB 接近上限，上传失败就先跳过它"),
    ("中药泡脚治百病.pdf", "a", "外治法，条目化程度高、检索收益大"),
    ("足底疗法治百病.pdf", "a", "足部反射区，与足疗图解成对"),
    ("足疗技术完全图解.pdf", "a", "图解版，NotebookLM 主要吃文字、图会丢，仍保留做文字说明源"),
    ("足部保健刮痧疗法.pdf", "a", "刮痧操作，补齐外治手法"),
    ("丹经指南-对照版.pdf", "a", "身心/丹道文本，与 13 养生组衔接（对照版字形更利于检索）"),
]

# 明确排除（写进 MANIFEST，避免以后重复纠结）
EXCLUDED = [
    ("tcmoc 的 671 个 .txt", "与 tcm-ancient-books 670 个字节级相同 → 只保留 tcmoc 的 30 个 .md"),
    ("tcm-skill 中 26 本同名古籍", "与 tcm-ancient-books 重复（本草纲目/伤寒论/温病条辨/针灸大成等）→ 教材部分才用 tcm-skill"),
    ("tcm-ancient-books 其余约 660 本", "批次 B：按 12 个一级类别合并成文件后再传（全量 252MB 文本 ≈ 1.6 亿字，首批先不塞）"),
    ("gmzyjc（光明中医 5,672 文件 / 22MB 文本）", "课程代号→课程名映射尚未完成，且混有校报/人物名单/李可专辑等非课程内容 → 批次 B 先补映射表"),
    ("《生辰数字化解癌症秘术》52MB / 60年疑难杂症 91.6MB / 古法八宅 107MB", "均超 NotebookLM 单文件上限；且后两者非心理、非本批主线"),
    ("风水、奇门、神相、周易、神咒、养殖、老A回忆录 PDF", "与‘中医+心理’主线无关"),
]


def expand(pattern):
    """展开相对 dataset 的路径（支持 glob），返回按名排序的绝对路径列表。"""
    if any(ch in pattern for ch in "*?["):
        hits = sorted(glob.glob(os.path.join(DATASET, pattern)))
        return hits
    p = os.path.join(DATASET, pattern)
    return [p] if os.path.exists(p) else []


def fmt_size(n):
    return f"{n / 1024 / 1024:.1f} MB"


def main():
    ap = argparse.ArgumentParser(description="组装 NotebookLM 首批上传文件")
    ap.add_argument("--out", default=os.path.join(ROOT, "notebook-batch"))
    ap.add_argument("--tier", default="a", help="包含哪些批次：a / ab（默认 a）")
    ap.add_argument("--no-pdf", action="store_true", help="不复制 PDF，只生成合并文本")
    args = ap.parse_args()

    outdir = args.out
    os.makedirs(outdir, exist_ok=True)

    missing = []
    used = set()          # 全局：同一输入不允许进两个输出（防重复源）
    rows = []             # MANIFEST 表格数据

    entries = [e for e in BATCH if e["tier"] in args.tier]

    for entry in entries:
        parts = []
        titles = []
        for pattern, forced_title in entry["books"]:
            files = expand(pattern)
            if not files:
                missing.append(pattern)
                continue
            for f in files:
                rel = os.path.relpath(f, DATASET)
                if rel in used:
                    continue          # 已在别的输出里出现过 → 跳过，保证不重复
                used.add(rel)
                title = forced_title if (forced_title and len(files) == 1) else title_of(rel)
                try:
                    with open(f, "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                except OSError as exc:
                    missing.append(f"{pattern} ({exc})")
                    continue
                if not text.strip():
                    continue
                parts.append(
                    "\n\n---\n\n"
                    f"## {title}\n\n"
                    f"> 来源: `{rel}`  \n"
                    f"> 上游: {upstream(rel)}\n\n"
                    + text
                )
                titles.append(title)
        if not parts:
            continue

        body = (
            f"# {entry['out'][:-3]}\n\n"
            f"> NotebookLM 首批合并源 · 由 scripts/build_notebook_batch.py 生成 · "
            f"含 {len(titles)} 部内容 · 上传后引用请落到下面各书的 `## 书名` 小节\n"
            + "".join(parts)
        )
        outpath = os.path.join(outdir, entry["out"])
        with open(outpath, "w", encoding="utf-8") as fh:
            fh.write(body)
        size = os.path.getsize(outpath)
        if size > HARD_CAP:
            print(f"[错误] {entry['out']} = {fmt_size(size)} 超过硬上限 {fmt_size(HARD_CAP)}，请拆分", file=sys.stderr)
            return 2
        if size > SOFT_CAP:
            print(f"[警告] {entry['out']} = {fmt_size(size)} 超过软上限，NotebookLM 处理可能变慢")
        rows.append((entry["out"], "文本", fmt_size(size), len(body), len(titles), entry["why"]))

    # PDF 复制
    if not args.no_pdf:
        for name, tier, why in PDFS:
            if tier not in args.tier:
                continue
            src = os.path.join(DATASET, "local", "ai-books", name)
            if not os.path.exists(src):
                missing.append(f"local/ai-books/{name}")
                continue
            dst = os.path.join(outdir, name)
            if os.path.abspath(src) != os.path.abspath(dst):
                shutil.copy2(src, dst)
            rows.append((name, "PDF", fmt_size(os.path.getsize(dst)), "-", 1, why))

    if missing:
        print("[错误] 以下输入不存在：", file=sys.stderr)
        for m in missing:
            print(f"    {m}", file=sys.stderr)
        return 2

    rows.sort(key=lambda r: r[0])
    n_src = len(rows)
    txt_mb = sum(os.path.getsize(os.path.join(outdir, r[0])) for r in rows if r[1] == "文本")
    pdf_mb = sum(os.path.getsize(os.path.join(outdir, r[0])) for r in rows if r[1] == "PDF")

    warn = "" if n_src <= SOURCE_LIMIT else f"\n> ⚠️ **{n_src} 源已超过常见上限 {SOURCE_LIMIT}**，请分笔记本上传。\n"
    manifest = [
        "# NotebookLM 首批上传清单",
        "",
        f"- 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 源数: **{n_src}**（常见单本上限 {SOURCE_LIMIT}）· 文本 {fmt_size(txt_mb)} · PDF {fmt_size(pdf_mb)}",
        f"- 生成命令: `python3 scripts/build_notebook_batch.py`",
        warn,
        "## 上传顺序（按文件名序号）",
        "",
        "| # | 文件 | 类型 | 大小 | 字符数 | 内含 | 为什么进首批 |",
        "|---|------|------|------|--------|------|--------------|",
    ]
    for i, (name, kind, size, chars, n, why) in enumerate(rows, 1):
        manifest.append(f"| {i} | `{name}` | {kind} | {size} | {chars} | {n} 部 | {why} |")

    manifest += [
        "",
        "## 明确排除（及原因）",
        "",
        "| 对象 | 原因 |",
        "|------|------|",
    ]
    for what, why in EXCLUDED:
        manifest.append(f"| {what} | {why} |")

    manifest += [
        "",
        "## 上传后立刻提的第一个问题",
        "",
        "```text",
        "以下是本次知识库的来源：中医古籍（扫描 OCR，非权威校本）、现代中医教材（有版权，仅本笔记本私人研习）、",
        "OpenStax 心理学（CC BY 4.0）。回答时：",
        "1) 先区分“古籍原文怎么说 / 现代教材怎么说 / 心理学怎么说”，冲突处明确指出；",
        "2) 每个结论标注来源书名与所在小节（## 书名）；",
        "3) 不确定就说不确定，不要用古籍语气编造条文。",
        "```",
        "",
        "完整提问模板与注意事项见 `docs/feeding-ai.md`。",
        "",
    ]
    with open(os.path.join(outdir, "MANIFEST.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(manifest))

    print(f"✅ 生成 {n_src} 个源 → {outdir}")
    print(f"   文本 {fmt_size(txt_mb)} · PDF {fmt_size(pdf_mb)}")
    for name, kind, size, chars, n, _ in rows:
        print(f"   [{kind}] {size:>9}  {name}")
    if n_src > SOURCE_LIMIT:
        print(f"⚠️  源数 {n_src} 超过常见上限 {SOURCE_LIMIT}，请分笔记本上传", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
