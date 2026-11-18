# CA-and-AE

Fundamentals of Circuit Analysis and Analog Electronics — 电路分析基础与模拟电子技术考试学习站。

首页先进入**电路分析**，再进入**模拟电子技术**。界面沿用 [qm-shu-review](https://github.com/yizhouren0622-create/qm-shu-review) 的纸张阅读风格，支持中文、英文和中英对照。

## 使用

- **知识与解题**：按认知顺序整理模型条件、解题步骤、易错点、配图和自检。
- **模拟卷与查漏**：每门课提供基础诊断A卷与综合训练B卷，共4套、40道原创题；各卷独立计时、自评分、查漏与打印。先作答，再看提示、解析和评分标准。自评分低于题目70%分值时显示回看知识点。
- **教材逐题**：默认显示授课计划指定作业，也可浏览全书题号清单、按章/题号筛选、查看已核验解析和标记重做。只有实际整理完的题目提供题干与答案。
- **考试范围**：以《电路与模拟电子技术授课计划20260913》第 2–5 页为最高依据。课件支持讲解，教材提供原题。卷面分值与80/100分钟为本站自测设置，不代表实际试卷安排。第6章引言/6.1及7.2.1仅概念，详细参数计算保留为拓展。

练习记录仅保存在当前浏览器，可以导出和导入 JSON 备份；不自动批改手写答案。数学公式已生成为原生 MathML，阅读不依赖外部公式服务。模拟卷提供题目版和含解析版打印。

## 内容状态

详细完成数量和下一步见 [CONTENT_STATUS.md](CONTENT_STATUS.md)。全书题号清单不等于全书解答完成；每题均明确区分已核验解析与待整理。

电路题目按所提供的**第 3 版**抄题和解答，并保留实际版本与页码；授课计划写第 4 版的差异已在范围页说明。模电采用**第 7 版**。原始整本 PDF、完整课件及个人文件路径不随网站上传。

## 本地查看与维护

可直接打开 `index.html`，或在本目录运行：

```sh
python3 -m http.server 8765
```

然后访问 `http://localhost:8765/`。普通阅读无需 Python 环境。

内容在 `data/`，页面由 `build_site.py` 生成。更新内容后：

```sh
python3 -m pip install -r requirements-build.txt
python3 build_site.py
python3 check_site.py
python3 test_math_typesetting.py
```

生成的 HTML 与源数据一起提交。补充教材题时须完整抄题、核对图和页码、列出推导与适用条件，再做独立计算核验；仅完成指定小问时需明确标注，不能计作整题完成。

## GitHub Pages

网站已发布：[在线学习站](https://yizhouren0622-create.github.io/CA-and-AE/)。当前 Pages 来源为 `codex/exam-study-site` 分支的 `/(root)`；更新该分支会自动部署。

本目录可直接作为 GitHub Pages 的发布根目录，包含 `.nojekyll`，所有资源使用相对路径。若以后改用主分支，在仓库 Settings → Pages → Deploy from a branch 中切换发布分支即可。

## English

A bilingual, exam-focused study site with Circuit Analysis first, followed by Analog Electronics. It includes concept and solution guides, original diagnostic papers with rubrics, and a textbook exercise inventory. Checked exercise entries contain transcribed statements, source figures, reasoning and verification. Pending entries do not contain guessed answers. The course plan controls exam scope; source editions and printed/PDF pages remain visible.

Progress is browser-local and exportable. Reading is buildless and equations use native MathML. To regenerate pages, install `requirements-build.txt`, run `python3 build_site.py`, then `python3 check_site.py`.


正文、提示、答案和独立公式统一由 `math_typesetting.py` 构建为原生 MathML；分式、上下标、根号与相量重音离线可读。正文公式使用 `display:inline math`，长公式在自身区域横向滚动。优先为新增内容写明确的 `$…$` 或 TeX 公式，不依赖旧记法识别；分母单位应放在 `\frac` 的分母内，枚举两个数值应写“和”或“分别”，不可用除号代替。文件名/网表标识保持字面形式。检查程序会拒绝正文裸下划线、乘方符号和公式中的斜杠除法，并检查分段公式行数；运行测试覆盖分母单位、指数范围、嵌套分式、相量、微分和中英文正文。
