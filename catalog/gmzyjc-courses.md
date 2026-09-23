# 光明教材（gmzyjc）课程代号映射表

> 由 `scripts/render_catalog.py` 生成于 2026-09-24，唯一事实来源是 [`gmzyjc-courses.json`](./gmzyjc-courses.json)，请勿直接编辑本文件。

- **数据源**：`data/gmzyjc/ok`（46 个目录）
- **官方课程清单**：`data/gmzyjc/README.md（光明教材电子化公益项目官方 21 门课程清单）`

## 分组（Notebook 批次 B 文件 14-20）

| 组 | 标题 | 目录 | 目录数 | 文件数 | 体积 |
| --- | --- | --- | --- | --- | --- |
| 14 | 经典讲解 | `hdnjs` `shl` `jgyl` `wbtb` `bc` | 5 | 987 | 5.5 MB |
| 15 | 经典原文 | `hdnjsw` `hdnjls` `shltm` `gbshl` `nj` `mj` `pwl` `fxj` | 8 | 427 | 1.5 MB |
| 16 | 基础与方剂 | `gl` `fjx` `kj` `qs` `kjn` `kjs` `rm` | 7 | 400 | 2.2 MB |
| 17 | 临床各科 | `nk` `wk` `fk` `ek` `gk` `yk` `hk` | 7 | 804 | 5.3 MB |
| 18 | 针灸学 | `zjs` `zjx` `zjz` | 3 | 764 | 1.5 MB |
| 19 | 临证与医案 | `lzcx` `zhencha` `ya` `yjxj` `zxyjh` `bzszgy` `lk` | 7 | 958 | 2.4 MB |
| 20 | 校史与杂纂 | `gmjcintro` `gmrw` `gmzy` `xlcy` `kykt` `zywx` `zyzl` | 7 | 213 | 2.2 MB |

## 目录明细

| 代号 | 书名/课程 | 课号 | 官方 | 类型 | 组 | 置信 | 文件数 | 体积 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bc` | 本草备要讲解 | 第14课 | ✅ | course | 14 | high | 504 | 1.4 MB | README《14本草备要讲解》 |
| `bzszgy` | 辨证施治纲要 | — |  | auxiliary | 19 | medium | 1 | 0.0 MB | 仅 1 文件 3.md（以『毛主席语录』开篇的《辨证施治纲要》节录）；zhencha 前言引作《辩证施治纲要》，非 README 21 课 |
| `ek` | 中医儿科学 | 第20课 | ✅ | course | 17 | high | 131 | 0.9 MB | README《20中医儿科学》 |
| `fjx` | 方剂讲解 | — | ✅ | course | 16 | high | 141 | 0.4 MB | README 清单末列《方剂讲解》（无编号）；fjs*.bz 分章文件，曹希平主编 |
| `fk` | 中医妇科学 | 第19课 | ✅ | course | 17 | high | 103 | 0.8 MB | README《19中医妇科学》 |
| `fxj` | 辅行诀 | — |  | original | 15 | high | 16 | 0.1 MB | 《辅行诀脏腑用药法要》古籍原文 16 篇 |
| `gbshl` | 桂林古本伤寒杂病论 | — |  | original | 15 | high | 34 | 0.3 MB | 《伤寒杂病论》桂林古本 |
| `gdhy` | 古代汉语 | — |  | docx-only | 不入批次 | medium | 0 | 0.0 MB | 仅 2 个 docx、无 md/txt → 不入批次 |
| `gk` | 中医骨伤科学 | 第17课 | ✅ | course | 17 | high | 146 | 0.5 MB | README《17中医骨伤科学》 |
| `gl` | 中医药学概论 | 第06课 | ✅ | course | 16 | high | 171 | 0.6 MB | README《06中医药学概论》；编者的话明示 |
| `gmjcintro` | 教材使用指南与答疑 | — |  | auxiliary | 20 | medium | 14 | 0.0 MB | dayi.md H1『如何解决学习中的疑问』等；daoyan/dzb 为各课共用样板，非身份依据 |
| `gmrw` | 顾问传略与学员名单 | — |  | auxiliary | 20 | medium | 87 | 0.5 MB | gmrw-85-*.md H1『85级毕业生名单』+ 顾问传略 |
| `gmzy` | 函大校史文献 | — |  | auxiliary | 20 | medium | 16 | 0.1 MB | gmzy001 H1『光明中医函授大学在京隆重开学』等校史报道 |
| `hdnjls` | 灵枢原文 | — |  | original | 15 | high | 84 | 0.3 MB | 《灵枢》原文（与 hdnjsw《素问》对称命名） |
| `hdnjs` | 黄帝内经讲解 | 第10课 | ✅ | course | 14 | high | 309 | 1.6 MB | README《10黄帝内经讲解》 |
| `hdnjsw` | 素问原文 | — |  | original | 15 | high | 84 | 0.4 MB | 《素问》原文 |
| `hk` | 中医喉科学 | 第22课 | ✅ | course | 17 | high | 60 | 0.3 MB | README《22中医喉科学》 |
| `jgyl` | 金匮要略讲解 | 第12课 | ✅ | course | 14 | high | 27 | 0.6 MB | README《12金匮要略讲解》 |
| `kj` | 方剂口诀 | 第07课 | ✅ | course | 16 | high | 12 | 0.1 MB | README《07方剂口诀》（口诀原文） |
| `kjn` | 方剂口诀分篇读本 | 第07课 |  | variant | 16 | medium | 9 | 0.1 MB | kjn00 H1『编者』；07 方剂口诀的分篇读本（衍生版） |
| `kjs` | 方剂口诀语音精简版 | 第07课 |  | variant | 16 | medium | 10 | 0.1 MB | kjs00 H1『说明』、kjs01 H1『四诊心法要诀』；07 口诀的语音精简版（衍生版） |
| `kykt` | 中医科研方法概论 | — |  | auxiliary | 20 | medium | 11 | 0.0 MB | kykt01/02 分章文件；科研方法教材，非 README 21 课 |
| `lk` | 李可急危重症医案 | — |  | auxiliary | 19 | high | 58 | 0.6 MB | lk01-07 H1『破格救心汤救治心衰实录』『肺心病急性感染』等 = 李可医案；README 载教材获李可老中医强烈推荐 |
| `lzcx` | 中医临证程序与辨证思维方法 | 第08课 | ✅ | course | 19 | high | 79 | 0.4 MB | README《08中医临证程序与辨证思维方法》 |
| `mj` | 脉经 | — |  | original | 15 | high | 13 | 0.3 MB | 《脉经》（王叔和）原文 |
| `nj` | 难经 | — |  | original | 15 | high | 90 | 0.0 MB | 《难经》原文 |
| `nk` | 中医内科学 | 第15课 | ✅ | course | 17 | high | 105 | 1.3 MB | README《15中医内科学》 |
| `pwl` | 脾胃论 | — |  | original | 15 | high | 103 | 0.1 MB | 《脾胃论》（李东垣） |
| `qs` | 口诀浅释 | 第07课 | ✅ | course | 16 | high | 34 | 0.5 MB | README《07口诀浅释》；dzb 口诀浅释 1-12 |
| `rm` | 中医概念入门 | — |  | auxiliary | 16 | high | 23 | 0.4 MB | rm 文件书评自引《中医概念入门》6 次（李文强著）；与 rmbook 23 文件名全同、13 同 10 异，字节更多（433KB>429KB）→ 保留此版 |
| `rmbook` | 中医概念入门（异版） | — |  | variant | 不入批次 | medium | 23 | 0.4 MB | rm 异版：23 文件名与 rm 全同，13 同 10 异，429KB<433KB → 不入批次 |
| `shl` | 伤寒论讲解 | 第11课 | ✅ | course | 14 | high | 103 | 1.0 MB | README《11伤寒论讲解》 |
| `shltm` | 宋本伤寒论条目 | — |  | original | 15 | high | 3 | 0.1 MB | 《伤寒论》宋本条目（3 文件） |
| `wbtb` | 温病条辨讲解 | 第13课 | ✅ | course | 14 | high | 44 | 0.9 MB | README《13温病条辨讲解》 |
| `wk` | 中医外科学 | 第16课 | ✅ | course | 17 | high | 126 | 0.9 MB | README《16中医外科学》 |
| `xlcy` | 校报·杏林春雨 | — |  | auxiliary | 20 | medium | 9 | 0.3 MB | xlcy/1988*.md H1『杏林春雨一九八八年九月一日』= 光明中医校报 |
| `ya` | 名医医案选读 | 第23课 | ✅ | course | 19 | high | 351 | 0.5 MB | README《23名医医案选读》 |
| `yjxj` | 历代医籍选介 | 第25课 | ✅ | course | 19 | high | 340 | 0.5 MB | README《25历代医籍选介》 |
| `yk` | 中医眼科学 | 第18课 | ✅ | course | 17 | high | 133 | 0.7 MB | README《18中医眼科学》 |
| `zhencha` | 临证程序·诊察 | — |  | auxiliary | 19 | high | 9 | 0.0 MB | 00qianyan 前言自称《临证程序-诊察》（李文强），引《中医概念入门》与光明《中医药学概论》 |
| `zjs` | 针灸学·上篇经络腧穴 | 第21课 | ✅ | course | 18 | high | 547 | 0.7 MB | README《21针灸学》上篇经络腧穴（zjs=上篇）；据 88 年版电子化（README 分工） |
| `zjx` | 针灸学·下篇治疗 | 第21课 | ✅ | course | 18 | high | 169 | 0.7 MB | README《21针灸学》下篇治疗（zjx=下篇） |
| `zjz` | 针灸学·中篇针灸术 | 第21课 | ✅ | course | 18 | high | 48 | 0.2 MB | README《21针灸学》中篇针灸术（zjz=中篇） |
| `zxyjh` | 中西医结合临床成果 | 第26课 | ✅ | course | 19 | high | 120 | 0.3 MB | README《26中西医结合临床成果》 |
| `zywx` | 实用中医文献学 | 第05课 | ✅ | course | 20 | high | 40 | 0.4 MB | README《05实用中医文献学》；zywx00 H1『编者与编者的话』（0.1/0.2/0.3 为版本迭代文件） |
| `zyzl` | 中医战略 | — |  | auxiliary | 20 | medium | 36 | 0.7 MB | zyzl00 H1『出版说明』；《中医战略》文集 |

## 类型说明

- `course`：光明函大官方课程教材（README 21 课清单）
- `original`：古籍原文/传本（组 15，配套经典讲解课程的底本）
- `variant`：同课程的衍生版或异版
- `auxiliary`：非 21 课的辅助资料（李文强现代著作、李可医案、校史文献等）
- `docx-only`：仅有 docx、无 md/txt，不入批次

## 备注

- daoyan.md（导言）与 dzb.md（电子版录入与校对）为各课共用样板文件，不能作为目录身份依据。
- 组 14-20 即 notebook-batch 批次 B 的文件 14-20；每组拼成 1 个 source（超 HARD_CAP 时按 -1/-2 拆分）。
- rmbook（rm 异版）与 gdhy（仅 docx）不入批次；data/gmzyjc 根目录的提交排名/提交记录.log/remove.py 为过程文件，不入批次。
- lk（李可医案）按内容归组 19 临证与医案；zywx（05 文献学）与 kykt（科研方法）为非临床课程，归组 20 校史与杂纂。
