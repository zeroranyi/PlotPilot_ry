# 信息结构梳理与重构建议

## 📊 当前信息层级

### 1️⃣ **小说级别（Novel）**
- 基本信息：标题、作者、目标章节数、前提
- 数据表：`novels`

### 2️⃣ **章节级别（Chapter）**
- 基本信息：章节号、标题、内容、大纲、状态
- 数据表：`chapters`

### 3️⃣ **世界观设定（Bible）**
包含：
- **角色（Characters）** - `characters` 表
  - 姓名、角色类型、描述、重要性
- **地点（Locations）** - `locations` 表
  - 名称、类型、描述
- **时间线笔记（Timeline Notes）** - `timeline_notes` 表
  - 事件、时间点、描述
- **风格笔记（Style Notes）** - `style_notes` 表
  - 分类、内容

### 4️⃣ **知识图谱（Knowledge Graph）**
- **三元组（Triples）** - `triples` 表
  - subject-predicate-object 关系
  - 支持角色、地点等实体类型
  - 关联章节、重要性、标签
- **章节摘要（Chapter Summaries）** - `chapter_summaries` 表
  - 章节号、摘要

### 5️⃣ **事件系统（Events）**
- **事件（Events）** - `events` 表
  - 事件类型、描述、故事时间、重要性
  - 关联章节
- **事件-角色关联** - `event_characters` 表

### 6️⃣ **故事结构（Story Structure）**
- **故事节点（Story Nodes）** - `story_nodes` 表
  - 树形结构：部/卷/幕/章节
  - 节点类型、标题、描述、章节范围
  - 规划状态、来源（手动/AI宏观/AI幕级）

### 7️⃣ **章节元素（Chapter Elements）** - 新增
- **章节元素关联** - `chapter_elements` 表
  - 元素类型（角色/地点/物品/组织/事件）
  - 关联类型、重要性、出场顺序

---

## 🤔 问题：故事线、情节弧、时间线的定位

### 当前实现（代码中存在，但未持久化）

#### **故事线（Storyline）** - `domain/novel/entities/storyline.py`
- 类型：主线/支线/角色线/感情线
- 状态：活跃/暂停/完成
- 章节范围：起始章节-结束章节
- 里程碑：关键节点列表
- **❌ 没有对应的数据表**

#### **情节弧（PlotArc）** - `domain/novel/entities/plot_arc.py`
- 剧情点列表（章节号 + 张力水平）
- 张力曲线插值计算
- **❌ 没有对应的数据表**

#### **时间线笔记（Timeline Notes）** - `timeline_notes` 表
- 当前只是 Bible 中的简单笔记
- 没有结构化的时间线系统
- **✅ 有数据表，但功能简单**

---

## 💡 建议的信息层级重构

### 方案：将故事线、情节弧、时间线提升为与 Bible 同级

```
小说（Novel）
├── 章节（Chapters）
│
├── 世界观设定（Bible）- 静态设定
│   ├── 角色（Characters）
│   ├── 地点（Locations）
│   ├── 风格笔记（Style Notes）
│   └── 世界设定（World Settings）
│
├── 故事结构（Story Structure）- 层级结构
│   └── 树形节点（部/卷/幕/章节）
│
├── 📍 故事线系统（Storylines）【新增/提升】- 叙事线索
│   ├── 主线（Main）
│   ├── 支线（Sub）
│   ├── 角色线（Character）
│   └── 感情线（Romance）
│
├── 📍 情节弧系统（Plot Arcs）【新增/提升】- 张力曲线
│   ├── 整体张力曲线
│   ├── 关键剧情点
│   └── 冲突/高潮/解决
│
├── 📍 时间线系统（Timeline）【增强/独立】- 时间流逝
│   ├── 故事时间轴
│   ├── 事件序列
│   └── 时间跨度管理
│
├── 知识图谱（Knowledge Graph）- 关系网络
│   ├── 三元组（Triples）
│   └── 章节摘要（Summaries）
│
└── 章节元素（Chapter Elements）- 元素关联
    └── 元素关联关系
```

---

## 🎯 三者的区别与联系

### **故事线（Storyline）**
- **作用**：追踪特定主题/角色的发展轨迹
- **粒度**：跨越多个章节的连续叙事
- **例子**：
  - 主线：主角的成长之路（第1-100章）
  - 支线：寻找神器（第20-45章）
  - 角色线：反派的阴谋（第10-80章）
  - 感情线：男女主的关系发展（第5-100章）
- **关键属性**：
  - 类型、状态、章节范围
  - 里程碑列表（关键节点）
  - 当前进度

### **情节弧（Plot Arc）**
- **作用**：控制整体节奏和张力
- **粒度**：全局的情绪曲线
- **例子**：
  - 第1-20章：低张力（铺垫）
  - 第21-40章：中张力（冲突升级）
  - 第41-50章：高张力（高潮）
  - 第51-60章：低张力（收尾）
- **关键属性**：
  - 剧情点列表（章节号 + 张力水平）
  - 张力插值计算
  - 下一个剧情点

### **时间线（Timeline）**
- **作用**：管理故事内时间流逝
- **粒度**：具体的时间点和事件
- **例子**：
  - 第1章：2024年1月1日，主角出生
  - 第10章：2044年1月1日，主角20岁生日
  - 第20章：三个月后，主角遇到导师
  - 第50章：一年后，最终决战
- **关键属性**：
  - 绝对时间（具体日期）
  - 相对时间（"三天后"、"两年前"）
  - 时间跨度
  - 关联事件

---

## 🔗 三者的关联关系

```
故事线（Storyline）
  ├── 关联到情节弧的某个阶段
  │   例：主线在第40章进入高潮阶段
  │
  └── 包含多个里程碑
      └── 里程碑关联到具体章节
          └── 章节关联到时间线事件

情节弧（Plot Arc）
  └── 定义全局张力曲线
      └── 影响所有故事线的节奏

时间线（Timeline）
  └── 记录事件发生的时间
      └── 事件关联到章节
          └── 章节推进故事线
```

---

## 📋 重构建议

### 1. **合并/增强时间线系统**

**当前问题：**
- `timeline_notes` 只是 Bible 下的简单笔记
- `events` 表已经有故事时间字段，但两者分离

**建议方案：**
- 将 `timeline_notes` 从 Bible 中独立出来
- 与 `events` 表整合，形成统一的时间线系统
- 支持：
  - 绝对时间（2024-01-01）
  - 相对时间（"三天后"）
  - 时间跨度（"持续一周"）
  - 时间锚点（"主角生日"）

### 2. **持久化故事线和情节弧**

**创建数据表：**

```sql
-- 故事线表
CREATE TABLE storylines (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    storyline_type TEXT NOT NULL,  -- main/sub/character/romance
    status TEXT NOT NULL,  -- active/paused/completed
    estimated_chapter_start INTEGER NOT NULL,
    estimated_chapter_end INTEGER NOT NULL,
    current_milestone_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 故事线里程碑表
CREATE TABLE storyline_milestones (
    id TEXT PRIMARY KEY,
    storyline_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    description TEXT NOT NULL,
    target_chapter INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (storyline_id) REFERENCES storylines(id) ON DELETE CASCADE
);

-- 情节弧表
CREATE TABLE plot_arcs (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    name TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 剧情点表
CREATE TABLE plot_points (
    id TEXT PRIMARY KEY,
    plot_arc_id TEXT NOT NULL,
    chapter_number INTEGER NOT NULL,
    tension_level INTEGER NOT NULL,  -- 1-5
    plot_point_type TEXT,  -- setup/conflict/climax/resolution
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plot_arc_id) REFERENCES plot_arcs(id) ON DELETE CASCADE
);
```

### 3. **在章节生成时使用**

**ContextBuilder 应该查询：**

```python
# Layer 1: 核心上下文
- 当前活跃的故事线
- 待完成的里程碑
- 当前章节的期望张力水平（从情节弧）
- 当前时间线位置

# Layer 2: 智能检索
- 基于故事线的相关角色/地点
- 基于时间线的相关事件
- 基于张力水平的参考章节

# Layer 3: 最近上下文
- 最近章节推进的故事线
- 最近完成的里程碑
- 最近的时间线事件
```

---

## 🎯 实施优先级

### 阶段一：持久化（高优先级）
1. 创建 `storylines` 和 `storyline_milestones` 表
2. 创建 `plot_arcs` 和 `plot_points` 表
3. 迁移现有代码中的 Storyline 和 PlotArc 到数据库

### 阶段二：时间线增强（中优先级）
1. 增强 `events` 表，支持更丰富的时间表示
2. 考虑是否将 `timeline_notes` 合并到 `events`
3. 添加时间线查询和管理 API

### 阶段三：章节生成集成（高优先级）
1. 在 ContextBuilder 中集成故事线查询
2. 在 ContextBuilder 中集成情节弧查询
3. 在 ContextBuilder 中集成时间线查询
4. 优化 token 预算分配

---

## ❓ 待讨论的问题

1. **是否要为 Storyline 和 PlotArc 创建数据表？**
   - 建议：是，必须持久化

2. **时间线是否要从 Bible 中独立出来，与 Events 整合？**
   - 建议：是，时间线应该是独立的一级系统

3. **三者在章节生成时的优先级？**
   - 建议：故事线（必须） > 情节弧（重要） > 时间线（参考）

4. **是否需要前端界面管理这三个系统？**
   - 建议：是，需要可视化编辑界面
