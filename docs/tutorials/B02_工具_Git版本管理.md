# 文档1 · Git 版本管理从零到项目协作（重构版）

> **项目**：万神殿穹顶三维 FEM 重构
> **版本**：v2.0 轮次 1/3（2026-08-13 逐轮重写）
> **定位**：实用工具书——只教你日常真的会用到的命令

---

## 写给你的使用说明（30 秒读完）

Git 不用全学，**日常 80% 时间只需要 5 条命令**。

本教材按「任务」组织，不按命令字典组织：

1. **第一次提交**：把项目存进版本库；
2. **日常循环**：改代码 → 看状态 → 提交 → 推送；
3. **出错了**：撤销、回退、解决冲突。

学完标准：**能独立完成每天「改完代码提交一次」，出问题时知道查哪节**。

### 🎩 老板版速读（30 秒，Leader 必读）

你不用敲 Git 命令，但**每天要检查 AI 是否守规矩**：

1. 提交信息带前缀（feat/fix/docs/refactor/test）；
2. `output/`、`__pycache__/`、`*.msh` 没被提交（.gitignore 生效）；
3. 每天结束时 `git push` 成功（云备份在）；
4. 大改动前先 `git status` / `git diff`（不让 AI 蒙头改）。

一句话指挥：「改完提交，信息按规范，push 前给我看 diff」。

---

## 第 1 章 Git 是什么

### 1.1 一句话版本

**Git 是一个「存档系统」：每次存一个档（commit），随时可以回到任何一档。**

### 1.2 为什么必须有 Git

没有 Git 的噩梦：

- 文件叫 `final.py`、`final2.py`、`final_真的不改了.py`；
- 改坏了想还原，发现没备份；
- 不知道哪次改动引入了 bug。

有 Git 之后：

- 每次有意义的改动存一档；
- 每档带说明（commit message）；
- 随时 `git diff` 看改了什么、`git checkout` 还原。

### 1.3 三个核心概念（白话版）

| 概念 | 白话 | 类比 |
| --- | --- | --- |
| 仓库（repository） | 项目的存档库 | 游戏存档文件夹 |
| 提交（commit） | 一个存档点 | 手动存档 |
| 远程（remote） | 云上的备份 | 云存档（GitHub） |

### 1.4 工作区 → 暂存区 → 仓库

```text
工作区（你正在改的文件）
   ↓  git add
暂存区（准备提交的清单）
   ↓  git commit
仓库（存档历史）
   ↓  git push
远程仓库（GitHub 云备份）
```

**暂存区是新手最容易懵的地方**：它像一个「购物车」，`git add` 是把商品放进购物车，`git commit` 才是结账存档。

### 1.5 本章小结

1. Git = 存档系统，commit 是存档点；
2. 三个区：工作区 → 暂存区 → 仓库 → 远程；
3. add 放购物车，commit 结账，push 云备份。

### 1.6 小练习

1. 用「游戏存档」比喻向室友解释 Git；
2. 说出 add / commit / push 分别对应三个区之间哪一步；
3. 思考：为什么每次提交要写说明？

---

## 第 2 章 日常五命令：从零到第一次提交

### 2.1 本章目标

学会 5 条命令，覆盖 80% 日常：

```text
git status    看状态
git add       放入暂存区
git commit    存档
git push      云备份
git pull      拉取最新
```

### 2.2 第一次提交（以万神殿为例）

**第 1 步：看状态**

```bash
cd /mnt/c/Users/tan83/Desktop/codex/pantheon-3d-fem
git status
```

会看到「未跟踪文件」（Untracked files）——这些是新文件，Git 还没管。

**第 2 步：全部加入暂存区**

```bash
git add .
```

`. = 当前目录所有文件`。`git status` 再看，文件变绿色 = 已进暂存区。

**第 3 步：提交（存档）**

```bash
git commit -m "feat: 完成 C0 球壳几何脚本"
```

**第 4 步：推送云端**

```bash
git push
```

（第一次推送需要 `-u origin main` 设置上游，之后直接 `git push`。）

### 2.3 日常循环（每天的标准动作）

```bash
# 1. 改完代码后，看改了什么
git status
git diff            # 具体改动内容

# 2. 加入暂存区
git add geometry/c0_spherical_shell.py   # 只加这个文件
# 或 git add .   全部加

# 3. 提交
git commit -m "fix: 修正球壳外半径计算"

# 4. 云备份（一天结束时）
git push
```

**提交信息规范（本项目）**：

| 前缀 | 含义 | 例子 |
| --- | --- | --- |
| `feat:` | 新功能 | `feat: 添加 Oculus 切割` |
| `fix:` | 修 bug | `fix: 修正密度单位` |
| `docs:` | 文档 | `docs: 重写文档4 第5章` |
| `refactor:` | 重构 | `refactor: 拆分 build_shell 函数` |
| `test:` | 测试 | `test: 添加网格收敛测试` |

### 2.4 查看历史

```bash
git log --oneline -10          # 最近 10 条（一行一条）
git log --stat -3              # 最近 3 条 + 改了哪些文件
```

输出示例：

```text
a1b2c3d feat: 完成 C0 球壳几何脚本
e4f5g6h docs: 重写文档4
```

### 2.5 常见问题

| 问题 | 原因 | 解决 |
| --- | --- | --- |
| 忘记 add 就 commit | 空提交 | 先 `git add .` 再 commit |
| push 被拒 | 远程有别人提交 | `git pull` 后再 push |
| commit 信息写错 | 手滑 | `git commit --amend -m "新信息"` |
| 把不该提交的文件提交了 | 没配 .gitignore | 见 2.6 |

### 2.6 .gitignore：让 Git 别碰这些文件

项目已有 `.gitignore`，关键内容：

```text
__pycache__/      # Python 缓存
output/           # 仿真输出（太大）
.venv/            # 虚拟环境
*.msh             # 网格文件（可重新生成）
```

规则：**能重新生成的文件都不提交**。

### 2.7 本章小结

1. 五命令：status / add / commit / push / pull；
2. 日常循环：改 → add → commit → push；
3. 提交信息规范：feat/fix/docs/refactor/test；
4. `.gitignore` 让 Git 不碰缓存和大文件。

### 2.8 小练习

1. 在万神殿仓库跑 `git status`，看懂输出；
2. 做一次真实提交（改一行注释），用规范信息；
3. 默写五条命令。

---

## 第 3 章 分支、撤销与冲突：出问题不慌

### 3.1 本章目标

1. 理解分支（branch）并会创建/合并；
2. 掌握撤销的三种场景；
3. 会处理合并冲突。

### 3.2 分支：平行世界的存档

**分支 = 在某个存档点开出一条平行线**。主分支 `main` 是正史，实验分支是「假如」。

```bash
# 创建并切换到新分支
git checkout -b experiment

# 在实验分支上随意折腾...

# 实验成功：合并回 main
git checkout main
git merge experiment

# 实验失败：直接删掉分支（干净）
git branch -d experiment
```

**万神殿的用法**：平时单人项目可以只用一个 `main` 分支；要做大改动（比如重构求解器）时开分支，成功再合并。

### 3.3 撤销：三种场景

**场景 A：还没 commit（只想扔掉改动）**

```bash
# 丢弃单个文件的修改
git checkout -- 文件名

# 丢弃所有修改（危险！不可恢复）
git checkout -- .
```

⚠️ 只用于「还没 add/commit」的改动。

**场景 B：add 错了（从暂存区拿出来）**

```bash
git restore --staged 文件名
```

文件从购物车拿出来，工作区的改动还在。

**场景 C：commit 后悔了**

```bash
# 撤销最近一次 commit，但保留改动在工作区（推荐）
git reset --soft HEAD~1

# 连改动一起丢弃（危险）
git reset --hard HEAD~1
```

`HEAD~1` = 上一个存档点。**`--hard` 是核弹，用了不可恢复**，除非已 push。

### 3.4 冲突：两个人改了同一处

合并时如果两边改了同一行，Git 会停下来说：

```text
CONFLICT (content): Merge conflict in config/params.py
```

打开文件会看到：

```text
<<<<<<< HEAD
R_INNER = 22.03        # 你的版本
=======
R_INNER = 22.00        # 别人的版本
>>>>>>> feature-branch
```

**解决步骤**：

1. 手动编辑：保留正确的行，删掉 `<<<<<<<`、`=======`、`>>>>>>>` 三行标记；
2. 保存文件；
3. `git add 文件`；
4. `git commit`（完成合并）。

> 冲突不可怕，可怕的是「闭眼删一半」。看清两边各是什么，再决定保留谁。

### 3.5 回退到旧版本

```bash
# 查看某次提交的代码（只读）
git show a1b2c3d:geometry/c0_spherical_shell.py

# 整个仓库回到某提交（不保留之后提交）
git reset --hard a1b2c3d

# 只把某个文件恢复到某提交
git checkout a1b2c3d -- geometry/c0_spherical_shell.py
```

### 3.6 本章小结

1. 分支 = 平行存档，`checkout -b` 创建，`merge` 合并；
2. 撤销三场景：未提交 `checkout --`，暂存 `restore --staged`，已提交 `reset`；
3. `--hard` 是核弹，慎用；
4. 冲突 = 手动保留正确内容 + 删标记 + add + commit。

### 3.7 小练习

1. 开一个分支，改点东西，合并回 main，再删除分支；
2. 造一个冲突（两个分支改同一行），练习解决；
3. 说出 `--hard` 为什么危险。

---

## 第 4 章 命令速查卡

### 日常

| 想干什么 | 命令 |
| --- | --- |
| 看状态 | `git status` |
| 看改动 | `git diff` |
| 全部暂存 | `git add .` |
| 存一档 | `git commit -m "feat: ..."` |
| 云备份 | `git push` |
| 拉最新 | `git pull` |
| 看历史 | `git log --oneline -10` |

### 分支

| 想干什么 | 命令 |
| --- | --- |
| 建并切分支 | `git checkout -b 名字` |
| 切回 main | `git checkout main` |
| 合并 | `git merge 分支名` |
| 删本地分支 | `git branch -d 名字` |
| 看所有分支 | `git branch -a` |

### 撤销

| 想干什么 | 命令 | 危险度 |
| --- | --- | --- |
| 丢未提交改动 | `git checkout -- 文件` | 中 |
| 暂存区拿出来 | `git restore --staged 文件` | 低 |
| 撤销 commit 保改动 | `git reset --soft HEAD~1` | 低 |
| 撤销 commit 丢改动 | `git reset --hard HEAD~1` | 🔴 高 |

### 审核清单

- [ ] 每天至少一次 `git commit` + `git push`
- [ ] 提交信息带前缀（feat/fix/docs/refactor/test）
- [ ] 不提交 `output/`、`__pycache__/`、`*.msh`
- [ ] 重要改动前看 `git status` 和 `git diff`
- [ ] 出问题先查本节，再动 `--hard`

---

> 全书完（v2.0，2026-08-13 重写）。旧版存档于 `_legacy/`。

---

## 实战增补 · 万神殿仓库的 git 全实录（2026-08）

> 本章基于《万神殿全解》成书卷二：31 个 commit 的完整编年史、真实踩过的 git 坑、以及「代码入库数据不入库」的项目级纪律。

### 增补 1：一个真实项目的 commit 编年史（33 commits 全景）

万神殿主仓库 8/10 建仓，8/17 决战日一天 16 个 commit。读 commit 历史 = 读项目传记：

| 期 | commit 数 | 内容 |
| --- | --- | --- |
| 骨架期 8/10 | 6 | 仓库骨架→资料归集→路径修正→日志→中继文档→索引修复 |
| 环境参数期 8/11 | 1 | D1 环境全绿 + P1/P2/P3/P5 参数定稿 |
| 教材与认知 8/13-16 | 8 | 教程对齐 dolfinx 0.8、C1 全链、网格无关性、Rankine 损伤 |
| **决战日 8/17** | **16** | C4 文献重标定→藻井网格六招→C6 证伪→C7 收官→57° 机理闭环 |
| 8/18 | 2+1 | 成书 15 卷入库、圆角功能入库 |

**commit message 规范实战**：`feat(geo): C3 圆角藻井 --round 开关与 P-09 诊断留档`——feat/docs 前缀 + 范围 + 一句话结论。好的 commit message 是「给三个月后的自己写的信」。

### 增补 2：三个真实踩过的坑

**坑 1：dubious ownership（沙箱/多用户环境必踩）**
沙箱用户与文件属主 SID 不同 → git 拒读仓库。正确姿势：
```bash
git -c safe.directory="C:/path/to/repo" -C "C:/path/to/repo" log --oneline
```
**铁律：单命令参数绕过，绝不写全局 config**（全局 safe.directory 是安全后门）。

**坑 2：docs 索引行被转义为 NUL**
AI 写文档时某字符变成空字节（\0），git 与编辑器表现各异。症状是文档「看起来正常但 grep 不到」。解法：重写该行。**AI 产出的文档要抽查不可见字符。**

**坑 3：嵌套仓库的隔离**
legacy_v1 自带独立 .git（13 commit 历史）。父仓库用 .gitignore 排除它，另存 bundle 备份——双保险归档，互不干扰。

### 增补 3：.gitignore 三道防线（本项目实战设计）

```gitignore
# Python 垃圾
.venv/  __pycache__/  *.pyc
# 仿真产物（动辄百 MB，绝不入库）
output/  *.vtu  *.xdmf  *.h5  *.pvd
# 旧项目存档
legacy_v1/
```

**设计思想**：代码与文档入库，数据与产物留本地。网格文件是「可重新生成的中间产物」，生成脚本（geometry/*.py）才是资产。问自己：这个文件删除后能否用 git 里的东西重新生成？能 → 不该入库。

### 增补 4：git bundle——比移动 .git 更稳的归档

```bash
git bundle create pantheon-v1-full.bundle --all   # 打包全部历史
git clone pantheon-v1-full.bundle <目录>           # 完整还原
```
1.41 MB 单文件 = 13 个 commit 的完整仓库。归档、传输、备份三合一。

### 增补小练习

1. 用 `git log --oneline` 看本项目 8/17 那天的 16 个 commit，用一句话概括每个 commit 在讲什么。
2. 你的 .gitignore 里有没有「能重新生成的产物」该加未加？
3. 模拟一次：git 报 dubious ownership 时，写出你的绕过命令（不写全局 config）。
