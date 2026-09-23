# 57 本目标书 · 逐本映射表

> 由 `scripts/render_catalog.py` 生成于 2026-09-23，唯一事实来源是 [`books.json`](./books.json)，请勿直接编辑本文件。

## 统计

| 状态 | 数量 | 含义 |
| --- | --- | --- |
| ✅ available | 7 | 有公版/开放原文可直接用于 AI |
| 🔶 related | 12 | 存在相关资料，但不是你指定的那个版本 |
| ❌ not_found | 38 | 未找到可确认合法授权的对应电子版 |

> ⚠️ `related` 不等于就是那本书。喂 AI 时请在提示词里注明实际来源与版本，避免模型把不同版本混为一谈。

## 逐本表

| # | 书名 | 分类 | 状态 | 可用来源 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 高敏感是种天赋 | psychology | ❌ not_found | — | 现代商业出版物，无合法 GitHub 全本 |
| 2 | 高敏感是种天赋Ⅱ·践行篇 | psychology | ❌ not_found | — | 同上 |
| 3 | 高敏感是种天赋Ⅲ·沟通篇 | psychology | ❌ not_found | — | 同上 |
| 4 | 中医诊断学 | tcm-textbook | 🔶 related | [tcm-skill](https://github.com/YuanZHAO321/TCM.Skill) | 七版教材知识库；非李灿东/方朝义指定 ISBN 原版 |
| 5 | 方剂学 | tcm-textbook | 🔶 related | [tcm-skill](https://github.com/YuanZHAO321/TCM.Skill) | 教材知识库；非李冀/季旭明指定版。公版本草底本另见 tcm-ancient-books |
| 6 | 中药学 | tcm-textbook | 🔶 related | [tcm-skill](https://github.com/YuanZHAO321/TCM.Skill) | 教材知识库；非钟赣生/杨柏灿指定版。公版本草底本见 tcm-ancient-books《神农本草经》《本草经集注》《新修本草》《本草备要》等 |
| 7 | 中医儿科学 | tcm-textbook | 🔶 related | [gmzyjc](https://github.com/6830920/gmzyjc) | 含《20中医儿科学》；1985 函授版，非赵霞/李新民新世纪第五版 |
| 8 | 中医妇科学 | tcm-textbook | 🔶 related | [gmzyjc](https://github.com/6830920/gmzyjc) | 含《19中医妇科学》；公益不同版 |
| 9 | 中医基础理论 | tcm-textbook | 🔶 related | [tcm-skill](https://github.com/YuanZHAO321/TCM.Skill) | 教材知识库；非郑洪新指定版 |
| 10 | 中医内科学 | tcm-textbook | 🔶 related | [tcm-skill](https://github.com/YuanZHAO321/TCM.Skill) | 七版知识库；同主题公益版另见 gmzyjc《15中医内科学》 |
| 11 | 中医外科学 | tcm-textbook | 🔶 related | [gmzyjc](https://github.com/6830920/gmzyjc) | 含《16中医外科学》；公益不同版，非陈红风指定版 |
| 12 | 针灸学 | tcm-textbook | 🔶 related | [tcm-skill](https://github.com/YuanZHAO321/TCM.Skill) | 教材知识库；gmzyjc 另含《21针灸学》；公版针灸底本《针灸甲乙经》《针灸大成》见 tcm-ancient-books |
| 13 | 医古文 | tcm-textbook | ❌ not_found | — | 未找到可确认授权的版本；古文原篇可从 tcmoc / tcm-ancient-books 中按篇目取 |
| 14 | 黄帝内经·上古天真 | tcm-classic | ✅ available | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 《素问》原典可直接用；非徐文兵/梁冬讲读版 |
| 15 | 黄帝内经·四气调神 | tcm-classic | ✅ available | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 原典参照；非对话版 |
| 16 | 黄帝内经·天年 | tcm-classic | ✅ available | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 原典参照；非徐文兵套装 |
| 17 | 黄帝内经·异法方宜 | tcm-classic | ✅ available | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 原典参照；非对话版 |
| 18 | 黄帝内经·金匮真言 | tcm-classic | ✅ available | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 原典参照；非对话版 |
| 19 | 黄帝内经·灵枢·通天 | tcm-classic | ✅ available | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 《灵枢》原典；tcmoc 亦收《灵枢集注》《灵枢识》等注释本 |
| 20 | 黄帝内经讲什么（导读册） | tcm-classic | ❌ not_found | — | 现代导读册，无合法全本；可用《素问》《灵枢》原典 + tcmoc 注释本自行导读 |
| 21 | 美食课：主食万岁 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 22 | 美食课：春季养肝 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 23 | 美食课：夏季养心 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 24 | 美食课：长夏养脾 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 25 | 美食课：秋季养肺 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 26 | 美食课：冬季养肾 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 27 | 黄帝内经四季养生法（第2版） | tcm-classic | 🔶 related | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 素问/灵枢原典参照；非中国中医药出版社现代编著版 |
| 28 | 字里藏医 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 29 | 知己 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 30 | 饮食滋味 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 31 | 梦与健康 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 32 | 徐文兵讲黄帝内经·前传（上下册） | tcm-classic | ❌ not_found | — | 现代出版物 |
| 33 | 黄帝内经的智慧 | tcm-classic | ❌ not_found | — | 现代出版物 |
| 34 | 黄帝内经（彩图精装·全注全译无删减） | tcm-classic | ✅ available | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 素问/灵枢/太素/内经知要等公版底本；非李爱勇民主与建设指定版 |
| 35 | 漫画《黄帝内经》（全2册） | tcm-classic | ❌ not_found | — | 现代出版物 |
| 36 | 漫画读懂《黄帝外经》 | tcm-classic | ❌ not_found | — | 《黄帝外经》原典可在 tcm-ancient-books / tcmoc 查到；漫画改编本为现代出版物 |
| 37 | 未发现的自我 | psychology | ❌ not_found | — | 荣格著作，中译本受版权保护 |
| 38 | 红书（The Red Book） | psychology | ❌ not_found | — | 原文与中译本均受版权保护 |
| 39 | 金花的秘密 | psychology | 🔶 related | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 公版底本《太乙金华宗旨》《慧命经》可查；荣格评述 + 卫礼贤译文受版权，无合法 GitHub 全本 |
| 40 | 荣格自传（回忆·梦·思考） | psychology | ❌ not_found | — | 现代出版物 |
| 41 | 让往事随风而逝（EMDR） | psychology | ❌ not_found | — | 现代出版物 |
| 42 | 玫瑰从来不慌张 | psychology | ❌ not_found | — | 现代出版物 |
| 43 | 人生没有多余的灰 / 疼 | psychology | ❌ not_found | — | 现代出版物 |
| 44 | 不原谅也没关系（CPTSD 自愈手册） | psychology | ❌ not_found | — | 现代出版物 |
| 45 | 身体从未忘记 | psychology | ❌ not_found | — | 现代出版物；OpenStax 心理学中有创伤应激相关章节可作学术替代 |
| 46 | 被讨厌的勇气 | psychology | ❌ not_found | — | 现代出版物；阿德勒理论可参考 OpenStax 心理学对应章节 |
| 47 | 中医心理治疗 | tcm-textbook | ❌ not_found | — | 未找到可确认授权的电子版 |
| 48 | 解剖列车（第4版） | fascia | ❌ not_found | — | 现代出版物 |
| 49 | 身体解读 | fascia | ❌ not_found | — | 现代出版物 |
| 50 | 筋膜灸疗学 | fascia | ❌ not_found | — | 现代出版物 |
| 51 | 筋膜学 | fascia | ❌ not_found | — | 现代出版物 |
| 52 | 筋膜学与中医学 | fascia | ❌ not_found | — | 现代出版物 |
| 53 | 筋膜学（通用教科书） | fascia | ❌ not_found | — | 现代出版物 |
| 54 | 筋膜学 | fascia | ❌ not_found | — | 现代出版物 |
| 55 | FASCIOLOGY（筋膜学）期刊 | fascia | ❌ not_found | — | 期刊，可经 NSSD / PubMed 按篇检索 |
| 56 | 中医情志学 | tcm-textbook | ❌ not_found | — | 现代出版物；情志理论原典见《黄帝内经》七情论述与 tcmoc 医经类 |
| 57 | 《伤寒论》情志病辨证论治规律 | tcm-textbook | 🔶 related | [tcm-ancient-books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 《伤寒论》原典可用；该专题研究论文可经 NSSD 检索 |
