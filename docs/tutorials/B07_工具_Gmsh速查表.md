# 文档4 配套速查 · Gmsh 函数与英文术语（2026-08-13）

> 用途：读文档4 时卡住就查这里。分四块：① 五步总流程；② 函数速查表；③ 核心函数详解；④ 英文术语表。
>
> 一句话记忆：**Gmsh = 加坯料（occ）→ 提交（synchronize）→ 撒网（mesh）→ 贴标签（PhysicalGroup）→ 存盘（write）**。

---

## 0. 整个文档4 其实只讲了五件事

| 步骤 | 干什么 | 通俗比喻 | 关键函数 |
| --- | --- | --- | --- |
| 1 开机 | 启动 Gmsh，新建模型 | 打开 3D 打印车间，开一个新工单 | `initialize`、`model.add` |
| 2 建模 | 加球/方块/圆柱，用布尔运算切出形状 | 先放坯料，再用布尔刀切/焊/拼 | `occ.addSphere`、`occ.cut`、`occ.fuse` |
| 3 撒网 | 划分网格 | 给几何表面和内部撒一张「渔网」，网眼大小 = 单元尺寸 | `mesh.generate`、`option.setNumber` |
| 4 贴标签 | 标记物理组 | 给每个面和体贴身份证，FEniCSx 才能认出来 | `addPhysicalGroup` |
| 5 存盘收尾 | 导出 .msh，关闭 Gmsh | 把成品打包发货，关灯下班 | `write`、`finalize` |

> 注意：实际脚本里第 4 步（物理组）要放在**所有布尔运算完成之后**，因为布尔操作会改变面的编号。

---

## 1. 函数速查表

### 1.1 启动 / 收尾（每次必有，4 个）

| 函数 | 作用 | 参数 | 返回值 | 出现章节 |
| --- | --- | --- | --- | --- |
| `gmsh.initialize()` | 启动 Gmsh 引擎 | 无 | 无 | §1.4、§2.1 |
| `gmsh.model.add("名字")` | 新建一个模型并命名 | 模型名字符串 | 模型 tag | §1.4、§2.1 |
| `gmsh.write("路径.msh")` | 把网格写到磁盘 | 文件路径 | 无 | §7.1、§18 |
| `gmsh.finalize()` | 关闭 Gmsh，释放内存 | 无 | 无 | §1.4 |

**白话**：`initialize` 是开机，`finalize` 是关机，`write` 是存盘。忘写 `finalize` 一般不会报错，但属于坏习惯。

### 1.2 几何创建（`gmsh.model.occ.*`）——都是「加坯料」，5 个

| 函数 | 作用 | 参数（按顺序） | 返回 | 出现章节 |
| --- | --- | --- | --- | --- |
| `occ.addSphere(x, y, z, r)` | 创建球体 | 球心坐标 x,y,z；半径 r | 体 tag | §3.1 |
| `occ.addBox(x, y, z, dx, dy, dz)` | 创建长方体 | 左下角坐标；三个方向边长 | 体 tag | §3.3、§11.2 |
| `occ.addCylinder(x, y, z, dx, dy, dz, r)` | 创建圆柱体 | 底面圆心；轴向向量；半径 | 体 tag | §3.2、§10 |
| `occ.addCone(x, y, z, dx, dy, dz, r_bottom, r_top)` | 创建圆锥台 | 底面圆心；轴向；底半径；顶半径 | 体 tag | §3.4 |
| `occ.addSurfaceFilling(...)` | 用曲线围成曲面（进阶） | 边界曲线 | 面 tag | §9.2 提及 |

**白话**：每个函数就像车间里「放一个标准坯料」。圆柱的三个关键信息：**放哪里（底面圆心）→ 朝哪个方向长（轴向向量）→ 多粗（半径）**。`addCone` 的顶半径填 0 就是尖圆锥，填非 0 就是圆台（漏斗形）。

### 1.3 几何变换与布尔运算（切/焊/拼/挪），8 个

| 函数 | 作用 | 白话 | 出现章节 |
| --- | --- | --- | --- |
| `occ.synchronize()` | 提交所有待处理的几何操作 | 「把草稿交上去，真正开始算」 | 几乎每节 |
| `occ.cut(A, B)` | 布尔减法：A 减去 B | 用刀 B 从 A 上切掉一块 | §4.2、§4.4 |
| `occ.fuse(A, B)` | 布尔加法：A 和 B 合并 | 把两块料焊成一个整体 | §4.1、§13 |
| `occ.intersect(A, B)` | 布尔相交：只留 A、B 重叠部分 | 只保留两块料压在一起的部分 | §4.3 |
| `occ.fragment(A, B)` | 切分/拼装：两体共享交界面但不合并 | 拼好但**不焊死**，接口处网格对齐 | §13 |
| `occ.rotate(实体, x, y, z, ax, ay, az, 角度)` | 绕某点和某轴旋转实体 | 让坯料转个方向（**角度单位是度**） | §11.2 |
| `occ.translate(实体, dx, dy, dz)` | 平移实体 | 把坯料挪个位置 | §11.2 |
| `occ.getBoundingBox(dim, tag)` | 查实体的包围盒 | 量一个实体的「三围」（最小/最大 x,y,z） | §6.4、§14 |

### 1.4 网格相关（撒网 + 查网），6 个

| 函数 | 作用 | 白话 | 出现章节 |
| --- | --- | --- | --- |
| `mesh.generate(dim)` | 生成网格 | 撒网；dim=1 只在线上布点，2 在面上，3 在体内（常用 3） | §5.2 |
| `mesh.setSize(实体列表, 尺寸列表)` | 在指定位置设局部网格尺寸 | 在重点部位换更密的网眼 | §15.2 |
| `mesh.getNodes()` | 取所有节点 | 数一数网上有多少个「绳结」 | §5.3、§18 |
| `mesh.getElements()` | 取所有单元 | 数一数有多少个「网眼」 | §5.3、§18 |
| `mesh.getElementTypeName(类型编号)` | 把单元类型编号转成名字 | 查 4 号单元叫什么（如 Tetrahedron） | §5.3 |
| `mesh.getQuality()` | 计算网格质量 | 检查网眼有没有「瘪掉变形的」 | §17.2 |

### 1.5 查询与物理组（认人 + 贴标签），2 个

| 函数 | 作用 | 白话 | 出现章节 |
| --- | --- | --- | --- |
| `model.getEntities(dim=2)` | 列出当前所有实体 | 点名册；dim=2 只列面，dim=3 只列体 | §6.4、§13 |
| `model.addPhysicalGroup(dim, [tag...], tag=编号, name="名字")` | 给一组面/体贴物理组标签 | 给一群面或体发身份证 | §6.2、§14 |

### 1.6 常用选项（`gmsh.option.setNumber("选项名", 值)`），14 个

| 选项名 | 什么意思 | 常用值 | 什么时候用 |
| --- | --- | --- | --- |
| `Mesh.CharacteristicLengthMax` | 全局最大网眼尺寸（单元边长上限） | 0.5 / 1.0 / 2.0 | 每次撒网前 |
| `Mesh.CharacteristicLengthMin` | 全局最小网眼尺寸 | 0.1 | 防止网眼过小、算不动 |
| `Mesh.CharacteristicLengthFromCurvature` | 按曲面弯曲程度自动加密 | 1 = 开 | 球壳/藻井凹角 |
| `Mesh.CharacteristicLengthExtendFromBoundary` | 局部细网从边界向外延伸 | 1 = 开 | 局部加密时 |
| `Mesh.Algorithm` | 二维网格算法 | 6 = Frontal-Delaunay（默认） | 默认不动 |
| `Mesh.Algorithm3D` | 三维网格算法 | 1 = Delaunay（默认） | 默认不动 |
| `Mesh.SaveAll` | 导出时是否保留所有内部面 | 1 = 保存 | 导出前 |
| `Mesh.MshFileVersion` | 导出文件格式版本 | 4.1 | 导出前 |
| `Mesh.ElementOrder` | 单元阶次 | 2 = 二阶（10 节点四面体） | 本项目固定用 2 |
| `Mesh.Optimize` | 网格质量优化开关 | 1 = 开 | 质量差时 |
| `Mesh.Smoothing` | 网格平滑迭代次数 | 10 | 质量差时 |

---

## 2. 核心函数详解（C0 之前必须吃透的 8 个）

### 2.1 `cut` —— 本项目第一主角

**语法**：
```python
result = gmsh.model.occ.cut(
    [(3, 外球tag)],      # 被减体（主体，object）
    [(3, 内球tag)],      # 减去的体（工具，tool）
    removeObject=True,   # 是否删除主体原体
    removeTool=True,     # 是否删除工具原体
)
```

**返回值的坑**：`result` 是一个元组 `(outDimTags, outDimTagsMap)`。我们只用第 0 个 `outDimTags`——它是**结果实体列表**，每个元素是 `(dim, tag)`，例如 `[(3, 5)]` 表示「3 维实体，编号 5」。

```python
shell_tag = None
for dim, tag in result[0]:
    if dim == 3:          # 只要体
        shell_tag = tag
```

**removeObject / removeTool 到底管谁**：

| 参数 | 管谁 | True 的含义 | 本项目通常 |
| --- | --- | --- | --- |
| `removeObject` | 第一个参数（主体，如外球） | 切完后把外球原体删掉 | True |
| `removeTool` | 第二个参数（工具，如内球） | 切完后把内球原体删掉 | True |

两个都 True = 外球、内球的原体都删掉，**只留下切出来的壳**。球壳本身是 `cut` 的新产物，不会因为这两个参数被删。

> ⚠️ **文档4 §4.4 原文注释有笔误**：「removeObject=False 保留内球，removeTool=True 删除内球」这句自相矛盾。正确理解：`removeObject` 管外球（主体），`removeTool` 管内球（工具）。示例代码两个参数都写 True 是对的。

**为什么布尔后要找新 tag**：布尔运算会「销毁重建」几何，原来的编号（tag）会失效。所以每次 `cut` 后都要从 `result[0]` 里重新找到壳的 tag，不能接着用旧变量。

### 2.2 `synchronize` —— 提交作业

OCC 内核用的是「延迟评估」：你调 `addSphere`、`cut` 时，Gmsh 只是把命令记在小本本上，**真正执行要等 `synchronize()`**。

规则：
- 每次几何操作（加/切/焊/拼/转/移）之后，做下一次操作**或查询之前**，先 `synchronize()`；
- 忘写最常见的症状：后续查询找不到实体，或切出来是空的。

### 2.3 `fuse` vs `fragment` —— 焊死 vs 拼装

| | `fuse` | `fragment` |
| --- | --- | --- |
| 效果 | 两个体**合并成一体** | 两体**保持独立** |
| 交界面 | 消失 | 保留，且网格节点共享（conformal） |
| 用途 | 只想得到一个整体 | 穹顶 + 鼓座装配（要分别贴标签、分别设材料） |

**记忆**：fuse 是「焊死」，fragment 是「拼好不焊」。装配穹顶和鼓座用 `fragment`，因为 FEniCSx 还要区分两个体，并在交界面施加绑定约束。

### 2.4 `addPhysicalGroup` —— 给 FEniCSx 的身份证

```python
gmsh.model.addPhysicalGroup(2, [42], tag=400, name="dome_base")
#                           ↑    ↑       ↑       ↑
#                     维度(2=面) 面的tag列表  编号    名字
```

- dim=2 是面（边界条件用），dim=3 是体（材料属性用）；
- `tag=` 是自己约定的编号（如 400 = 拱脚面），**编号方案见文档4 §6.3 表**；
- FEniCSx 读网格后，靠这些编号找边界和材料，所以编号必须和求解代码约定一致。

### 2.5 `getEntities` + `getBoundingBox` —— 用位置认面，不靠运气

布尔操作后 tag 会变，**不能死记 tag**。可靠做法：

```python
for dim, tag in gmsh.model.getEntities(dim=2):          # 遍历所有面
    bbox = gmsh.model.occ.getBoundingBox(dim, tag)      # 量三围
    z_min, z_max = bbox[2], bbox[5]                     # 只取 z 方向上下限
    if abs(z_center + 22.03) < 0.01:                    # 在 z=-22.03 附近 → 底面
        bottom_faces.append(tag)
```

`getBoundingBox` 返回 6 个数：`(x_min, y_min, z_min, x_max, y_max, z_max)`，下标 0-5。

### 2.6 `rotate` + `translate` —— 藻井盒子的变身术

```python
gmsh.model.occ.rotate([(3, box)], 0, 0, 0,   # 旋转中心
                                      0, 0, 1,   # 旋转轴
                                      np.degrees(theta_center))  # 角度【度】
gmsh.model.occ.translate([(3, box)], dx, dy, dz)  # 平移
```

**最容易踩的坑**：`rotate` 的角度单位是**度**，而 `np.sin/np.cos` 用的是**弧度**。文档里用 `np.degrees()` 做转换，正好演示了这个坑。

### 2.7 网格尺寸 —— 全局 vs 局部

```python
# 全局：网眼边长上限 0.5m
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.5)

# 局部：在凹角点 (x,y,z) 处加密到 0.15m
gmsh.model.mesh.setSize(gmsh.model.getEntities(0), [(x, y, z, 0.15)])
```

网眼越小越精细，但单元数量爆炸，算得越慢。策略：**全局粗、重点部位局部加密**。

---

## 3. 英文术语表

### 3.1 软件与代码

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| API | 应用程序接口 | 别人写好的「遥控器按钮」，调函数就是按按钮 |
| GUI | 图形界面 | 用鼠标点的窗口界面（Gmsh 也可用 GUI） |
| script / script | 脚本 | 用代码写好的「操作说明书」，让电脑照做 |
| option | 选项/设置 | 控制软件行为的开关和旋钮 |
| parameter | 参数 | 喂给函数的输入值 |
| argument | 实参 | 调用函数时实际填的那个值 |
| return / return value | 返回值 | 函数干完活后交回的结果 |
| module | 模块 | 一个代码文件/功能包，`import gmsh` 就是请它进场 |
| import | 导入 | 把某个库请进来用 |
| tag | 编号/标签 | Gmsh 给每个实体发的整数身份证号 |
| dim / dimension | 维度 | 0=点，1=线，2=面，3=体 |
| entity | 实体 | 几何世界里任何一个可被引用的东西（点线面体统称） |
| kernel | 内核 | 负责「真正计算几何」的引擎 |
| built-in | 内置的 | 软件自带的（Gmsh 自带的轻量几何内核） |
| list | 列表 | 一列数据，如 `[3, 5]` |
| tuple | 元组 | 像列表但不可修改的一包数据，如 `(dim, tag)` |
| dict | 字典 | 键→值对应表，如 `{"dome_inner": 200}` |
| f-string | 格式化字符串 | `f"半径={r}"` 会自动把变量填进文字里 |
| docstring | 函数说明书 | 函数开头三引号里那段说明文字 |
| Args / Returns | 参数说明 / 返回说明 | docstring 里的两节小标题 |
| Path | 路径对象 | Python 里专门管文件路径的类型 |
| mkdir(parents=True, exist_ok=True) | 建文件夹 | 一键建多层目录，已存在也不报错 |
| print | 打印输出 | 在终端显示文字 |

### 3.2 几何

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| OCC / OpenCASCADE | 开源 CAD 几何内核 | 工业级几何引擎，支持布尔运算，本项目专用 |
| point / curve / surface / volume | 点 / 线 / 面 / 体 | 几何的四种基本形态（0D/1D/2D/3D） |
| boolean operation | 布尔运算 | 对几何做「交、并、差」运算 |
| fuse / union | 并集（焊） | 两块料合成一块 |
| cut / difference | 差集（切） | A 减去 B |
| intersect / intersection | 交集 | 只留重叠部分 |
| fragment | 切分/拼装 | 拼好但不合并，交界面共享 |
| synchronize | 同步/提交 | 让 Gmsh 真正执行记下的几何操作 |
| bounding box | 包围盒 | 把实体包住的最小长方体，用 6 个数表示 |
| axis | 轴 | 旋转或圆柱的基准方向线 |
| coordinate | 坐标 | 描述位置的三元组 (x, y, z) |
| radius / diameter | 半径 / 直径 | 半径是直径的一半 |
| sphere / cylinder / cone / box | 球 / 圆柱 / 圆锥台 / 长方体 | Gmsh 直接能造的标准坯料 |
| shell | 壳 | 空心的薄壁结构（外球减内球的结果） |
| ring | 环 | 环形（鼓座像一个大圆环墙） |
| wedge | 楔形体 | 尖劈形，对称切片可能用到 |
| NURBS | 非均匀有理B样条 | 工业级自由曲面表示法，精确变厚度外表面才用 |
| rotate / translation | 旋转 / 平移 | 给实体翻身 / 挪窝 |
| topology | 拓扑 | 几何体之间「怎么连」的结构关系 |

### 3.3 网格

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| mesh | 网格 | 把几何切成小块（单元）的网 |
| generate | 生成 | 执行撒网动作 |
| node | 节点 | 网格的「绳结」，单元角点 |
| element | 单元 | 网格的最小块（四面体/三角形等） |
| tetrahedron (tet) | 四面体 | 四棱锥形状的 3D 单元，本项目主力 |
| characteristic length | 特征长度 | 网格尺寸设定值，网眼大小的「标尺」 |
| curvature | 曲率 | 曲面弯曲的程度，弯得越狠越要加密 |
| Delaunay | 德劳内（算法） | 一种网格算法，生成的三角形/四面体质量均衡 |
| Frontal | 推进波前（算法） | 另一种网格算法，从边界往里推进 |
| MMG3D | 网格重划工具 | 一种实验性的三维网格算法/优化工具 |
| element order | 单元阶次 | 一阶=直边 4 节点，二阶=曲边 10 节点 |
| conformal | 共形/协调 | 两块体交界面上的节点完全对齐、共享 |
| quality | 质量 | 衡量单元形状好不好（越接近正四面体越好） |
| Gamma | 质量指标名 | 0~1 之间的评分，越接近 1 越好 |
| optimize / smoothing | 优化 / 平滑 | 让歪单元变正的两招后处理 |
| size field | 尺寸场 | 描述「每个位置网眼多大」的场 |
| background mesh | 背景网格 | 进阶技巧：用一套粗网格控制另一套细网格 |
| refinement | 加密 | 让局部网眼变细 |

### 3.4 物理组与 FEM

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| physical group | 物理组 | 把若干面/体打包命名，供求解器识别 |
| boundary condition | 边界条件 | 给求解问题设定的「边界规矩」（哪里固定、哪里受力） |
| Dirichlet | 狄利克雷（边界条件） | 直接规定某处位移等于某个值的边界条件（固定端就是它） |
| interface | 交界面 | 两个体之间的接触面 |
| constraint | 约束 | 限制某些自由度不许动 |
| material property | 材料属性 | 密度、弹性模量、泊松比等 |
| fixed support | 固支 | 完全固定、不能动不能转的约束 |
| load | 荷载/载荷 | 施加的力或压力 |
| stress | 应力 | 单位面积上的内力 |

### 3.5 数学与万神殿专有

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| spherical coordinates | 球坐标 | 用 半径r、子午角φ、环向角θ 描述空间点 |
| meridian angle (φ) | 子午角 | 从球顶（Z 轴）往下量到该点的角度 |
| azimuthal angle (θ) | 环向角 | 在水平面里绕 Z 轴转的角度 |
| radian | 弧度 | 角度的数学单位，π = 180° |
| degree | 度 | 角度的常用单位，180° = π |
| arcsin | 反正弦 | 已知正弦值反求角度，如 arcsin(0.2031)≈11.7° |
| clip | 截断/夹取 | `np.clip(t, 1.5, 5.9)` 把 t 限制在 1.5~5.9 之间 |
| oculus | 穹顶圆洞 | 万神殿顶部直径 8.95m 的圆洞 |
| coffer | 藻井 | 穹顶内表面的方形凹槽，5 层 × 28 扇区 |
| drum | 鼓座 | 穹顶下方的环形墙体 |
| base | 基座/底面 | 最底下的支撑部分 |
| inner / outer | 内 / 外 | 内表面/外表面 |
| bottom / edge / face | 底面 / 边缘 / 面 | 几何部位描述 |
| sector | 扇区 | 一圈分成 28 份，每份叫一个扇区 |
| tolerance | 容差 | 判断「算不算相等」的允许误差，如 `< 0.01` |

### 3.6 周边库（PyVista / meshio / numpy）

| 英文 | 中文 | 一句话解释 |
| --- | --- | --- |
| numpy | 数值计算库 | Python 的数学工具箱，`np.sin`、`np.array` 都来自它 |
| meshio | 网格读写库 | 读 .msh 文件的通用工具 |
| pyvista | 三维可视化库 | 把网格画成 3D 图 |
| UnstructuredGrid | 非结构化网格对象 | PyVista 里装四面体网格的容器 |
| plot / show_edges / window_size | 绘图 / 显示边线 / 窗口尺寸 | PyVista 画图时的几个按钮 |
| tetra10 | 10 节点二阶四面体 | 二阶单元的专门名字，PyVista 预览时可能降级显示 |

---

## 4. 记忆口诀

**函数 = 中文动作**：

| 英文函数 | 中文动作 | 联想 |
| --- | --- | --- |
| add | 加 | 加坯料 |
| cut | 剪 | 布尔剪刀 |
| fuse | 焊 | 焊死成一体 |
| intersect | 只留重叠 | 交集 |
| fragment | 拼不焊 | 拼装积木 |
| rotate / translate | 转 / 挪 | 翻身、挪窝 |
| synchronize | 提交 | 交作业 |
| get | 查 | 查询（getEntities=点名，getBoundingBox=量三围） |
| set | 设 | 设置（setSize=定网眼，setNumber=拧旋钮） |
| generate | 生成 | 撒网 |
| write | 存 | 存盘 |
| initialize / finalize | 开 / 关 | 开机、关机 |

**两套角度单位**：

| 场景 | 单位 | 例子 |
| --- | --- | --- |
| Gmsh `rotate` | 度 | 传 `np.degrees(theta)` |
| numpy 三角函数 | 弧度 | `np.sin(phi)`、`np.arcsin(...)` |

**标准流程顺序**（C0 球壳）：

```text
initialize → model.add → addSphere(外) → addSphere(内) → synchronize
→ cut(外, 内) → synchronize → 从 result[0] 找壳 tag
→ 网格设置 → mesh.generate(3) → 物理组 → write → finalize
```

---

## 5. 给你的阅读路线（文档4 第 1–9 章）

1. **§2–§3**：先把立方体和球体示例跑通，只看 4 个函数：`add`、`synchronize`、`generate`、`write`；
2. **§4.4 球壳**：吃透 `cut` 和「布尔后找新 tag」——这是 C0 的心脏；
3. **§5–§6**：记网格尺寸两个选项 + `addPhysicalGroup` 的用法；
4. **§8–§9**：参数化球面（球坐标换算）和变厚度近似——C0 直接要用。

读完标准：不看文档，能默写出 C0 球壳 12 行主流程（上面「标准流程顺序」），并说清 `cut` 返回值的含义。

---

## 6. ⚠️ 文档4 原文两处注意

1. **§4.4 注释笔误**：见 2.1 节。`removeObject` 管主体（外球），`removeTool` 管工具（内球）；示例代码两个 True 是对的。
2. **§9.2 简化方案误差**：均匀厚度近似（平均厚 3.70m）会带来约 ±2m 的厚度偏差。C0 先按简化方案走，脚本里注释标注「近似」即可，严格变厚度留给后续 NURBS 方案。

---

## 实战增补 · 战役新增 API 与选项速查（2026-08-17 实测）

> 本章收录 8/17 藻井攻坚战役中实测验证的 API、选项与失效记录（P-08~P-12）。与正文速查互补：正文是标准库，本章是实战补丁。

### 增补 1：旋转体与布尔（变厚度穹顶战役新增）

| API | 签名要点 | 实测备注 |
| --- | --- | --- |
| `occ.addCircleArc(start, center, end)` | 三点定弧，圆心必须给 | 内球面真圆弧——**平滑弧面比折线更易出好网格**（负雅可比教训） |
| `occ.revolve([(2,surf)], 0,0,0, 0,0,1, angle)` | 绕 z 轴旋转扫角 | 参数化扫角：2π 整天 / 2π/28 切片 |
| `occ.fuse([(3,a)], [(3,b),(3,c)])` | 多工具并集 | 三件焊接共形单体积；**材料分区后置给求解器**（按坐标 callable 赋） |
| `occ.getBoundingBox(dim, tag)` | 返回 (x0,y0,z0,x1,y1,z1) | 位置识别法的基础（z 跨度/位置/半宽三招） |
| `occ.getBoundary([(3,b)], combined, oriented, recursive)` | 取体的边界面/边 | P-09 诊断：面→边能取到，但 fillet 不认边 tag |

### 增补 2：网格控制选项（六招攻坚实测）

| 选项 | 值 | 实测效果 |
| --- | --- | --- |
| `Mesh.HighOrderOptimize` | 2 | 高阶曲边优化：藻井倒转 **14→8**（减不净） |
| `Mesh.SecondOrderLinear` | 1 | 二阶元边中点按直线放置（放弃曲边）：**倒转清零但失曲边精度** |
| `Mesh.CharacteristicLengthMax` | lc | 全局网格密度总开关；**对倒转无效**（几何奇异非网格问题） |
| `Mesh.MshFileVersion` | 4.1 | FEniCSx gmshio 兼容版本 |
| `Mesh.ElementOrder` | 2 | 二阶四面体 CG2（总纲锁定） |

### 增补 3：失效 API 黑名单（P-08~P-12 实测，别踩）

| API | 失效症状 | 替代路线 |
| --- | --- | --- |
| `occ.fillet([(3,box)], edges, radii)` | 对盒体报 **Invalid data**；面→边能取到但 API 不认 OCC 边 tag（P-09） | 手工画圆角截面（8 切线点+4 圆弧）+ `occ.extrude` 挤出 |
| `occ.chamfer(..., [d1,d2]*n)` | 签名不符（P-09） | 同上 |
| 棱边 `setSize` 局部加密 | 布尔切割后**失效**（P-11，布尔重建几何实体，局部尺寸约束丢失） | 接受局限换思路（切片/直边） |
| 质量检查 API 在倒转处 | 倒转单元报错（P-08） | 容错处理（try/except） |

### 增补 4：核心机理一页版

- **tag 作废原理**：布尔运算生成新实体、Gmsh 重新编号；与删不删原体无关。永远从 `result[0]` 重新取 tag。
- **再入角数量决定倒转**：140 个 90° 凹角 → 8 个倒转；28 切片（5 个凹角）→ 0 倒转。**网格质量问题的根在几何。**
- **相切布尔是病态之源**：工具比目标多伸一截（margin）是几何脚本的保险丝。
- **synchronize 纪律**：每次 OCC 操作后 `gmsh.model.occ.synchronize()`——几何「消失」九成是忘了它。

### 增补小练习

1. 写出用 revolve 生成「完整甜甜圈」的伪代码（截面 + 轴）。
2. 为什么 SecondOrderLinear=1 能清倒转但「失曲边精度」？精度丢在哪？
3. fillet 失效后的两条替代路线分别是什么？
