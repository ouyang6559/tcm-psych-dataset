#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 tcm-ancient-books 的 701 本古籍按《中国中医古籍总目》12 个一级分类归类。

分类依据: data/tcmoc/Catelog.md（《中国中医古籍总目》分类表，12 个一级类）
方法:
    1) 有序关键词规则 RULES —— 先特异后宽泛，首个命中生效；
    2) OVERRIDES 人工校订 —— 书名判不准、或位置与书名矛盾的少数几本（编号 → 分类 + 理由）；
    3) 规则全不命中的书用邻域平滑兜底 —— 上游编号基本按类排序，
       取前后 ±6 本已归类邻居的多数票（平票取离得最近的邻居所属类），仍无票 → 综合性著作。

用法:
    python3 scripts/classify_ancient.py           # 生成 catalog/ancient-categories.json + 打印复核报告
    python3 scripts/classify_ancient.py --check   # 只打印报告，不写文件

复核报告两节:
    [A] 规则未命中（靠邻域平滑兜底）—— 逐本列出，人工过目
    [B] 与邻域多数不一致 —— 多为类别交界处的例外，逐本人工确认后写进 OVERRIDES 或接受
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 《中国中医古籍总目》12 个一级分类（顺序即分类表顺序）
CATS = [
    ("yijing", "医经类", "1"),
    ("jichu", "基础理论", "2"),
    ("shanghan", "伤寒金匮", "3"),
    ("zhenfa", "诊法类", "4"),
    ("zhenjiu", "针灸推拿", "5"),
    ("bencao", "本草", "6"),
    ("fangshu", "方书", "7"),
    ("linzheng", "临证各科", "8"),
    ("yangsheng", "养生", "9"),
    ("yian", "医案医话医论", "10"),
    ("yishi", "医史", "11"),
    ("zonghe", "综合性著作", "12"),
]
CAT_IDS = [c[0] for c in CATS]

# 有序规则：首个命中生效。顺序原则：
#   针灸/伤寒/医经/医案 等特异词最先 → 临证专科词（妇儿内外伤眼喉）先于泛诊法词（脉/诊/舌）
#   → 诊法 → 基础理论 → 本草 → 温病 → 养生 → 方书 → 医史 → 综合兜底。
RULES: list[tuple[re.Pattern, str]] = [
    # 1 针灸推拿（含《总目》5.5 推拿按摩、5.6 外治法）。注意：炙 只认『炙膏肓』，
    # 否则 雷公炮炙论/炮炙大法 会被误抓进来；针 认裸字以覆盖『金针秘传』。
    (re.compile(r"针|灸|炙膏肓|明堂|腧|穴|经络|经穴|子午流注|铜人|推拿|按摩|奇经八脉|刺血|十四经|十二经脉|外治"), "zhenjiu"),
    # 2 伤寒金匮
    (re.compile(r"伤寒|金匮|仲景"), "shanghan"),
    # 3 医经类（素问/灵枢/内经/难经/医经/外经/灵素；医经 排除『中医经验集』类误抓）
    (re.compile(r"素问|灵枢|内经|难经|医经(?!验)|外经|灵素"), "yijing"),
    # 4 医案医话医论
    (re.compile(r"医案|医话|医论|医门|医说|诊余|随笔|类案|验案|治验|寓意草|遗稿|垂教|经验集|卮言|刍言|方案"), "yian"),
    # 5 临证各科·专科（妇儿内外伤眼喉口齿 + 杂病）——先于诊法泛词，
    # 否则『喉舌备要秘旨』被『舌』抓走、『金疮跌打接骨药性秘书』被『药性』抓走
    (re.compile(
        r"内科|外科|妇科|女科|妇人|幼|儿科|小儿|婴|胎产|产科|产宝|产鉴|产后|广嗣|毓麟|达生|济阴|颅囟"
        r"|痘|疹|麻科|疡|疮|疽|发背|背疽|跌打|跌损|伤科|理伤|救伤|损伤|接骨|正骨|正体|金疮"
        r"|眼科|目科|银海|瑶函|目经|明目|喉|口齿|白喉|血证|脚气|杂病|虚劳|虚损|理虚|中风"
        r"|疳|痔|疯|疠|痰",
    ), "linzheng"),
    # 6 临证各科·温病（《总目》8.2：四时温病/瘟疫/疟疾/痧胀霍乱）
    (re.compile(r"温病|温疫|瘟疫|疫|温热|湿热|暑|伏暑|痧|霍乱|瘴|疟|痢|热病|六因"), "linzheng"),
    # 7 诊法类
    (re.compile(r"脉|诊|望|舌|察"), "zhenfa"),
    # 8 基础理论（病源 已移除：335 宣导法属养生，571 诸病源候论走 OVERRIDES）
    (re.compile(r"阴阳|五行|运气|五运|六气|藏象|病机|病理|脾胃|生理|格致余论"), "jichu"),
    # 9 本草（含《总目》6.4 食疗本草 → 食疗/食治/饮食 归本草）
    (re.compile(r"本草|本经|药性|药征|药鉴|炮炙|炮制|药症|药歌|要药|食疗|食治|饮食|饮馔"), "bencao"),
    # 10 养生（《总目》9：养生通论/导引气功/炼丹）
    (re.compile(r"养生|导引|宣导|摄生|性命|易筋|洗髓|养老|女丹|仙经|寿世|延寿|修昆仑|炼丹|胎息"), "yangsheng"),
    # 11 方书
    (re.compile(r"方|歌括|歌诀|汤头|局方|验方|成方|丸散"), "fangshu"),
    # 12 医史（传记/史料/书目）
    (re.compile(r"医史|医学史|医籍考|名老中医|传略|洗冤|医家"), "yishi"),
    # 13 综合性著作（兜底关键词；回春 已移除：382 回春录属医案段）
    (re.compile(r"医学|医宗|医统|大全|全书|入门|汇编|集成|类编|宝鉴|纲目|指掌|汇粹|正宗|玉案|医通"), "zonghe"),
]

# 人工校订：编号 → (分类, 理由)。规则判错、书名与内容不符、或书名信息不足时使用。
OVERRIDES: dict[str, tuple[str, str]] = {
    "048": ("zonghe", "《思考中医》（刘力红，2003）为现代著作，混在古籍库中"),
    "050": ("bencao", "《名医别录》为本草著作，书名无本草字样"),
    "073": ("fangshu", "《增广和剂局方药性总论》主体为和剂局方"),
    "079": ("zonghe", "《仁术便览》为综合性医书"),
    "080": ("zonghe", "《中医之钥》书名无分类特征"),
    "081": ("fangshu", "《祖剂》为古方类方书"),
    "116": ("fangshu", "《回生集》为验方集"),
    "200": ("linzheng", "《邯郸遗稿》为妇产科著作（邻域 199/201 均为妇儿）；勿被『遗稿』误判入医案"),
    "221": ("linzheng", "文件名『余无言』疑为医家人名/其著作，位于外科伤科段，按邻域归临证各科（存疑）"),
    "257": ("linzheng", "《症因脉治》为内科杂病广论（秦昌遇），非脉学书"),
    "270": ("linzheng", "《慎柔五书》为内科虚损类"),
    "275": ("linzheng", "《刘涓子鬼遗方》为外科痈疽方书，位于外科段"),
    "280": ("linzheng", "《医学从众录》以杂病证治各论为主（陈修园）"),
    "303": ("yishi", "《李翰卿》为医家小传，虽位于针灸段仍归医史"),
    "325": ("linzheng", "《原机启微》为眼科奠基书（银海系统）"),
    "337": ("zhenjiu", "《理瀹骈文》为外治法专著，按《总目》5.6 归针灸推拿"),
    "355": ("zhenjiu", "《灵枢经脉翼》为经脉图（夏英绘），按《总目》5.2 经络孔穴归针灸推拿"),
    "379": ("yian", "《市隐庐医学杂着》为医话杂著，位于医话段"),
    "390": ("linzheng", "《辨证汇编》按《总目》8.1 临证综合"),
    "413": ("yian", "《医学课儿策》为医论（医案医话医论段）"),
    "414": ("yian", "《医学读书记》为读书随笔医话"),
    "418": ("yian", "《医学源流论》为徐灵胎医论集"),
    "456": ("linzheng", "《万氏秘传片玉心书》为儿科著作，夹在医经/伤寒段之间"),
    "534": ("zonghe", "《心医集》书名信息不足，暂归综合性"),
    "535": ("zonghe", "《西池集》书名信息不足，暂归综合性"),
    "540": ("linzheng", "《宁坤秘笈》为妇科方书"),
    "542": ("zonghe", "《寿世保元》为综合性医书（勿被『寿世』误判入养生）"),
    "557": ("yijing", "《华氏中藏经》论脉候脏腑，按医经类收"),
    "564": ("zonghe", "《金匮钩玄》为丹溪派杂病书，非金匮注释（位于综合段）"),
    "567": ("linzheng", "《脉因证治》为丹溪派内科杂病书（朱门弟子编），非脉学书"),
    "571": ("jichu", "《诸病源候论》为病源病机之祖，按基础理论"),
    "576": ("zonghe", "《医经国小》疑即《医经小学》（刘纯），为入门歌括教材，按《总目》12.5 教材"),
    "585": ("linzheng", "《卫济宝书》为外科著作"),
    "586": ("linzheng", "《三消论》论消渴，归内科"),
    "620": ("yian", "《推求师意》为丹溪派医论"),
    "621": ("yian", "《褚氏遗书》为医论"),
    "623": ("yian", "《医旨绪余》为孙一奎医论"),
    "628": ("yian", "《医医小草》为医话小品"),
    "631": ("zonghe", "《医法圆通》（郑钦安）为综合性医书"),
    "640": ("linzheng", "《宜麟策》为求嗣（广嗣）类，按《总目》8.4.3 归女科"),
    "641": ("jichu", "《医理真传》（郑钦安）论阴阳病理"),
    "647": ("zonghe", "《万病回春》为综合性医书"),
    "648": ("yian", "《医津一筏》为医论小品"),
    "651": ("bencao", "《十二經補瀉溫涼引經藥歌》为繁体书名，规则无法命中；性质为药性歌括"),
    "653": ("fangshu", "《辅行诀脏腑用药法要》为经方源头方书（陶弘景），书名无方字"),
    "652": ("linzheng", "《三时伏气外感篇》为叶天士温病著作"),
    "655": ("yian", "《评琴书屋医略》为医话医论"),
    "661": ("linzheng", "《七十二症辨治方法》为杂病证治"),
    "672": ("yian", "《经方实验录》为曹颖甫经方医案集，勿被『经方』误判入方书"),
    "686": ("yian", "《中医临证经验与方法》为临证医著/医话"),
    "692": ("yian", "《鲙残篇》位于医话群（693-697）之间，按邻域归医话"),
}

WINDOW = 6  # 邻域平滑窗口 ±WINDOW 本

NOTES = [
    "048-思考中医 为现代著作（刘力红 2003），上游混入古籍库，暂归综合性著作并在此标注。",
    "221-余无言 文件名疑为医家人名（同 303-李翰卿 形式），内容与归类存疑，按邻域暂归临证各科。",
    "114-外治寿世方、337-理瀹骈文 按《总目》5.6 外治法归针灸推拿类（与所在编号段不同）。",
    "140-小儿推拿广意、160-幼科推拿秘书 按《总目》5.5 推拿按摩归针灸推拿类。",
    "523-千金食治、533-食疗方、555-饮食须知 按《总目》6.4 食疗本草归本草类。",
    "694/695/698 三本为合刊（文件名含两书名），700 使用点号分隔——编号解析均已兼容。",
]


def find_books() -> list[Path]:
    for cand in (
        ROOT / "dataset" / "tcm" / "classics" / "tcm-ancient-books",
        ROOT / "data" / "tcm-ancient-books",
    ):
        if cand.is_dir() and any(cand.glob("*.txt")):
            return sorted(cand.glob("*.txt"))
    sys.exit("找不到 tcm-ancient-books 目录（先运行 scripts/sync.sh 与 build_dataset.sh）")


def rule_label(title: str) -> tuple[str | None, str | None]:
    for pat, cat in RULES:
        if pat.search(title):
            return cat, pat.pattern
    return None, None


def neighbor_majority(labels: list[str | None], i: int) -> tuple[str | None, dict[str, int]]:
    votes: dict[str, int] = {}
    dist: dict[str, int] = {}
    lo, hi = max(0, i - WINDOW), min(len(labels), i + WINDOW + 1)
    for j in range(lo, hi):
        if j == i or not labels[j]:
            continue
        lab = labels[j]
        votes[lab] = votes.get(lab, 0) + 1
        d = abs(j - i)
        if lab not in dist or d < dist[lab]:
            dist[lab] = d
    if not votes:
        return None, votes
    top = max(votes.values())
    cands = [lab for lab, n in votes.items() if n == top]
    if len(cands) == 1:
        return cands[0], votes
    return min(cands, key=lambda lab: dist[lab]), votes  # 平票取最近邻居所属类


def main() -> None:
    check_only = "--check" in sys.argv
    books = find_books()

    ids: list[str] = []
    titles: list[str] = []
    for p in books:
        m = re.match(r"(\d{3})", p.stem)
        if not m:
            print(f"  !! 跳过无法解析编号的文件: {p.name}")
            continue
        ids.append(m.group(1))
        titles.append(p.stem[4:] if len(p.stem) > 4 and p.stem[3] in "-." else p.stem[3:])
    if len(set(ids)) != len(ids):
        sys.exit("存在重复编号，中止")

    # 第一轮：规则 + 校订
    labels: list[str | None] = []
    sources: list[str] = []  # override / rule / smooth
    reasons: list[str] = []
    for bid, title in zip(ids, titles):
        if bid in OVERRIDES:
            cat, why = OVERRIDES[bid]
            labels.append(cat)
            sources.append("override")
            reasons.append(why)
            continue
        cat, pat = rule_label(title)
        labels.append(cat)
        sources.append("rule" if cat else "")
        reasons.append(pat or "")

    # 第二轮：邻域平滑（只对未命中的书；对第一轮快照投票，避免遍历顺序影响结果）
    snapshot = list(labels)
    smoothed: list[tuple[str, str, dict[str, int]]] = []  # (id, title, votes)
    for i, lab in enumerate(snapshot):
        if lab is not None:
            continue
        maj, votes = neighbor_majority(snapshot, i)
        labels[i] = maj or "zonghe"
        sources[i] = "smooth"
        reasons[i] = "邻域多数" if maj else "无邻居票，兜底"
        smoothed.append((ids[i], titles[i], votes))

    # 复核报告
    counts = {cid: 0 for cid in CAT_IDS}
    for lab in labels:
        counts[lab] += 1
    print("=== 分类计数 ===")
    for cid, name, no in CATS:
        print(f"  {no:>2}. {name:<8} {counts[cid]:>4} 本")

    print(f"\n=== [A] 规则未命中、靠邻域平滑兜底（{len(smoothed)} 本）===")
    for bid, title, votes in smoothed:
        i = ids.index(bid)
        v = ",".join(f"{k}:{n}" for k, n in sorted(votes.items(), key=lambda x: -x[1])) or "无票"
        print(f"  {bid} {title[:28]:<30} → {labels[i]:<9} ({v})")

    # 与邻域多数不一致（第一轮已归类的书）
    conflicts: list[tuple[str, str, str, str, dict[str, int]]] = []
    base = list(labels)  # 全量标签（含平滑）作邻居
    for i in range(len(ids)):
        if sources[i] == "smooth":
            continue
        maj, votes = neighbor_majority([None if j == i else base[j] for j in range(len(base))], i)
        if maj and maj != labels[i]:
            conflicts.append((ids[i], titles[i], labels[i], maj, votes))
    print(f"\n=== [B] 与邻域多数不一致（{len(conflicts)} 本，人工确认后接受或写进 OVERRIDES）===")
    for bid, title, lab, maj, votes in conflicts:
        src = sources[ids.index(bid)]
        v = ",".join(f"{k}:{n}" for k, n in sorted(votes.items(), key=lambda x: -x[1]))
        print(f"  {bid} {title[:26]:<28} → {lab:<9} ({src}) ≠ 邻域 {maj:<9} ({v})")

    total = len(ids)
    if total != 701:
        print(f"\n!! 警告：只解析到 {total} 本书（预期 701）")

    if check_only:
        return

    out = {
        "generated_at": datetime.date.today().isoformat(),
        "taxonomy": "《中国中医古籍总目》12 个一级分类，见 data/tcmoc/Catelog.md",
        "method": "有序关键词规则 + 人工校订(OVERRIDES) + 邻域平滑兜底；生成脚本 scripts/classify_ancient.py",
        "total": total,
        "categories": [
            {"id": cid, "name": name, "catelog_no": no, "count": counts[cid]}
            for cid, name, no in CATS
        ],
        "assignments": dict(zip(ids, labels)),
        "overrides": {k: {"cat": v[0], "reason": v[1]} for k, v in sorted(OVERRIDES.items())},
        "notes": NOTES,
    }
    path = ROOT / "catalog" / "ancient-categories.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n生成 {path.relative_to(ROOT)}（{total} 本）")


if __name__ == "__main__":
    main()
