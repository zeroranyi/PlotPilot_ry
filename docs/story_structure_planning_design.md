# 故事结构规划功能设计

## 需求分析

### 两种规划模式

1. **宏观规划（Macro Planning）**
   - 在开始写作前规划整体结构
   - 规划层次：部（Part）→ 卷（Volume）→ 幕（Act）
   - 输出：完整的结构框架，包含每个节点的标题、描述、预计章节数
   - 特点：一次性生成整体框架，用户可调整后确认

2. **幕级规划（Act Planning）**
   - 为具体的幕规划章节内容
   - 规划层次：幕（Act）→ 章节（Chapter）
   - 输出：该幕下所有章节的标题、大纲
   - 特点：渐进式规划，每个幕单独规划

---

## 数据库设计

### 现有表结构
```sql
CREATE TABLE story_nodes (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    parent_id TEXT,
    node_type TEXT NOT NULL CHECK(node_type IN ('part', 'volume', 'act', 'chapter')),
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,

    -- 章节范围（自动计算，仅用于 part/volume/act）
    chapter_start INTEGER,
    chapter_end INTEGER,
    chapter_count INTEGER DEFAULT 0,

    -- 章节内容（仅用于 chapter 类型）
    content TEXT,
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',

    -- 元数据（JSON 格式）
    metadata TEXT DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 扩展方案：利用 metadata 字段

在 `metadata` JSON 字段中添加规划相关信息：

```json
{
  // 规划状态
  "planning_status": "draft" | "ai_generated" | "user_edited" | "confirmed",

  // 规划来源
  "planning_source": "manual" | "ai_macro" | "ai_act",

  // AI 生成的建议（宏观规划）
  "macro_plan": {
    "suggested_title": "建议的标题",
    "suggested_description": "建议的描述",
    "suggested_chapter_count": 10,
    "themes": ["主题1", "主题2"],
    "key_events": ["关键事件1", "关键事件2"]
  },

  // AI 生成的建议（幕级规划）
  "act_plan": {
    "suggested_chapters": [
      {
        "number": 1,
        "title": "章节标题",
        "outline": "章节大纲",
        "key_points": ["要点1", "要点2"]
      }
    ],
    "narrative_arc": "叙事弧线描述",
    "conflicts": ["冲突1", "冲突2"]
  },

  // 用户自定义标签
  "tags": ["标签1", "标签2"],

  // 其他扩展字段
  "custom_fields": {}
}
```

### 优势
1. **无需修改表结构**：利用现有的 metadata 字段
2. **灵活扩展**：JSON 格式可以随时添加新字段
3. **向后兼容**：不影响现有功能
4. **类型安全**：在应用层通过 Pydantic 模型验证

---

## 领域模型扩展

### 1. 规划状态枚举
```python
class PlanningStatus(str, Enum):
    """规划状态"""
    DRAFT = "draft"              # 草稿（未规划）
    AI_GENERATED = "ai_generated"  # AI 已生成
    USER_EDITED = "user_edited"    # 用户已编辑
    CONFIRMED = "confirmed"        # 已确认

class PlanningSource(str, Enum):
    """规划来源"""
    MANUAL = "manual"        # 手动创建
    AI_MACRO = "ai_macro"    # AI 宏观规划
    AI_ACT = "ai_act"        # AI 幕级规划
```

### 2. 规划元数据模型
```python
from pydantic import BaseModel
from typing import List, Optional

class MacroPlanSuggestion(BaseModel):
    """宏观规划建议"""
    suggested_title: str
    suggested_description: str
    suggested_chapter_count: int
    themes: List[str] = []
    key_events: List[str] = []

class ChapterPlanSuggestion(BaseModel):
    """章节规划建议"""
    number: int
    title: str
    outline: str
    key_points: List[str] = []

class ActPlanSuggestion(BaseModel):
    """幕级规划建议"""
    suggested_chapters: List[ChapterPlanSuggestion]
    narrative_arc: str
    conflicts: List[str] = []

class PlanningMetadata(BaseModel):
    """规划元数据"""
    planning_status: PlanningStatus = PlanningStatus.DRAFT
    planning_source: PlanningSource = PlanningSource.MANUAL
    macro_plan: Optional[MacroPlanSuggestion] = None
    act_plan: Optional[ActPlanSuggestion] = None
    tags: List[str] = []
    custom_fields: dict = {}
```

### 3. StoryNode 扩展
```python
@dataclass
class StoryNode:
    # ... 现有字段 ...
    metadata: dict = field(default_factory=dict)

    def get_planning_metadata(self) -> PlanningMetadata:
        """获取规划元数据"""
        return PlanningMetadata(**self.metadata)

    def set_planning_metadata(self, planning: PlanningMetadata):
        """设置规划元数据"""
        self.metadata = planning.dict(exclude_none=True)

    def is_planned(self) -> bool:
        """是否已规划"""
        planning = self.get_planning_metadata()
        return planning.planning_status in [
            PlanningStatus.AI_GENERATED,
            PlanningStatus.USER_EDITED,
            PlanningStatus.CONFIRMED
        ]
```

---

## API 设计

### 1. 宏观规划 API

#### 生成宏观规划
```
POST /api/v1/structure/novels/{novel_id}/macro-plan
```

请求体：
```json
{
  "premise": "小说前提",
  "target_chapters": 100,
  "structure_preference": {
    "parts": 3,
    "volumes_per_part": 3,
    "acts_per_volume": 3
  }
}
```

响应：
```json
{
  "novel_id": "novel-123",
  "structure": [
    {
      "node_type": "part",
      "number": 1,
      "title": "第一部：起源",
      "description": "描述...",
      "suggested_chapter_count": 30,
      "themes": ["主题1", "主题2"],
      "volumes": [
        {
          "node_type": "volume",
          "number": 1,
          "title": "第一卷：觉醒",
          "description": "描述...",
          "suggested_chapter_count": 10,
          "acts": [
            {
              "node_type": "act",
              "number": 1,
              "title": "第一幕：初遇",
              "description": "描述...",
              "suggested_chapter_count": 3,
              "key_events": ["事件1", "事件2"]
            }
          ]
        }
      ]
    }
  ]
}
```

#### 确认宏观规划
```
POST /api/v1/structure/novels/{novel_id}/macro-plan/confirm
```

请求体：
```json
{
  "structure": [/* 用户可能修改过的结构 */]
}
```

响应：创建的节点列表

### 2. 幕级规划 API

#### 生成幕级规划
```
POST /api/v1/structure/acts/{act_id}/plan
```

请求体：
```json
{
  "context": {
    "previous_chapters_summary": "前面章节摘要",
    "act_description": "本幕描述"
  }
}
```

响应：
```json
{
  "act_id": "act-123",
  "chapters": [
    {
      "number": 1,
      "title": "章节标题",
      "outline": "章节大纲",
      "key_points": ["要点1", "要点2"]
    }
  ],
  "narrative_arc": "叙事弧线",
  "conflicts": ["冲突1"]
}
```

#### 确认幕级规划
```
POST /api/v1/structure/acts/{act_id}/plan/confirm
```

请求体：
```json
{
  "chapters": [/* 用户可能修改过的章节列表 */]
}
```

响应：创建的章节节点列表

### 3. 查询 API

#### 获取结构树（包含规划状态）
```
GET /api/v1/structure/novels/{novel_id}/tree?include_planning=true
```

响应：
```json
{
  "novel_id": "novel-123",
  "nodes": [
    {
      "id": "part-1",
      "node_type": "part",
      "title": "第一部",
      "planning_status": "confirmed",
      "planning_source": "ai_macro",
      "children": [/* ... */]
    }
  ]
}
```

---

## 服务层设计

### 1. MacroPlanningService
```python
class MacroPlanningService:
    """宏观规划服务"""

    async def generate_macro_plan(
        self,
        novel_id: str,
        premise: str,
        target_chapters: int,
        structure_preference: dict
    ) -> dict:
        """生成宏观规划"""
        # 1. 调用 LLM 生成结构建议
        # 2. 解析为结构化数据
        # 3. 返回规划结果（不保存到数据库）
        pass

    async def confirm_macro_plan(
        self,
        novel_id: str,
        structure: dict
    ) -> List[StoryNode]:
        """确认并保存宏观规划"""
        # 1. 创建所有节点（part/volume/act）
        # 2. 设置 planning_status = confirmed
        # 3. 设置 planning_source = ai_macro
        # 4. 保存 macro_plan 建议到 metadata
        # 5. 批量保存到数据库
        pass
```

### 2. ActPlanningService
```python
class ActPlanningService:
    """幕级规划服务"""

    async def generate_act_plan(
        self,
        act_id: str,
        context: dict
    ) -> dict:
        """生成幕级规划"""
        # 1. 获取幕节点信息
        # 2. 获取上下文（前面章节、Bible 等）
        # 3. 调用 LLM 生成章节规划
        # 4. 返回规划结果（不保存到数据库）
        pass

    async def confirm_act_plan(
        self,
        act_id: str,
        chapters: List[dict]
    ) -> List[StoryNode]:
        """确认并保存幕级规划"""
        # 1. 创建所有章节节点
        # 2. 设置 planning_status = confirmed
        # 3. 设置 planning_source = ai_act
        # 4. 保存 act_plan 建议到 metadata
        # 5. 批量保存到数据库
        # 6. 更新父节点的章节范围
        pass
```

---

## LLM 提示词设计

### 1. 宏观规划提示词
```python
MACRO_PLANNING_PROMPT = """
你是一位资深的小说结构规划师。请根据以下信息为小说设计完整的结构框架。

小说前提：
{premise}

目标章节数：{target_chapters}

结构偏好：
- {parts} 部
- 每部 {volumes_per_part} 卷
- 每卷 {acts_per_volume} 幕

请设计一个完整的结构框架，包括：
1. 每个部/卷/幕的标题和描述
2. 每个层级的预计章节数
3. 每个部的主题
4. 每个幕的关键事件

输出格式（JSON）：
{
  "parts": [
    {
      "number": 1,
      "title": "第一部：标题",
      "description": "描述",
      "suggested_chapter_count": 30,
      "themes": ["主题1", "主题2"],
      "volumes": [
        {
          "number": 1,
          "title": "第一卷：标题",
          "description": "描述",
          "suggested_chapter_count": 10,
          "acts": [
            {
              "number": 1,
              "title": "第一幕：标题",
              "description": "描述",
              "suggested_chapter_count": 3,
              "key_events": ["事件1", "事件2"]
            }
          ]
        }
      ]
    }
  ]
}

只输出 JSON，不要有任何解释文字。
"""
```

### 2. 幕级规划提示词
```python
ACT_PLANNING_PROMPT = """
你是一位资深的小说章节规划师。请为以下幕规划具体的章节内容。

幕信息：
标题：{act_title}
描述：{act_description}
预计章节数：{suggested_chapter_count}

上下文：
{context}

请规划该幕的所有章节，包括：
1. 每个章节的标题
2. 每个章节的大纲（2-3 句话）
3. 每个章节的关键要点
4. 整个幕的叙事弧线
5. 主要冲突

输出格式（JSON）：
{
  "chapters": [
    {
      "number": 1,
      "title": "章节标题",
      "outline": "章节大纲",
      "key_points": ["要点1", "要点2"]
    }
  ],
  "narrative_arc": "叙事弧线描述",
  "conflicts": ["冲突1", "冲突2"]
}

只输出 JSON，不要有任何解释文字。
"""
```

---

## 前端交互流程

### 1. 宏观规划流程
```
用户进入结构规划页面
  ↓
点击"生成宏观规划"
  ↓
后端调用 LLM 生成结构建议
  ↓
前端展示树形结构（可编辑）
  ↓
用户调整标题、描述、章节数
  ↓
点击"确认规划"
  ↓
后端创建所有节点并保存
  ↓
进入工作台，显示完整结构
```

### 2. 幕级规划流程
```
用户在工作台选择某个幕
  ↓
点击"规划章节"
  ↓
后端调用 LLM 生成章节建议
  ↓
前端展示章节列表（可编辑）
  ↓
用户调整章节标题、大纲
  ↓
点击"确认规划"
  ↓
后端创建章节节点并保存
  ↓
工作台显示该幕的章节列表
```

---

## 实现优先级

### Phase 1：核心功能（MVP）
1. ✅ 数据库表已存在（story_nodes）
2. ⬜ 扩展 StoryNode 领域模型（添加规划元数据方法）
3. ⬜ 实现 MacroPlanningService（生成 + 确认）
4. ⬜ 实现宏观规划 API 端点
5. ⬜ 前端：宏观规划页面（生成 + 编辑 + 确认）

### Phase 2：幕级规划
1. ⬜ 实现 ActPlanningService（生成 + 确认）
2. ⬜ 实现幕级规划 API 端点
3. ⬜ 前端：幕级规划对话框（生成 + 编辑 + 确认）

### Phase 3：优化和扩展
1. ⬜ 支持重新生成规划
2. ⬜ 支持部分修改后重新生成
3. ⬜ 规划历史记录
4. ⬜ 规划模板功能

---

## 技术要点

### 1. 状态管理
- 使用 `planning_status` 区分节点状态
- 已确认的节点不允许删除（需要先取消确认）
- 规划状态影响 UI 显示（不同颜色/图标）

### 2. 数据一致性
- 宏观规划确认时，批量创建所有节点（事务）
- 幕级规划确认时，更新父节点的章节范围
- 删除节点时，级联删除子节点

### 3. 性能优化
- 宏观规划生成可能较慢，使用异步任务
- 前端显示加载状态和进度
- 大结构树使用虚拟滚动

### 4. 用户体验
- 生成的建议保存在 metadata 中，用户可随时查看
- 支持"恢复 AI 建议"功能
- 提供结构预览（章节数统计、分布图表）

---

## 总结

这个设计方案的核心优势：

1. **无需修改表结构**：利用现有的 metadata JSON 字段
2. **灵活扩展**：可以随时添加新的规划类型和字段
3. **向后兼容**：不影响现有的手动创建功能
4. **清晰的状态管理**：通过 planning_status 区分不同阶段
5. **渐进式实现**：可以分阶段开发，先实现宏观规划，再实现幕级规划

下一步：开始实现 Phase 1 的核心功能。
