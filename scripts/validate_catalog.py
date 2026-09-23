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
ANCIENT = ROOT / "catalog" / "ancient-categories.json"
GMZYJC = ROOT / "catalog" / "gmzyjc-courses.json"

REQUIRED_SOURCE_FIELDS = {"id", "name", "category", "rating", "status", "url", "scope"}
REQUIRED_BOOK_FIELDS = {"n", "title", "category", "status", "source_id"}
VALID_STATUS = {"open", "restricted", "index-only", "reference", "local"}
VALID_BOOK_STATUS = {"available", "related", "not_found"}

# 《中国中医古籍总目》12 个一级分类（与 scripts/classify_ancient.py 保持一致）
VALID_ANCIENT_CATS = {
    "yijing", "jichu", "shanghan", "zhenfa", "zhenjiu", "bencao",
    "fangshu", "linzheng", "yangsheng", "yian", "yishi", "zonghe",
}
ANCIENT_TOTAL = 701
REQUIRED_GMZYJC_FIELDS = {"code", "title", "course_no", "official", "kind", "group", "confidence", "evidence", "files", "bytes"}
VALID_KINDS = {"course", "original", "variant", "auxiliary", "docx-only"}
VALID_CONFIDENCE = {"high", "medium", "low"}

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


def check_ancient(doc: dict) -> None:
    """校验 catalog/ancient-categories.json（701 本古籍 → 12 类归类）。"""
    if not doc:
        return
    cats = doc.get("categories", [])
    cat_ids = [c.get("id") for c in cats]
    if len(cats) != 12 or set(cat_ids) != VALID_ANCIENT_CATS:
        errors.append(f"ancient-categories: categories 应为 12 个 {sorted(VALID_ANCIENT_CATS)}，实际 {cat_ids}")
    nos = {c.get("catelog_no") for c in cats}
    if nos != {str(i) for i in range(1, 13)}:
        errors.append(f"ancient-categories: catelog_no 应为字符串 1-12，实际 {sorted(map(str, nos))}")

    assign = doc.get("assignments", {})
    if doc.get("total") != ANCIENT_TOTAL or len(assign) != ANCIENT_TOTAL:
        errors.append(f"ancient-categories: total={doc.get('total')}、assignments={len(assign)}，应为 {ANCIENT_TOTAL}")
    expected = {f"{i:03d}" for i in range(ANCIENT_TOTAL)}
    actual = set(assign)
    if actual != expected:
        errors.append(
            f"ancient-categories: assignments 编号不匹配，"
            f"缺 {sorted(expected - actual)[:5]}，多 {sorted(actual - expected)[:5]}"
        )
    bad_vals = {v for v in assign.values() if v not in VALID_ANCIENT_CATS}
    if bad_vals:
        errors.append(f"ancient-categories: assignments 含非法分类值 {sorted(bad_vals)}")

    tally: dict[str, int] = {}
    for v in assign.values():
        tally[v] = tally.get(v, 0) + 1
    for c in cats:
        if c.get("count") != tally.get(c.get("id"), 0):
            errors.append(
                f"ancient-categories: {c.get('id')} count={c.get('count')} "
                f"与 assignments 统计 {tally.get(c.get('id'), 0)} 不符"
            )

    for oid, ov in (doc.get("overrides") or {}).items():
        if oid not in assign:
            errors.append(f"ancient-categories: override {oid} 不在 assignments 中")
        elif ov.get("cat") != assign[oid]:
            errors.append(f"ancient-categories: override {oid} cat={ov.get('cat')} 与 assignments={assign[oid]} 不符")
        if not ov.get("reason"):
            errors.append(f"ancient-categories: override {oid} 缺少 reason")

    ds = ROOT / "dataset" / "tcm" / "classics" / "tcm-ancient-books"
    if ds.is_dir():
        disk_ids = {p.name[:3] for p in ds.glob("*.txt")}
        if not expected <= disk_ids:
            errors.append(f"ancient-categories: 数据目录缺编号 {sorted(expected - disk_ids)[:5]}")
    else:
        warnings.append("dataset/tcm/classics/tcm-ancient-books 不存在，跳过古籍文件核对")


def check_gmzyjc(doc: dict) -> None:
    """校验 catalog/gmzyjc-courses.json（46 目录 → 批次 B 组 14-20）。"""
    if not doc:
        return
    dirs = doc.get("dirs", [])
    groups = doc.get("groups", [])
    codes: dict[str, dict] = {}
    for d in dirs:
        code = d.get("code", "<无code>")
        missing = REQUIRED_GMZYJC_FIELDS - d.keys()
        if missing:
            errors.append(f"gmzyjc {code}: 缺少字段 {sorted(missing)}")
        if code in codes:
            errors.append(f"gmzyjc code 重复: {code}")
        codes[code] = d
        if d.get("kind") not in VALID_KINDS:
            errors.append(f"gmzyjc {code}: kind={d.get('kind')} 不合法，应为 {sorted(VALID_KINDS)}")
        if d.get("confidence") not in VALID_CONFIDENCE:
            errors.append(f"gmzyjc {code}: confidence={d.get('confidence')} 不合法")
        g = d.get("group")
        if g is not None and not (isinstance(g, int) and 14 <= g <= 20):
            errors.append(f"gmzyjc {code}: group={g} 应为 14-20 或 null")
        if not isinstance(d.get("files"), int) or d.get("files", -1) < 0:
            errors.append(f"gmzyjc {code}: files 应为非负整数")
        if not isinstance(d.get("bytes"), int) or d.get("bytes", -1) < 0:
            errors.append(f"gmzyjc {code}: bytes 应为非负整数")
        if d.get("group") is None and not d.get("evidence"):
            errors.append(f"gmzyjc {code}: 不入批次但缺少 evidence 说明")

    seen_in_groups: set[str] = set()
    for g in groups:
        no = g.get("no")
        if not isinstance(no, int) or no not in range(14, 21):
            errors.append(f"gmzyjc 组 {no}: 应为 14-20")
            continue
        for code in g.get("dirs", []):
            if code not in codes:
                errors.append(f"gmzyjc 组 {no}: 目录 {code} 不在 dirs 中")
                continue
            if codes[code].get("group") != no:
                errors.append(f"gmzyjc 组 {no} 含 {code}，但其 group={codes[code].get('group')}")
            if code in seen_in_groups:
                errors.append(f"gmzyjc: {code} 出现在多个组")
            seen_in_groups.add(code)
    field_grouped = {c for c, d in codes.items() if d.get("group") is not None}
    if field_grouped != seen_in_groups:
        errors.append(f"gmzyjc: group 字段与 groups 列表不一致（对称差 {sorted(field_grouped ^ seen_in_groups)}）")
    group_nos = {g.get("no") for g in groups}
    if group_nos != set(range(14, 21)):
        errors.append(f"gmzyjc: groups 应恰好覆盖 14-20，实际 {sorted(group_nos, key=str)}")

    st = doc.get("stats", {})
    expected_stats = {
        "dirs_total": len(dirs),
        "dirs_batched": len(field_grouped),
        "dirs_excluded": len(dirs) - len(field_grouped),
        "files_batched": sum(codes[c].get("files", 0) for c in field_grouped),
        "bytes_batched": sum(codes[c].get("bytes", 0) for c in field_grouped),
    }
    for key, val in expected_stats.items():
        if st.get(key) != val:
            errors.append(f"gmzyjc stats.{key}={st.get(key)}，按 dirs 推算应为 {val}")

    data = ROOT / "data" / "gmzyjc" / "ok"
    if data.is_dir():
        disk_dirs = {p.name for p in data.iterdir() if p.is_dir()}
        if disk_dirs != set(codes):
            errors.append(
                f"gmzyjc: data/gmzyjc/ok 与 JSON 目录不一致，"
                f"缺 {sorted(disk_dirs - set(codes))[:5]}，多 {sorted(set(codes) - disk_dirs)[:5]}"
            )
        for code, d in sorted(codes.items()):
            sub = data / code
            if not sub.is_dir():
                continue
            files = [p for p in sub.rglob("*") if p.is_file() and p.suffix in {".md", ".txt"}]
            nbytes = sum(p.stat().st_size for p in files)
            if len(files) != d.get("files") or nbytes != d.get("bytes"):
                errors.append(
                    f"gmzyjc {code}: files/bytes 与磁盘不符"
                    f"（JSON {d.get('files')}/{d.get('bytes')}，磁盘 {len(files)}/{nbytes}）"
                )
    else:
        warnings.append("data/gmzyjc/ok 不存在，跳过目录与体积核对")


def main() -> int:
    check_urls = "--check-urls" in sys.argv
    src_doc = load(SOURCES)
    book_doc = load(BOOKS)
    anc_doc = load(ANCIENT)
    gm_doc = load(GMZYJC)

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

    check_ancient(anc_doc)
    check_gmzyjc(gm_doc)

    print(
        f"sources: {len(sources)} 条，books: {len(books)} 条，"
        f"ancient: {anc_doc.get('total', 0)} 本，gmzyjc: {len(gm_doc.get('dirs', []))} 目录"
    )

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
