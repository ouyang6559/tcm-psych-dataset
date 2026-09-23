#!/usr/bin/env python3
"""把 OpenStax osbooks-* 仓库的 CNXML 源文件转换成一份 Markdown。

用法:
    python3 scripts/cnxml2md.py dataset/psychology/openstax-psychology \
        -o dataset/_markdown/psychology-openstax.md

说明:
    - 章节顺序取自 collections/<slug>.collection.xml
    - 模块标题取自各 modules/<id>/index.cnxml 的 <title>
    - 只做结构与文本提取，不追求 100% 版式还原；图片以占位注释标注
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_of(el: ET.Element) -> str:
    """递归抽取纯文本，处理行内标记。"""
    out: list[str] = []
    if el.text:
        out.append(el.text)
    for child in el:
        name = local(child.tag)
        inner = text_of(child)
        if name == "emphasis":
            effect = child.get("effect", "")
            if effect in {"italics", "italic"}:
                out.append(f"*{inner}*")
            elif effect in {"bold"}:
                out.append(f"**{inner}**")
            else:
                out.append(inner)
        elif name in {"term", "cnx-term"}:
            out.append(f"**{inner}**")
        elif name in {"code", "monospace"}:
            out.append(f"`{inner}`")
        elif name == "link":
            href = child.get("href", "")
            out.append(f"[{inner}]({href})" if href else inner)
        elif name == "newline":
            out.append("\n\n")
        elif name in {"citenote", "xref"}:
            out.append(inner)
        else:
            out.append(inner)
        if child.tail:
            out.append(child.tail)
    return "".join(out)


def tidy(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" ?\n ?", "\n\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def rejoin_tables(text: str) -> str:
    """tidy() 会把单换行变双换行，导致表格行之间出现空行（非法 Markdown）。
    把夹在表格行之间的空行去掉，恢复成连续表格。"""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            j = i
            while j < len(lines):
                if lines[j].lstrip().startswith("|"):
                    out.append(lines[j])
                    j += 1
                elif j + 1 < len(lines) and lines[j + 1].lstrip().startswith("|"):
                    j += 1  # 丢弃表格行之间的单个空行
                else:
                    break
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def render_table(el: ET.Element) -> str:
    """CNXML 用 <tgroup><thead>/<tbody><row><entry>，HTML 用 <tr>/<td>/<th>，两者都认。"""
    rows: list[list[str]] = []
    for tr in el.iter():
        if local(tr.tag) not in {"tr", "row"}:
            continue
        cells = [tidy(text_of(td)).replace("\n", " ").replace("|", "｜")
                 for td in tr if local(td.tag) in {"td", "th", "entry"}]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def walk(el: ET.Element, level: int, out: list[str]) -> None:
    """把 content 树渲染成 Markdown。level 是当前标题层级（章=1, 节=2 起）。"""
    for child in el:
        name = local(child.tag)
        if name == "section":
            title_el = next((c for c in child if local(c.tag) == "title"), None)
            if title_el is not None:
                title = tidy(text_of(title_el)).replace("\n", " ")
                out.append("")
                out.append(f"{'#' * min(level, 6)} {title}")
                out.append("")
                for c in child:
                    if local(c.tag) != "title":
                        walk_section_body(c, level + 1, out)
            else:
                walk(child, level + 1, out)
        elif name == "para":
            body = tidy(text_of(child))
            if body:
                out.extend(["", body])
        elif name == "list":
            out.append("")
            for item in child:
                if local(item.tag) == "item":
                    out.append(f"- {tidy(text_of(item)).replace(chr(10), ' ')}")
            out.append("")
        elif name == "table":
            rendered = render_table(child)
            if rendered:
                out.extend(["", rendered, ""])
        elif name in {"figure", "image"}:
            # CNXML 的表格通常包在 <figure class="table"> 里，先取表格
            for sub in child:
                if local(sub.tag) == "table":
                    rendered = render_table(sub)
                    if rendered:
                        out.extend(["", rendered, ""])
            caption = next((c for c in child.iter() if local(c.tag) == "caption"), None)
            cap = tidy(text_of(caption)) if caption is not None else ""
            src = next((c for c in child.iter() if local(c.tag) in {"image", "img"}), None)
            href = (src.get("src") or src.get("xlink:href", "")) if src is not None else ""
            if cap or href:
                desc = cap or "figure"
                out.extend(["", f"*[Figure: {desc}{' — ' + href if href else ''}]*", ""])
        elif name in {"title", "metadata", "media", "newline"}:
            continue
        elif name in {"note", "example", "statement", "problem", "solution"}:
            walk(child, level, out)
        else:
            body = tidy(text_of(child))
            if body:
                out.extend(["", body])


def walk_section_body(el: ET.Element, level: int, out: list[str]) -> None:
    if local(el.tag) == "section":
        walk(el, level, out)
    else:
        walk(_wrapper(el), level, out)


class _wrapper:  # noqa: N801 - 让 walk() 能渲染单个节点
    def __init__(self, node: ET.Element):
        self._node = node

    def __iter__(self):
        return iter([self._node])


def parse_collection(path: Path) -> tuple[str, list[tuple[str, list[str]]]]:
    """返回 (书名, [(章节标题, [module id...]), ...])，顶层散落模块归入 Front Matter。"""
    root = ET.parse(path).getroot()
    title = ""
    for md in root.iter():
        if local(md.tag) == "title" and md.text:
            title = md.text.strip()
            break

    def content_blocks(parent: ET.Element):
        """parent 是 collection 根或 subcollection 根时，取其 <content> 的子节点。"""
        for c in parent:
            if local(c.tag) == "content":
                yield from c
            elif local(c.tag) == "module" or local(c.tag) == "subcollection":
                # 传进来的已经是 <content> 本身
                yield c

    top = next((c for c in root if local(c.tag) == "content"), None)
    chapters: list[tuple[str, list[str]]] = []
    unlisted: list[str] = []
    if top is None:
        return title, chapters

    for node in content_blocks(top):
        name = local(node.tag)
        if name == "module":
            unlisted.append(node.get("document", ""))
        elif name == "subcollection":
            ctitle = ""
            mods: list[str] = []
            for sub in node:
                if local(sub.tag) == "title" and sub.text:
                    ctitle = sub.text.strip()
                elif local(sub.tag) == "content":
                    for m in sub:
                        if local(m.tag) == "module":
                            mods.append(m.get("document", ""))
            chapters.append((ctitle or "Untitled", mods))

    if unlisted:
        chapters.insert(0, ("Front Matter", unlisted))
    return title, chapters


def module_title_and_body(path: Path) -> tuple[str, str]:
    root = ET.parse(path).getroot()
    title_el = next((c for c in root if local(c.tag) == "title"), None)
    title = tidy(text_of(title_el)).replace("\n", " ") if title_el is not None else path.parent.name
    content = next((c for c in root if local(c.tag) == "content"), None)
    out: list[str] = []
    if content is not None:
        walk(content, 3, out)  # 章 #, 节 ##, 模块内 section 从 ### 开始
    return title, rejoin_tables(tidy("\n".join(out)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", type=Path, help="osbooks-* 仓库根目录")
    ap.add_argument("-o", "--output", type=Path, required=True, help="输出 Markdown 路径")
    args = ap.parse_args()

    repo: Path = args.repo
    modules_dir = repo / "modules"
    if not modules_dir.is_dir():
        print(f"找不到 {modules_dir}", file=sys.stderr)
        return 1

    collections = sorted((repo / "collections").glob("*.collection.xml"))
    if not collections:
        print("找不到 collections/*.collection.xml", file=sys.stderr)
        return 1

    book_title, chapters = parse_collection(collections[0])
    available = {p.parent.name for p in modules_dir.glob("*/index.cnxml")}
    seen: set[str] = set()
    lines = [f"# {book_title}", "", f"> 由 scripts/cnxml2md.py 从 {repo.name} 转换生成", ""]

    ch_no = 0
    for ch_title, mods in chapters:
        mods = [m for m in mods if m in available]
        if not mods:
            continue
        if ch_title == "Front Matter":
            label = "Front Matter"          # 前言不参与正文编号
        else:
            ch_no += 1
            label = f"{ch_no}. {ch_title}"
        lines += [f"{'#' * 1} {label}", ""]
        for mid in mods:
            seen.add(mid)
            f = modules_dir / mid / "index.cnxml"
            try:
                m_title, body = module_title_and_body(f)
            except ET.ParseError as exc:
                lines += [f"## {mid}（解析失败: {exc}）", ""]
                continue
            lines += [f"## {m_title}", ""]
            if body:
                lines.append(body)
            lines.append("")

    orphans = sorted(available - seen)
    if orphans:
        lines += ["# 未在合集中的模块", ""]
        for mid in orphans:
            m_title, body = module_title_and_body(modules_dir / mid / "index.cnxml")
            lines += [f"## {m_title}", "", body, ""]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    args.output.write_text(text, encoding="utf-8")
    print(f"生成 {args.output}：{ch_no} 章 + 前言，{len(seen) + len(orphans)} 个模块，"
          f"{len(text):,} 字符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
