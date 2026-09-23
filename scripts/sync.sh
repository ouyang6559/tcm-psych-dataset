#!/usr/bin/env bash
# 一键同步开放资料源到本地 data/ 目录
# 用法:
#   scripts/sync.sh                 # 同步所有 status=open 的源（推荐）
#   scripts/sync.sh --list          # 只列出源，不下载
#   scripts/sync.sh --only tcm-skill,tcmoc
#   scripts/sync.sh --with-restricted          # 追加同步版权存疑的源（需自行确认版权）
#   scripts/sync.sh --only ai-books --no-lfs   # 跳过 LFS 大文件下载
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG="$ROOT/catalog/sources.json"
DATA="$ROOT/data"

ONLY=""
WITH_RESTRICTED=0
DO_LIST=0
FORCE=0
SKIP_LFS=0
DEPTH=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --only) ONLY="${2:?--only 需要 id}"; shift 2 ;;
    --with-restricted) WITH_RESTRICTED=1; shift ;;
    --list) DO_LIST=1; shift ;;
    --force) FORCE=1; shift ;;
    --no-lfs) SKIP_LFS=1; shift ;;
    --depth) DEPTH="${2:?--depth 需要数字}"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知参数: $1 （用 --help 查看用法）" >&2; exit 1 ;;
  esac
done

[[ -f "$CATALOG" ]] || { echo "找不到目录文件: $CATALOG" >&2; exit 1; }
command -v python3 >/dev/null || { echo "需要 python3" >&2; exit 1; }
command -v git >/dev/null || { echo "需要 git" >&2; exit 1; }

HAVE_LFS=0
if command -v git-lfs >/dev/null 2>&1 || git lfs version >/dev/null 2>&1; then
  HAVE_LFS=1
fi

mkdir -p "$DATA"

# 从 catalog 读出待处理源，输出: id<TAB>clone_url<TAB>branch<TAB>status<TAB>lfs<TAB>size_mb<TAB>skip_default
read_sources() {
  python3 - "$CATALOG" <<'PY'
import json, sys
cat = json.load(open(sys.argv[1], encoding="utf-8"))
for s in cat["sources"]:
    if not s.get("clone_url"):
        continue
    print("\t".join([
        s["id"],
        s["clone_url"],
        s.get("branch") or "-",   # 空字段会让 read 错位，用占位符
        s["status"],
        "1" if s.get("lfs") else "0",
        str(s.get("size_mb") or "?"),
        "1" if s.get("skip_default") else "0",
    ]))
PY
}

if [[ "$DO_LIST" == "1" ]]; then
  printf "%-24s %-14s %-10s %s\n" "ID" "STATUS" "SIZE(MB)" "URL"
  printf "%-24s %-14s %-10s %s\n" "------------------------" "--------------" "----------" "----"
  while IFS=$'\t' read -r id url branch status lfs size skip_default; do
    printf "%-24s %-14s %-10s %s\n" "$id" "$status" "$size" "$url"
  done < <(read_sources)
  exit 0
fi

SYNCED=0 SKIPPED=0 FAILED=0

while IFS=$'\t' read -r id url branch status lfs size skip_default; do
  [[ "$branch" == "-" ]] && branch=""

  # 版权状态门限（优先于 --only，避免显式点名绕过 restricted/index-only）
  case "$status" in
    open|local) ;;
    restricted)
      [[ "$WITH_RESTRICTED" == "1" ]] || { echo "[跳过] ${id} （restricted：版权存疑，加 --with-restricted 才同步）"; SKIPPED=$((SKIPPED+1)); continue; } ;;
    *)
      echo "[跳过] ${id} （status=${status}，仅索引，不同步文件）"; SKIPPED=$((SKIPPED+1)); continue ;;
  esac

  # --only 过滤
  if [[ -n "$ONLY" ]]; then
    [[ ",$ONLY," == *",$id,"* ]] || { SKIPPED=$((SKIPPED+1)); continue; }
  elif [[ "$skip_default" == "1" ]]; then
    echo "[跳过] ${id} （skip_default：与其他源重复，指定 --only ${id} 才同步）"
    SKIPPED=$((SKIPPED+1))
    continue
  fi

  dest="$DATA/$id"
  if [[ -d "$dest/.git" && "$FORCE" != "1" ]]; then
    echo "[已存在] $id → $dest （加 --force 重新克隆）"
    SYNCED=$((SYNCED+1))
    continue
  fi

  # LFS 处理
  clone_env=()
  if [[ "$lfs" == "1" ]]; then
    if [[ "$HAVE_LFS" == "1" && "$SKIP_LFS" != "1" ]]; then
      echo "[LFS] $id 含 Git LFS 对象，将一并下载（$size MB）"
    else
      echo "[LFS] $id 含 LFS 对象，但未启用下载 → 只取指针文件（安装 git-lfs 并去掉 --no-lfs 可取实体）"
      clone_env=(env GIT_LFS_SKIP_SMUDGE=1)
    fi
  fi

  echo "[同步] $id ← $url  (branch=${branch:-默认}, ~${size}MB)"
  rm -rf "$dest"
  # ${arr[@]+...} 兼容 bash 3.2（macOS 默认）在 set -u 下的空数组展开
  if ${clone_env[@]+"${clone_env[@]}"} git clone --depth "$DEPTH" ${branch:+--branch "$branch"} "$url" "$dest" 2>&1 | sed 's/^/    /'; then
    SYNCED=$((SYNCED+1))
  else
    echo "[失败] $id" >&2
    FAILED=$((FAILED+1))
    rm -rf "$dest"
  fi
done < <(read_sources)

echo
# 变量必须用 ${} 包裹：bash 3.2 会把紧跟的中文字节并入变量名
echo "完成：同步 ${SYNCED}，跳过 ${SKIPPED}，失败 ${FAILED}"
echo "下一步：scripts/build_dataset.sh 生成统一数据集"
