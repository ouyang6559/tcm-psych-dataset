#!/usr/bin/env bash
# 把 data/ 下已同步的源，按 catalog 中的 dataset_path 归置成统一数据集 dataset/
# 剥离上游 .git 目录，避免数据集目录变成嵌套仓库。
# 用法:
#   scripts/build_dataset.sh            # 生成 dataset/ + MANIFEST.md
#   scripts/build_dataset.sh --clean    # 先清空 dataset/ 再重建
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG="$ROOT/catalog/sources.json"
DATA="$ROOT/data"
DATASET="$ROOT/dataset"

[[ "${1:-}" == "--clean" ]] && rm -rf "$DATASET"
mkdir -p "$DATASET"

command -v python3 >/dev/null || { echo "需要 python3" >&2; exit 1; }

copied=0 missing=0 skipped=0

while IFS=$'\t' read -r id dataset_path status; do
  # 中间字段为空时 read 会错位，python 端用 "-" 占位
  [[ "$dataset_path" == "-" ]] && dataset_path=""
  [[ -n "$dataset_path" ]] || continue
  src="$DATA/$id"
  dest="$DATASET/$dataset_path"
  if [[ ! -d "$src" ]]; then
    # 只对可自动同步的源给出提示，restricted/index-only 不主动建议拉取
    case "$status" in
      open|local)
        echo "[缺失] ${id} （先跑 scripts/sync.sh --only ${id}）"
        missing=$((missing+1)) ;;
      *)
        echo "[未同步] ${id} （status=${status}，默认不同步）"
        skipped=$((skipped+1)) ;;
    esac
    continue
  fi
  mkdir -p "$dest"
  echo "[归置] $id → dataset/$dataset_path"
  # rsync 排除 .git / .DS_Store / README 说明文件保留
  if command -v rsync >/dev/null; then
    rsync -a --exclude='.git/' --exclude='.DS_Store' "$src/" "$dest/"
  else
    (cd "$src" && tar --exclude='.git' --exclude='.DS_Store' -cf - .) | (cd "$dest" && tar -xf -)
    rm -rf "$dest/.git"
  fi
  copied=$((copied+1))
done < <(python3 - "$CATALOG" <<'PY'
import json, sys
cat = json.load(open(sys.argv[1], encoding="utf-8"))
for s in cat["sources"]:
    print("%s\t%s\t%s" % (s["id"], s.get("dataset_path") or "-", s["status"]))
PY
)

# 生成清单
MANIFEST="$DATASET/MANIFEST.md"
{
  echo "# 数据集清单 (MANIFEST)"
  echo
  echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
  echo
  echo "| 目录 | 文件数 | 体积 |"
  echo "| --- | --- | --- |"
} > "$MANIFEST"

while IFS= read -r dir; do
  rel="${dir#"$DATASET"/}"
  count=$(find "$dir" -type f ! -name '.DS_Store' | wc -l | tr -d ' ')
  size=$(du -sh "$dir" 2>/dev/null | cut -f1)
  echo "| $rel | $count | $size |" >> "$MANIFEST"
done < <(find "$DATASET" -mindepth 1 -type d ! -path '*/.git*' | sort)

{
  echo
  echo "> 上表目录行的文件数与体积**包含其子目录**。"
  echo
  echo "## 按扩展名统计"
  echo
  echo "| 扩展名 | 数量 |"
  echo "| --- | --- |"
  find "$DATASET" -type f ! -path '*/.git/*' ! -name '.DS_Store' ! -name 'MANIFEST.md' \
    | sed 's/.*\.//' | tr '[:upper:]' '[:lower:]' \
    | grep -E '^[a-z0-9]{1,6}$' | sort | uniq -c | sort -rn \
    | awk '{printf "| .%s | %s |\n", $2, $1}'
  echo
  echo "总文件数: $(find "$DATASET" -type f ! -path '*/.git/*' ! -name '.DS_Store' ! -name 'MANIFEST.md' | wc -l | tr -d ' ')"
  echo "总体积: $(du -sh "$DATASET" | cut -f1)"
} >> "$MANIFEST"

echo
echo "完成：归置 ${copied} 个源，缺失 ${missing} 个，未同步 ${skipped} 个"
echo "数据集: $DATASET"
echo "清单:   $MANIFEST"
echo "接着看: docs/feeding-ai.md"
