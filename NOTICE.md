# 版权声明（NOTICE）

本仓库（`ouyang6559/tcm-psych-dataset`）**只存放目录元数据与处理脚本，不存放受版权保护的书籍文件**。

## 1. 本仓库自有内容

- `scripts/`、`docs/`、`README.md`、`catalog/*.json`、`catalog/*.md`：以 [MIT License](./LICENSE) 发布。
- 目录中对各上游项目的介绍文字为重新撰写的摘要，版权归原项目维护者。

## 2. 通过脚本同步到本地的内容

`scripts/sync.sh` 下载的内容**不在本仓库中分发**，其版权归属上游项目：

| 上游 | 许可状态 | 使用要求 |
| --- | --- | --- |
| [xiaopangxia/TCM-Ancient-Books](https://github.com/xiaopangxia/TCM-Ancient-Books) | 无 LICENSE 文件；正文为 1949 年前公版古籍 | 正文可自由使用；建议向上游回馈改进 |
| [lab99x/tcmoc](https://github.com/lab99x/tcmoc) | 无 LICENSE 文件；收录古籍为公版 | 同上；其元数据规范建议遵循上游约定 |
| [6830920/gmzyjc](https://github.com/6830920/gmzyjc) | README 明确声明"公益开放，大家可以广为传播" | 按上游声明自由传播，建议注明来源 |
| [YuanZHAO321/TCM.Skill](https://github.com/YuanZHAO321/TCM.Skill) | **CC BY-NC 4.0** | 必须署名、**禁止商业使用** |
| [openstax/osbooks-psychology](https://github.com/openstax/osbooks-psychology) | 仓库 LICENSE 标注 **CC BY-NC-SA 4.0** | 署名、非商业、**相同方式共享**；网页另提供免费 PDF/EPUB |
| [ouyang6559/ai-books](https://github.com/ouyang6559/ai-books) | 个人收藏，含公版与现代出版物 | 仅限个人学习使用，勿再分发 |
| Lance-myk 两个仓库（标注 `restricted`） | 无 LICENSE，现代讲授内容 | **默认不同步**，使用前须自行确认版权 |

## 3. 明确不纳入的内容

以下来源因版权问题被排除在同步与数据集之外（见 `catalog/sources.json` 的 `excluded`）：

- annas-archive.org
- Z-Lib 系列镜像（zlib.wwkejishe.top、zh.z-lib.sk、zh.z-lib.li 等）
- 各类现代商业出版物的未授权 PDF/EPUB/TXT

`catalog/books.json` 中标注 `not_found` 的 37 本书**只有书名，没有任何下载地址**。这不代表互联网上不存在相关文件，只代表本项目不提供、不索引、不引导未授权副本。

## 4. 生成数据集的使用限制

本地生成的 `dataset/` 目录中可能包含：

- **可自由使用**：公版古籍正文（`tcm/classics/`）
- **须遵守许可**：CC 许可的教材（`tcm/textbooks/tcm-skill/`、`psychology/openstax-psychology/`）
- **仅限个人使用**：`local/ai-books/`、`tcm/restricted/`

将这些内容上传到第三方 AI 服务（NotebookLM、ChatGPT 等）建立私人知识库属于个人使用行为，请勿将生成的知识库、答案全文或衍生数据集公开再分发。公开发布由本数据集生成的内容前，请逐项确认上游许可。
