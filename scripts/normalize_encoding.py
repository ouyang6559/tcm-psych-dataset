#!/usr/bin/env python3
"""把数据集里的文本文件统一转成 UTF-8（含换行符归一化）。

背景: xiaopangxia/TCM-Ancient-Books 全部 701 个 txt 是 GB18030 编码，
光明中医教材里也混有 GB18030 文件，直接喂给大模型全是乱码。

用法:
    python3 scripts/normalize_encoding.py dataset/                 # 原地转换
    python3 scripts/normalize_encoding.py dataset/ --check         # 只检查不改文件
    python3 scripts/normalize_encoding.py dataset/ --report r.json # 输出详细报告

规则:
    1. 已是合法 UTF-8（含带 BOM）→ 仅去 BOM、换行归一化
    2. 非 UTF-8 → 依次尝试 gb18030 / big5 / utf-16 / shift_jis，用中文占比 + 
       替换字符数选最优解
    3. 含 NUL 字节或解码结果中文占比过低 → 判为二进制，跳过并记录
    4. 只处理文本扩展名，图片/音视频/压缩包一律跳过
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

TEXT_EXT = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".xml",
    ".cnxml", ".html", ".htm", ".yml", ".yaml", ".ini", ".cfg",
    ".srt", ".log", ".py", ".sh", ".bat",
}
BINARY_EXT = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico",
    ".pdf", ".mp4", ".mp3", ".wav", ".zip", ".gz", ".tar", ".7z",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".epub",
    ".ttf", ".otf", ".woff", ".woff2", ".exe", ".dll", ".so", ".dylib",
    ".bin", ".db", ".sqlite",
}
CANDIDATES = ["gb18030", "big5", "utf-16", "utf-16-le", "shift_jis", "euc-kr"]
MIN_CJK = 0.05  # 判定「确实是中文文本」的最低中文字符占比


def cjk_ratio(text: str) -> float:
    if not text:
        return 0.0
    cn = sum(1 for c in text if "一" <= c <= "鿿" or "㐀" <= c <= "䶿")
    return cn / len(text)


def score(text: str) -> tuple[float, int]:
    """越小越好：先看替换符与控制符，再看中文占比。"""
    bad = text.count("\ufffd")
    ctrl = sum(1 for c in text if c < " " and c not in "\r\n\t")
    return (bad * 10 + ctrl, -cjk_ratio(text))


def decode(data: bytes) -> tuple[str, str] | tuple[None, str]:
    if b"\x00" in data:
        return None, "含 NUL 字节，判为二进制"

    # 去 BOM 的 UTF-8 / UTF-16
    for bom, enc in ((b"\xef\xbb\xbf", "utf-8-sig"), (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16")):
        if data.startswith(bom):
            try:
                return data.decode(enc), enc
            except UnicodeDecodeError:
                break

    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    best: tuple | None = None
    best_enc = ""
    for enc in CANDIDATES:
        try:
            text = data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
        s = score(text)
        if best is None or s < best:
            best, best_enc = s, enc
        if s[0] == 0 and cjk_ratio(text) >= MIN_CJK:
            return text, enc  # 干净且是中文，直接采纳

    if best is not None and best[0] < len(data) * 0.05:
        return data.decode(best_enc, errors="replace"), best_enc

    # 宽松模式: 语料里偶见个别坏字节（如错位的半个双字节），若损坏比例极低则放行
    for enc in [e for e in [best_enc] + CANDIDATES if e]:
        try:
            text = data.decode(enc, errors="replace")
        except (UnicodeDecodeError, UnicodeError):
            continue
        reps = text.count("\ufffd")
        if reps and reps / max(len(text), 1) < 0.005 and cjk_ratio(text) >= MIN_CJK:
            return text, f"{enc}+replace({reps})"
    return None, f"无法可靠解码（最佳尝试 {best_enc or '无'}）"


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path, help="要处理的目录（如 dataset/）")
    ap.add_argument("--check", action="store_true", help="只检查，不写文件")
    ap.add_argument("--report", type=Path, help="输出 JSON 报告")
    args = ap.parse_args()

    if not args.root.is_dir():
        print(f"目录不存在: {args.root}", file=sys.stderr)
        return 1

    stats: Counter = Counter()
    encodings: Counter = Counter()
    failures: list[dict] = []
    touched: list[dict] = []

    for path in sorted(args.root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        ext = path.suffix.lower()
        if ext in BINARY_EXT:
            stats["binary_ext_skipped"] += 1
            continue
        if ext and ext not in TEXT_EXT:
            stats["unknown_ext_skipped"] += 1
            continue
        unnamed = not ext  # 无扩展名文件解不出文本就当二进制，不计为失败

        raw = path.read_bytes()
        text, enc = decode(raw)
        if text is None:
            if unnamed or b"\x00" in raw:
                stats["binary_sniffed_skipped"] += 1
                continue
            stats["failed"] += 1
            failures.append({"file": str(path), "reason": enc, "size": len(raw)})
            continue

        encodings[enc] += 1
        if enc == "utf-8" and "\r" not in text:
            stats["already_utf8"] += 1
            continue

        new = normalize_newlines(text).encode("utf-8")
        changed = new != raw
        stats["converted"] += 1
        if changed:
            touched.append({"file": str(path), "from": enc, "bytes": len(raw),
                            "utf8_bytes": len(new)})
        if not args.check and changed:
            path.write_bytes(new)

    result = {
        "root": str(args.root),
        "check_only": args.check,
        "stats": dict(stats),
        "source_encodings": dict(encodings.most_common()),
        "converted_files": touched,
        "failures": failures,
    }
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                               encoding="utf-8")

    print(f"扫描 {args.root}")
    print(f"  源编码分布 : {dict(encodings.most_common())}")
    print(f"  已是 UTF-8 : {stats['already_utf8']}")
    print(f"  需转换     : {stats['converted']}"
          f"{'（--check 未写入）' if args.check else ''}")
    print(f"  跳过(二进制): {stats['binary_ext_skipped'] + stats['unknown_ext_skipped'] + stats['binary_sniffed_skipped']}")
    print(f"  解码失败   : {stats['failed']}")
    for f in failures[:10]:
        print(f"    - {f['file']}: {f['reason']}")
    if len(failures) > 10:
        print(f"    ... 共 {len(failures)} 个，详见 --report")
    if stats["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
