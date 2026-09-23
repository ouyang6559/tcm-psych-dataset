#!/usr/bin/env python3
"""校验 catalog/ 下的目录文件是否结构完整、交叉引用是否有效。

用法:
    python3 scripts/validate_catalog.py           # 只做结构校验
    python3 scripts/validate_catalog.py --check-urls   # 追加网络可达性检查（较慢）
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "catalog" / "sources.json"
BOOKS = ROOT / "catalog" / "books.json"

REQUIRED_SOURCE_FIELDS = {"id", "name", "category", "rating", "status", "url", "scope"}
REQUIRED_BOOK_FIELDS = {"n", "title", "category", "status", "source_id"}
VALID_STATUS = {"open", "restricted", "index-only", "reference", "local"}
VALID_BOOK_STATUS = {"available", "related", "not_found"}

errors: list[str] = []
warnings: list[str] = []


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"缺少文件: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"JSON 解析失败 {path.name}: {exc}")
    return {}


def main() -> int:
    check_urls = "--check-urls" in sys.argv
    src_doc = load(SOURCES)
    book_doc = load(BOOKS)

    sources = src_doc.get("sources", [])
    books = book_doc.get("books", [])

    ids: set[str] = set()
    for s in sources:
        sid = s.get("id", "<无id>")
        missing = REQUIRED_SOURCE_FIELDS - s.keys()
        if missing:
            errors.append(f"source {sid}: 缺少字段 {sorted(missing)}")
        if sid in ids:
            errors.append(f"source id 重复: {sid}")
        ids.add(sid)
        status = s.get("status")
        if status and status not in VALID_STATUS:
            errors.append(f"source {sid}: status={status} 不合法，应为 {sorted(VALID_STATUS)}")
        rating = s.get("rating")
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            errors.append(f"source {sid}: rating 应为 1-5 的整数")
        if status in {"open", "restricted", "local"} and not s.get("clone_url"):
            errors.append(f"source {sid}: status={status} 但缺少 clone_url")
        if not s.get("dataset_path") and status in {"open", "local"}:
            warnings.append(f"source {sid}: status={status} 但 dataset_path 为空，build_dataset 会跳过")
        if s.get("verified") is False:
            warnings.append(f"source {sid}: verified=false，地址未实际连通验证")

    seen_n: set[int] = set()
    for b in books:
        n = b.get("n")
        missing = REQUIRED_BOOK_FIELDS - b.keys()
        if missing:
            errors.append(f"book #{n}: 缺少字段 {sorted(missing)}")
        if n in seen_n:
            errors.append(f"book n 重复: {n}")
        seen_n.add(n)
        if b.get("status") not in VALID_BOOK_STATUS:
            errors.append(f"book #{n} {b.get('title')}: status={b.get('status')} 不合法")
        sid = b.get("source_id")
        if sid and sid not in ids:
            errors.append(f"book #{n} {b.get('title')}: source_id={sid} 在 sources 中不存在")
        if not sid and b.get("status") != "not_found":
            errors.append(f"book #{n} {b.get('title')}: 非 not_found 状态必须给出 source_id")

    print(f"sources: {len(sources)} 条，books: {len(books)} 条")

    if check_urls:
        for s in sources:
            url = s.get("url")
            if not url:
                continue
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "curl/8"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status >= 400:
                        warnings.append(f"url {s['id']}: HTTP {resp.status} ({url})")
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"url {s['id']}: 不可达 {exc} ({url})")
        for t in src_doc.get("tools", []):
            url = t.get("url")
            if not url:
                continue
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "curl/8"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status >= 400:
                        warnings.append(f"tool {t.get('name')}: HTTP {resp.status}")
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"tool {t.get('name')}: 不可达 {exc}")

    for w in warnings:
        print(f"[warn] {w}")
    for e in errors:
        print(f"[ERROR] {e}")

    if errors:
        print(f"\n校验失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"\n校验通过：0 个错误，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
