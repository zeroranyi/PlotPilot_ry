# 故事结构规划完整设计 - 串联 Bible 元素

## 整体架构

```
小说 (Novel)
  ├─ Bible (世界观设定)
  │   ├─ 人物 (Characters)
  │   ├─ 地点 (Locations)
  │   ├─ 道具 (Items)
  │   ├─ 组织 (Organizations)
  │   ├─ 事件 (Events)
  │   └─ 关系 (Triples)
  │
  └─ 故事结构 (Story Structure)
      ├─ 部 (Part)
      │   ├─ 卷 (Volume)
      │   │   ├─ 幕 (Act) ──┐
      │   │   │   └─ 章节 (Chapter) ─── 关联 ──> Bible 元素
      │   │   │                         │
      │   │   │                         ├─ 出场人物
      │   │   │                         ├─ 场景地点
      │   │   │                         ├─ 使用道具
      │   │   │                         ├─ 涉及组织
      │   │   │                         └─ 关键事件
```

---

## 数据库设计

### 1. 核心表结构

#### story_nodes 表（扩展）
```sql
CREATE TABLE story_nodes (
    -- 基础字段
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    parent_id TEXT,
    node_type TEXT NOT NULL CHECK(node_type IN ('part', 'volume', 'act', 'chapter')),
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,

    -- 规划相关
    planning_status TEXT DEFAULT 'draft'
      CHECK(planning_status IN ('draft', 'ai_generated', 'user_edited', 'confirmed')),
    planning_source TEXT DEFAULT 'manual'
      CHECK(planning_source IN ('manual', 'ai_macro', 'ai_act')),

    -- 章节范围（自动计算，仅用于 part/volume/act）
    chapter_start INTEGER,
    chapter_end INTEGER,
    chapter_count INTEGER DEFAULT 0,
    suggested_chapter_count INTEGER,

    -- 章节内容（仅用于 chapter 类型）
    content TEXT,
    outline TEXT,  -- 章节大纲
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',

    -- 结构化规划信息
    themes TEXT,  -- JSON array: ["主题1", "主题2"]
    key_events TEXT,  -- JSON array: ["事件1", "事件2"]
    narrative_arc TEXT,
    conflicts TEXT,  -- JSON array: ["冲突1", "冲突2"]

    -- POV 视角（仅用于 chapter）
    pov_character_id TEXT,  -- 视角人物 ID

    -- 时间线（仅用于 chapter）
    timeline_start TEXT,  -- 开始时间（相对时间或绝对时间）
    timeline_end TEXT,    -- 结束时间

    -- 扩展元数据
    metadata TEXT DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (pov_character_id) REFERENCES characters(id) ON DELETE SET NULL
);
```

#### chapter_elements 表（新建 - 章节与 Bible 元素关联）
```sql
CREATE TABLE chapter_elements (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    element_type TEXT NOT NULL CHECK(element_type IN ('character', 'location', 'item', 'organization', 'event')),
    element_id TEXT NOT NULL,

    -- 关联类型
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'appears',      -- 出场
        'mentioned',    -- 提及
        'scene',        -- 场景
        'uses',         -- 使用（道具）
        'involved',     -- 涉及（组织）
        'occurs'        -- 发生（事件）
    )),

    -- 重要性
    importance TEXT DEFAULT 'normal' CHECK(importance IN ('major', 'normal', 'minor')),

    -- 出场顺序（同一章节内）
    appearance_order INTEGER,

    -- 备注
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chapter_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    UNIQUE(chapter_id, element_type, element_id, relation_type)
);

CREATE INDEX idx_chapter_elements_chapter ON chapter_elements(chapter_id);
CREATE INDEX idx_chapter_elements_element ON chapter_elements(element_type, element_id);
```

#### chapter_scenes 表（新建 - 章节场景分段）
```sql
CREATE TABLE chapter_scenes (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    scene_number INTEGER NOT NULL,

    -- 场景信息
    location_id TEXT,  -- 场景地点
    timeline TEXT,     -- 场景时间

    -- 场景描述
    summary TEXT,      -- 场景摘要
    purpose TEXT,      -- 场景目的（推进情节/人物发展/世界观展示）

    -- 场景内容
    content TEXT,      -- 场景正文
    word_count INTEGER DEFAULT 0,

    -- 场景中的人物
    characters TEXT,   -- JSON array: [{"id": "char-1", "role": "protagonist"}]

    order_index INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chapter_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    UNIQUE(chapter_id, scene_number)
);

CREATE INDEX idx_chapter_scenes_chapter ON chapter_scenes(chapter_id);
```

---

## 领域模型

### 1. 章节元素关联

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class ElementType(str, Enum):
    """元素类型"""
    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    ORGANIZATION = "organization"
    EVENT = "event"

class RelationType(str, Enum):
    """关联类型"""
    APPEARS = "appears"      # 出场
    MENTIONED = "mentioned"  # 提及
    SCENE = "scene"          # 场景
    USES = "uses"            # 使用（道具）
    INVOLVED = "involved"    # 涉及（组织）
    OCCURS = "occurs"        # 发生（事件）

class Importance(str, Enum):
    """重要性"""
    MAJOR = "major"    # 主要
    NORMAL = "normal"  # 普通
    MINOR = "minor"    # 次要

@dataclass
class ChapterElement:
    """章节元素关联"""
    id: str
    chapter_id: str
    element_type: ElementType
    element_id: str
    relation_type: RelationType
    importance: Importance = Importance.NORMAL
    appearance_order: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ChapterScene:
    """章节场景"""
    id: str
    chapter_id: str
    scene_number: int
    order_index: int
    location_id: Optional[str] = None
    timeline: Optional[str] = None
    summary: Optional[str] = None
    purpose: Optional[str] = None
    content: Optional[str] = None
    word_count: int = 0
    characters: List[dict] = field(default_factory=list)  # [{"id": "char-1", "role": "protagonist"}]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

### 2. 扩展 StoryNode

```python
@dataclass
class StoryNode:
    # ... 之前的字段 ...

    # POV 视角（仅用于 chapter）
    pov_character_id: Optional[str] = None

    # 时间线（仅用于 chapter）
    timeline_start: Optional[str] = None
    timeline_end: Optional[str] = None

    # 关联的元素（运行时加载，不存储在数据库）
    elements: List[ChapterElement] = field(default_factory=list, repr=False)
    scenes: List[ChapterScene] = field(default_factory=list, repr=False)

    def get_characters(self, importance: Optional[Importance] = None) -> List[str]:
        """获取章节中的人物 ID 列表"""
        chars = [e.element_id for e in self.elements
                 if e.element_type == ElementType.CHARACTER
                 and e.relation_type == RelationType.APPEARS]
        if importance:
            chars = [e.element_id for e in self.elements
                     if e.element_type == ElementType.CHARACTER
                     and e.relation_type == RelationType.APPEARS
                     and e.importance == importance]
        return chars

    def get_locations(self) -> List[str]:
        """获取章节中的地点 ID 列表"""
        return [e.element_id for e in self.elements
                if e.element_type == ElementType.LOCATION
                and e.relation_type == RelationType.SCENE]

    def get_items(self) -> List[str]:
        """获取章节中的道具 ID 列表"""
        return [e.element_id for e in self.elements
                if e.element_type == ElementType.ITEM
                and e.relation_type == RelationType.USES]
```

---

## 规划流程设计

### 阶段 1：宏观规划（Macro Planning）

**输入**：
- 小说前提（premise）
- Bible 基础信息（主角、主要地点、核心冲突）
- 目标章节数
- 结构偏好（几部几卷几幕）

**输出**：
- 部-卷-幕的完整结构
- 每个层级的标题、描述、主题
- 每个幕的关键事件、预计章节数

**AI 提示词要点**：
```
基于以下信息规划小说结构：

小说前提：{premise}
主角：{main_characters}
主要地点：{main_locations}
核心冲突：{core_conflicts}

请规划 {parts} 部，每部 {volumes} 卷，每卷 {acts} 幕。
每个幕需要包含：
1. 标题和描述
2. 主题标签
3. 关键事件
4. 预计章节数
5. 叙事弧线
6. 主要冲突
```

---

### 阶段 2：幕级规划（Act Planning）

**输入**：
- 幕的信息（标题、描述、关键事件）
- Bible 完整信息（所有人物、地点、道具等）
- 前面章节的摘要（如果有）
- 预计章节数

**输出**：
- 该幕下所有章节的列表
- 每个章节的：
  - 标题
  - 大纲
  - POV 视角人物
  - 主要出场人物
  - 场景地点
  - 使用的道具
  - 涉及的组织
  - 关键事件

**AI 提示词要点**：
```
为以下幕规划章节：

幕信息：
标题：{act_title}
描述：{act_description}
关键事件：{key_events}
预计章节数：{suggested_chapter_count}

可用的 Bible 元素：
人物：{characters}
地点：{locations}
道具：{items}
组织：{organizations}

前面章节摘要：{previous_summary}

请规划 {suggested_chapter_count} 个章节，每个章节需要包含：
1. 标题和大纲
2. POV 视角人物（从人物列表中选择）
3. 主要出场人物（标注重要性：major/normal/minor）
4. 场景地点（从地点列表中选择）
5. 使用的道具（如果有）
6. 涉及的组织（如果有）
7. 关键事件（如果有）

输出格式（JSON）：
{
  "chapters": [
    {
      "number": 1,
      "title": "章节标题",
      "outline": "章节大纲",
      "pov_character_id": "char-1",
      "elements": {
        "characters": [
          {"id": "char-1", "importance": "major", "relation": "appears"},
          {"id": "char-2", "importance": "normal", "relation": "appears"}
        ],
        "locations": [
          {"id": "loc-1", "relation": "scene"}
        ],
        "items": [
          {"id": "item-1", "relation": "uses"}
        ],
        "organizations": [
          {"id": "org-1", "relation": "involved"}
        ],
        "events": [
          {"id": "event-1", "relation": "occurs"}
        ]
      }
    }
  ]
}
```

---

### 阶段 3：章节场景规划（Scene Planning）

**输入**：
- 章节信息（标题、大纲、关联元素）
- 章节预计字数

**输出**：
- 章节内的场景分段
- 每个场景的：
  - 场景地点
  - 场景时间
  - 场景摘要
  - 场景目的
  - 场景中的人物

**AI 提示词要点**：
```
为以下章节规划场景：

章节信息：
标题：{chapter_title}
大纲：{chapter_outline}
POV 人物：{pov_character}
出场人物：{characters}
场景地点：{locations}

请将章节分为 3-5 个场景，每个场景包含：
1. 场景地点（从章节地点中选择）
2. 场景时间（相对时间）
3. 场景摘要（1-2 句话）
4. 场景目的（推进情节/人物发展/世界观展示）
5. 场景中的人物及其角色
```

---

## API 设计

### 1. 宏观规划 API

```
POST /api/v1/planning/novels/{novel_id}/macro
Request:
{
  "target_chapters": 100,
  "structure": {
    "parts": 3,
    "volumes_per_part": 3,
    "acts_per_volume": 3
  }
}

Response:
{
  "structure": [
    {
      "type": "part",
      "number": 1,
      "title": "第一部：起源",
      "description": "...",
      "themes": ["成长", "冒险"],
      "suggested_chapter_count": 30,
      "volumes": [...]
    }
  ]
}

POST /api/v1/planning/novels/{novel_id}/macro/confirm
Request: { "structure": [...] }
Response: { "created_nodes": 27 }
```

### 2. 幕级规划 API

```
POST /api/v1/planning/acts/{act_id}/chapters
Response:
{
  "chapters": [
    {
      "number": 1,
      "title": "初遇",
      "outline": "主角在酒馆遇到神秘老人...",
      "pov_character_id": "char-1",
      "elements": {
        "characters": [
          {"id": "char-1", "importance": "major", "relation": "appears"},
          {"id": "char-2", "importance": "normal", "relation": "appears"}
        ],
        "locations": [
          {"id": "loc-1", "relation": "scene"}
        ]
      }
    }
  ]
}

POST /api/v1/planning/acts/{act_id}/chapters/confirm
Request: { "chapters": [...] }
Response: { "created_chapters": 5 }
```

### 3. 章节场景规划 API

```
POST /api/v1/planning/chapters/{chapter_id}/scenes
Response:
{
  "scenes": [
    {
      "number": 1,
      "location_id": "loc-1",
      "timeline": "清晨",
      "summary": "主角在酒馆醒来",
      "purpose": "推进情节",
      "characters": [
        {"id": "char-1", "role": "protagonist"}
      ]
    }
  ]
}

POST /api/v1/planning/chapters/{chapter_id}/scenes/confirm
Request: { "scenes": [...] }
Response: { "created_scenes": 3 }
```

### 4. 章节元素管理 API

```
# 添加章节元素
POST /api/v1/chapters/{chapter_id}/elements
Request:
{
  "element_type": "character",
  "element_id": "char-1",
  "relation_type": "appears",
  "importance": "major",
  "appearance_order": 1
}

# 获取章节元素
GET /api/v1/chapters/{chapter_id}/elements?type=character

# 删除章节元素
DELETE /api/v1/chapters/{chapter_id}/elements/{element_id}

# 批量更新章节元素
PUT /api/v1/chapters/{chapter_id}/elements
Request:
{
  "elements": [
    {"element_type": "character", "element_id": "char-1", ...},
    {"element_type": "location", "element_id": "loc-1", ...}
  ]
}
```

---

## 前端交互设计

### 1. 宏观规划页面

```
┌─────────────────────────────────────────┐
│ 宏观规划                                 │
├─────────────────────────────────────────┤
│ 目标章节数: [100]                        │
│ 结构偏好:                                │
│   部数: [3]  每部卷数: [3]  每卷幕数: [3] │
│                                         │
│ [生成规划]                               │
├─────────────────────────────────────────┤
│ 第一部：起源 (30章)                      │
│   主题: 成长, 冒险                       │
│   ├─ 第一卷：觉醒 (10章)                 │
│   │   ├─ 第一幕：初遇 (3章)              │
│   │   │   关键事件: 遇到神秘老人         │
│   │   ├─ 第二幕：试炼 (4章)              │
│   │   └─ 第三幕：突破 (3章)              │
│   ├─ 第二卷：...                         │
│   └─ 第三卷：...                         │
│                                         │
│ [编辑] [确认规划]                        │
└─────────────────────────────────────────┘
```

### 2. 幕级规划对话框

```
┌─────────────────────────────────────────┐
│ 规划章节 - 第一幕：初遇                  │
├─────────────────────────────────────────┤
│ 预计章节数: 3                            │
│ [生成章节规划]                           │
├─────────────────────────────────────────┤
│ 第1章：酒馆相遇                          │
│   大纲: 主角在酒馆遇到神秘老人...        │
│   POV: [李明 ▼]                         │
│   出场人物:                              │
│     • 李明 (主要)                        │
│     • 神秘老人 (普通)                    │
│   场景地点:                              │
│     • 破旧酒馆                           │
│   使用道具:                              │
│     • 古老地图                           │
│                                         │
│ 第2章：...                               │
│                                         │
│ [编辑] [确认规划]                        │
└─────────────────────────────────────────┘
```

### 3. 章节详情页（显示关联元素）

```
┌─────────────────────────────────────────┐
│ 第1章：酒馆相遇                          │
├─────────────────────────────────────────┤
│ 大纲: 主角在酒馆遇到神秘老人...          │
│ POV: 李明                                │
│ 状态: 草稿  字数: 0                      │
├─────────────────────────────────────────┤
│ 出场人物 (2)                             │
│   🟢 李明 (主要)                         │
│   🟡 神秘老人 (普通)                     │
│   [+ 添加人物]                           │
├─────────────────────────────────────────┤
│ 场景地点 (1)                             │
│   📍 破旧酒馆                            │
│   [+ 添加地点]                           │
├─────────────────────────────────────────┤
│ 使用道具 (1)                             │
│   🎒 古老地图                            │
│   [+ 添加道具]                           │
├─────────────────────────────────────────┤
│ 场景分段 (3)                             │
│   场景1: 清晨，破旧酒馆                  │
│     主角在酒馆醒来...                    │
│   场景2: 上午，破旧酒馆                  │
│     神秘老人出现...                      │
│   场景3: 中午，破旧酒馆                  │
│     老人交给主角地图...                  │
│   [+ 添加场景]                           │
├─────────────────────────────────────────┤
│ [开始写作]                               │
└─────────────────────────────────────────┘
```

---

## 数据流转示意

```
1. 创建小说
   ↓
2. 生成 Bible（人物、地点、道具等）
   ↓
3. 宏观规划（生成部-卷-幕结构）
   ↓ (用户编辑并确认)
   ↓
4. 创建结构节点（story_nodes 表）
   ↓
5. 选择某个幕，进行幕级规划
   ↓ (AI 根据 Bible 生成章节规划)
   ↓
6. 创建章节节点 + 关联元素（chapter_elements 表）
   ↓
7. 选择某个章节，进行场景规划
   ↓ (AI 生成场景分段)
   ↓
8. 创建场景记录（chapter_scenes 表）
   ↓
9. 开始写作（基于场景大纲）
```

---

## 核心优势

### 1. 完整的关联体系
- 章节 ↔ 人物：知道每个章节有哪些人物出场
- 章节 ↔ 地点：知道每个章节发生在哪里
- 章节 ↔ 道具：知道每个章节使用了哪些道具
- 人物 ↔ 章节：反向查询，知道某个人物在哪些章节出场

### 2. 渐进式规划
- 先规划整体结构（宏观）
- 再规划具体章节（幕级）
- 最后规划场景细节（场景级）
- 每一步都可以人工调整

### 3. AI 辅助决策
- AI 根据 Bible 信息智能推荐人物、地点
- AI 根据情节需要安排道具使用
- AI 根据叙事节奏分配场景

### 4. 数据可追溯
- 每个章节的元素关联都有记录
- 可以统计人物出场频率
- 可以分析地点使用情况
- 可以检查道具伏笔是否回收

---

## 实现优先级

### Phase 1：基础架构
1. ✅ story_nodes 表已存在
2. ⬜ 添加规划相关字段到 story_nodes
3. ⬜ 创建 chapter_elements 表
4. ⬜ 创建 chapter_scenes 表
5. ⬜ 更新领域模型

### Phase 2：宏观规划
1. ⬜ 实现 MacroPlanningService
2. ⬜ 实现宏观规划 API
3. ⬜ 前端：宏观规划页面

### Phase 3：幕级规划
1. ⬜ 实现 ActPlanningService（集成 Bible）
2. ⬜ 实现幕级规划 API
3. ⬜ 前端：幕级规划对话框

### Phase 4：章节元素管理
1. ⬜ 实现 ChapterElementService
2. ⬜ 实现章节元素 API
3. ⬜ 前端：章节详情页（显示关联元素）

### Phase 5：场景规划
1. ⬜ 实现 ScenePlanningService
2. ⬜ 实现场景规划 API
3. ⬜ 前端：场景规划界面

---

## 总结

这个设计将 Bible 和故事结构完全串联起来：

1. **宏观规划**：规划整体结构框架
2. **幕级规划**：为每个幕规划章节，并关联 Bible 元素
3. **场景规划**：为每个章节规划场景细节
4. **元素追踪**：完整记录每个章节使用的人物、地点、道具等

这样用户在写作时：
- 知道这一章有哪些人物出场
- 知道场景发生在哪里
- 知道需要使用哪些道具
- 有清晰的场景分段指引

同时系统可以：
- 统计人物出场频率
- 检查伏笔是否回收
- 分析情节连贯性
- 生成章节摘要
