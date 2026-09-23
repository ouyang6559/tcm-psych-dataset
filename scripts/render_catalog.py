#!/usr/bin/env python3
"""从 catalog/*.json 生成人类可读的 Markdown 表格。

改完 JSON 后运行一次：
    python3 scripts/render_catalog.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"

RATING = {5: "★★★★★", 4: "★★★★☆", 3: "★★★☆☆", 2: "★★☆☆☆", 1: "★☆☆☆☆"}
STATUS_LABEL = {
    "open": "🔄 自动同步",
    "restricted": "⚠️ 需 --with-restricted",
    "index-only": "📇 仅索引",
    "reference": "🌐 网页参考",
    "local": "💻 本地已有",
}
BOOK_STATUS = {
    "available": "✅ available",
    "related": "🔶 related",
    "not_found": "❌ not_found",
}


def load(name: str) -> dict:
    return json.loads((CATALOG / name).read_text(encoding="utf-8"))


def write(name: str, text: str) -> None:
    (CATALOG / name).write_text(text, encoding="utf-8")
    print(f"生成 {name}")


def render_sources(doc: dict) -> str:
    lines = [
        "# 资料源目录",
        "",
        f"> 由 `scripts/render_catalog.py` 生成于 {doc['generated_at']}，"
        "唯一事实来源是 [`sources.json`](./sources.json)，请勿直接编辑本文件。",
        "",
        "## 汇总表",
        "",
        "| 资料源 | 推荐 | 状态 | 平台 | 体积 | 格式 | 范围 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    order = {"open": 0, "local": 1, "restricted": 2, "index-only": 3, "reference": 4}
    for s in sorted(doc["sources"], key=lambda x: (order.get(x["status"], 9), -x["rating"])):
        size = f"{s['size_mb']} MB" if isinstance(s.get("size_mb"), (int, float)) else "—"
        fmt = "/".join(s.get("format") or []) or "—"
        scope = s["scope"].replace("\n", " ").replace("|", "｜")
        if len(scope) > 90:
            scope = scope[:89] + "…"
        verified = "" if s.get("verified") else " ※"
        lines.append(
            f"| [{s['name']}]({s['url']}){verified} | {RATING.get(s['rating'], s['rating'])} "
            f"| {STATUS_LABEL.get(s['status'], s['status'])} | {s['platform']} "
            f"| {size} | {fmt} | {scope} |"
        )

    lines += ["", "## 详细说明", ""]
    for s in doc["sources"]:
        lines += [
            f"### {s['name']}（{s['name_zh']}）",
            "",
            f"- **ID**：`{s['id']}`",
            f"- **推荐**：{RATING.get(s['rating'], s['rating'])}",
            f"- **状态**：{STATUS_LABEL.get(s['status'], s['status'])}",
            f"- **地址**：{s['url'] or '待核实'}",
        ]
        if s.get("branch"):
            lines.append(f"- **分支**：`{s['branch']}`")
        if isinstance(s.get("size_mb"), (int, float)):
            lines.append(f"- **体积**：约 {s['size_mb']} MB")
        if s.get("archived"):
            lines.append("- **注意**：上游仓库已归档（只读）")
        if not s.get("verified"):
            lines.append("- **注意**：地址未实际连通验证")
        lines += [
            f"- **许可**：{s['license']}",
            f"- **范围**：{s['scope']}",
        ]
        if s.get("dataset_path"):
            lines.append(f"- **数据集路径**：`dataset/{s['dataset_path']}`")
        if s.get("notes"):
            lines.append(f"- **备注**：{s['notes']}")
        lines.append("")

    lines += ["## 明确排除", "", "| 来源 | 理由 |", "| --- | --- |"]
    for e in doc.get("excluded", []):
        lines.append(f"| {e['name']} | {e['reason']} |")

    lines += ["", "## 相关工具", "", "| 工具 | 用途 | 地址 |", "| --- | --- | --- |"]
    for t in doc.get("tools", []):
        lines.append(f"| {t['name']} | {t['use']} | {t['url']} |")

    lines += ["", "\n※ = 未连通验证", ""]
    return "\n".join(lines)


def render_books(doc: dict, sources: dict) -> str:
    by_id = {s["id"]: s for s in sources["sources"]}
    books = doc["books"]
    counts = {}
    for b in books:
        counts[b["status"]] = counts.get(b["status"], 0) + 1

    lines = [
        "# 57 本目标书 · 逐本映射表",
        "",
        f"> 由 `scripts/render_catalog.py` 生成于 {doc['generated_at']}，"
        "唯一事实来源是 [`books.json`](./books.json)，请勿直接编辑本文件。",
        "",
        "## 统计",
        "",
        "| 状态 | 数量 | 含义 |",
        "| --- | --- | --- |",
    ]
    legend = doc["legend"]
    for key in ("available", "related", "not_found"):
        lines.append(f"| {BOOK_STATUS[key]} | {counts.get(key, 0)} | {legend[key]} |")

    lines += [
        "",
        "> ⚠️ `related` 不等于就是那本书。喂 AI 时请在提示词里注明实际来源与版本，"
        "避免模型把不同版本混为一谈。",
        "",
        "## 逐本表",
        "",
        "| # | 书名 | 分类 | 状态 | 可用来源 | 说明 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for b in books:
        sid = b.get("source_id")
        if sid:
            src = by_id.get(sid, {})
            link = f"[{sid}]({src.get('url', '')})"
        else:
            link = "—"
        note = (b.get("note") or "").replace("|", "｜")
        lines.append(
            f"| {b['n']} | {b['title']} | {b['category']} | {BOOK_STATUS[b['status']]} | {link} | {note} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_gmzyjc(doc: dict) -> str:
    dirs = {d["code"]: d for d in doc["dirs"]}
    lines = [
        "# 光明教材（gmzyjc）课程代号映射表",
        "",
        f"> 由 `scripts/render_catalog.py` 生成于 {doc['generated_at']}，"
        "唯一事实来源是 [`gmzyjc-courses.json`](./gmzyjc-courses.json)，请勿直接编辑本文件。",
        "",
        f"- **数据源**：`{doc['source_dir']}`（46 个目录）",
        f"- **官方课程清单**：`{doc['readme']}`",
        "",
        "## 分组（Notebook 批次 B 文件 14-20）",
        "",
        "| 组 | 标题 | 目录 | 目录数 | 文件数 | 体积 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for g in doc["groups"]:
        members = [dirs[c] for c in g["dirs"]]
        files = sum(m["files"] for m in members)
        nbytes = sum(m["bytes"] for m in members)
        codes = " ".join(f"`{c}`" for c in g["dirs"])
        lines.append(
            f"| {g['no']} | {g['title']} | {codes} | {len(members)} | {files} | {nbytes / 1024 / 1024:.1f} MB |"
        )

    lines += [
        "",
        "## 目录明细",
        "",
        "| 代号 | 书名/课程 | 课号 | 官方 | 类型 | 组 | 置信 | 文件数 | 体积 | 证据 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for code in sorted(dirs):
        d = dirs[code]
        course = f"第{d['course_no']:02d}课" if d.get("course_no") else "—"
        official = "✅" if d.get("official") else ""
        group = str(d["group"]) if d.get("group") is not None else "不入批次"
        ev = d["evidence"].replace("|", "｜")
        lines.append(
            f"| `{code}` | {d['title']} | {course} | {official} | {d['kind']} | {group} "
            f"| {d['confidence']} | {d['files']} | {d['bytes'] / 1024 / 1024:.1f} MB | {ev} |"
        )

    lines += ["", "## 类型说明", ""]
    for key, val in doc["kinds"].items():
        lines.append(f"- `{key}`：{val}")
    lines += ["", "## 备注", ""]
    for note in doc.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def render_ancient(doc: dict) -> str:
    lines = [
        "# 701 本中医古籍 · 12 类归类表",
        "",
        f"> 由 `scripts/render_catalog.py` 生成于 {doc['generated_at']}，"
        "唯一事实来源是 [`ancient-categories.json`](./ancient-categories.json)，请勿直接编辑本文件。",
        "",
        f"- **分类体系**：{doc['taxonomy']}",
        f"- **归类方法**：{doc['method']}",
        f"- **总数**：{doc['total']} 本（编号 000-700，源文件见 `dataset/tcm/classics/tcm-ancient-books/`）",
        "",
        "## 分类统计",
        "",
        "| 《总目》分类号 | 分类 | id | 本数 |",
        "| --- | --- | --- | --- |",
    ]
    for c in doc["categories"]:
        lines.append(f"| {c['catelog_no']} | {c['name']} | `{c['id']}` | {c['count']} |")
    total = sum(c["count"] for c in doc["categories"])
    lines.append(f"| — | **合计** | — | **{total}** |")

    ovr = doc.get("overrides", {})
    cat_name = {c["id"]: c["name"] for c in doc["categories"]}
    lines += [
        "",
        f"## 人工校订（OVERRIDES，{len(ovr)} 条）",
        "",
        "书名无法由关键词规则判准、或位置与书名矛盾的少数书目，"
        "由 `scripts/classify_ancient.py` 中的 OVERRIDES 直接指定：",
        "",
        "| 编号 | 分类 | 理由 |",
        "| --- | --- | --- |",
    ]
    for oid in sorted(ovr):
        ov = ovr[oid]
        reason = ov["reason"].replace("|", "｜")
        lines.append(f"| {oid} | {cat_name.get(ov['cat'], ov['cat'])} | {reason} |")

    lines += ["", "## 备注", ""]
    for note in doc.get("notes", []):
        lines.append(f"- {note}")
    lines += ["", "> 重新归类：改 `scripts/classify_ancient.py` 后运行 `python3 scripts/classify_ancient.py`。", ""]
    return "\n".join(lines)


def main() -> None:
    sources = load("sources.json")
    books = load("books.json")
    gmzyjc = load("gmzyjc-courses.json")
    ancient = load("ancient-categories.json")
    write("sources.md", render_sources(sources))
    write("books.md", render_books(books, sources))
    write("gmzyjc-courses.md", render_gmzyjc(gmzyjc))
    write("ancient-categories.md", render_ancient(ancient))


if __name__ == "__main__":
    main()
