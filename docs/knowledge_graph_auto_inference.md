# 知识图谱自动感知设计 - 基于章节关联自动生成三元组

## 核心思路

当用户在章节中关联 Bible 元素时，系统自动生成或更新三元组，构建动态知识图谱。

---

## 自动生成规则

### 1. 人物关系推断

#### 规则 1：共同出场 → 认识关系
```
IF 人物A 和 人物B 在同一章节出场
AND 两者都是 major 或 normal 重要性
THEN 生成三元组：
  (人物A, "认识", 人物B)
  confidence: 0.6
  source: "chapter-{id}"
  first_appearance: "第X章"
```

#### 规则 2：多次共同出场 → 关系强化
```
IF 人物A 和 人物B 在 N 个章节共同出场 (N >= 3)
THEN 更新三元组：
  (人物A, "熟悉", 人物B)
  confidence: 0.8
  related_chapters: ["chapter-1", "chapter-3", "chapter-5"]
```

#### 规则 3：POV 人物 + 出场人物 → 互动关系
```
IF 章节的 POV 是人物A
AND 人物B 在该章节出场（major）
THEN 生成三元组：
  (人物A, "互动", 人物B)
  confidence: 0.7
  source: "chapter-{id}"
```

### 2. 人物-地点关系

#### 规则 4：人物在地点出场
```
IF 人物A 在章节X出场
AND 章节X的场景地点是 地点L
THEN 生成三元组：
  (人物A, "到访过", 地点L)
  confidence: 0.9
  first_appearance: "第X章"
```

#### 规则 5：人物常驻地点
```
IF 人物A 在地点L出场 >= 5次
THEN 生成三元组：
  (人物A, "常驻于", 地点L)
  confidence: 0.8
  related_chapters: [...]
```

### 3. 人物-道具关系

#### 规则 6：人物使用道具
```
IF 人物A 在章节X出场
AND 章节X使用了道具I
THEN 生成三元组：
  (人物A, "使用过", 道具I)
  confidence: 0.8
  first_appearance: "第X章"
```

#### 规则 7：道具持有者推断
```
IF 人物A 在连续多个章节使用道具I
THEN 生成三元组：
  (人物A, "持有", 道具I)
  confidence: 0.7
```

### 4. 人物-组织关系

#### 规则 8：人物涉及组织
```
IF 人物A 在章节X出场
AND 章节X涉及组织O
THEN 生成三元组：
  (人物A, "与...有关", 组织O)
  confidence: 0.6
  first_appearance: "第X章"
```

### 5. 事件关系

#### 规则 9：人物参与事件
```
IF 人物A 在章节X出场
AND 章节X发生事件E
THEN 生成三元组：
  (人物A, "参与", 事件E)
  confidence: 0.9
  first_appearance: "第X章"
```

#### 规则 10：事件发生地点
```
IF 章节X发生事件E
AND 章节X的场景地点是 地点L
THEN 生成三元组：
  (事件E, "发生于", 地点L)
  confidence: 1.0
```

---

## 数据库设计扩展

### triples 表（已存在，需要扩展字段）

```sql
-- 已有字段
CREATE TABLE triples (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,

    -- 新增字段
    confidence REAL DEFAULT 1.0,  -- 置信度 (0.0-1.0)
    source_type TEXT DEFAULT 'manual' CHECK(source_type IN ('manual', 'auto_inferred', 'ai_generated')),
    source_chapter_id TEXT,  -- 来源章节
    first_appearance TEXT,  -- 首次出现（章节标题）
    related_chapters TEXT,  -- 相关章节列表（JSON array）

    -- 已有字段
    description TEXT,
    tags TEXT,
    attributes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (source_chapter_id) REFERENCES story_nodes(id) ON DELETE SET NULL,
    UNIQUE(novel_id, subject_type, subject_id, predicate, object_type, object_id)
);

CREATE INDEX idx_triples_confidence ON triples(confidence);
CREATE INDEX idx_triples_source ON triples(source_type);
CREATE INDEX idx_triples_chapter ON triples(source_chapter_id);
```

---

## 服务层设计

### KnowledgeGraphService

```python
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class TripleInferenceRule:
    """三元组推断规则"""
    name: str
    condition: callable  # 条件函数
    generator: callable  # 生成函数
    confidence: float
    priority: int  # 优先级（用于冲突解决）

class KnowledgeGraphService:
    """知识图谱服务"""

    def __init__(self, triple_repo, chapter_element_repo, story_node_repo):
        self.triple_repo = triple_repo
        self.chapter_element_repo = chapter_element_repo
        self.story_node_repo = story_node_repo
        self.rules = self._init_rules()

    def _init_rules(self) -> List[TripleInferenceRule]:
        """初始化推断规则"""
        return [
            # 规则 1：共同出场 → 认识
            TripleInferenceRule(
                name="co_appearance_acquaintance",
                condition=self._check_co_appearance,
                generator=self._generate_acquaintance_triple,
                confidence=0.6,
                priority=1
            ),
            # 规则 2：多次共同出场 → 熟悉
            TripleInferenceRule(
                name="frequent_co_appearance_familiar",
                condition=self._check_frequent_co_appearance,
                generator=self._generate_familiar_triple,
                confidence=0.8,
                priority=2
            ),
            # ... 其他规则
        ]

    async def infer_from_chapter(self, chapter_id: str) -> List[Triple]:
        """从章节推断三元组"""
        # 1. 获取章节信息
        chapter = await self.story_node_repo.get_by_id(chapter_id)

        # 2. 获取章节关联的所有元素
        elements = await self.chapter_element_repo.get_by_chapter(chapter_id)

        # 3. 应用所有推断规则
        inferred_triples = []
        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            if rule.condition(chapter, elements):
                triples = rule.generator(chapter, elements)
                inferred_triples.extend(triples)

        # 4. 去重和合并
        merged_triples = self._merge_triples(inferred_triples)

        # 5. 保存到数据库
        for triple in merged_triples:
            await self._save_or_update_triple(triple)

        return merged_triples

    async def infer_from_novel(self, novel_id: str) -> Dict[str, int]:
        """从整部小说推断三元组"""
        # 1. 获取所有章节
        chapters = await self.story_node_repo.get_chapters_by_novel(novel_id)

        # 2. 逐章推断
        stats = {
            "total_chapters": len(chapters),
            "inferred_triples": 0,
            "updated_triples": 0
        }

        for chapter in chapters:
            triples = await self.infer_from_chapter(chapter.id)
            stats["inferred_triples"] += len(triples)

        # 3. 全局推断（跨章节分析）
        global_triples = await self._infer_global_patterns(novel_id)
        stats["inferred_triples"] += len(global_triples)

        return stats

    def _check_co_appearance(self, chapter: StoryNode, elements: List[ChapterElement]) -> bool:
        """检查是否有多个人物共同出场"""
        characters = [e for e in elements
                     if e.element_type == ElementType.CHARACTER
                     and e.relation_type == RelationType.APPEARS
                     and e.importance in [Importance.MAJOR, Importance.NORMAL]]
        return len(characters) >= 2

    def _generate_acquaintance_triple(self, chapter: StoryNode, elements: List[ChapterElement]) -> List[Triple]:
        """生成认识关系三元组"""
        characters = [e for e in elements
                     if e.element_type == ElementType.CHARACTER
                     and e.relation_type == RelationType.APPEARS
                     and e.importance in [Importance.MAJOR, Importance.NORMAL]]

        triples = []
        # 两两组合
        for i, char_a in enumerate(characters):
            for char_b in characters[i+1:]:
                triple = Triple(
                    id=f"triple-{uuid.uuid4()}",
                    novel_id=chapter.novel_id,
                    subject_type="character",
                    subject_id=char_a.element_id,
                    predicate="认识",
                    object_type="character",
                    object_id=char_b.element_id,
                    confidence=0.6,
                    source_type="auto_inferred",
                    source_chapter_id=chapter.id,
                    first_appearance=chapter.title,
                    related_chapters=[chapter.id]
                )
                triples.append(triple)

        return triples

    def _check_frequent_co_appearance(self, chapter: StoryNode, elements: List[ChapterElement]) -> bool:
        """检查是否有频繁共同出场的人物"""
        # 这个需要查询历史数据
        # 在实际实现中，这个检查会在 _infer_global_patterns 中进行
        return False

    async def _infer_global_patterns(self, novel_id: str) -> List[Triple]:
        """推断全局模式（跨章节分析）"""
        triples = []

        # 1. 分析人物共同出场频率
        co_appearance_stats = await self._analyze_co_appearance(novel_id)
        for (char_a, char_b), count in co_appearance_stats.items():
            if count >= 3:
                # 升级为"熟悉"关系
                triple = await self._upgrade_relationship(
                    novel_id, char_a, char_b, "熟悉", 0.8
                )
                if triple:
                    triples.append(triple)

        # 2. 分析人物-地点频率
        location_stats = await self._analyze_character_locations(novel_id)
        for (char_id, loc_id), count in location_stats.items():
            if count >= 5:
                # 生成"常驻于"关系
                triple = Triple(
                    id=f"triple-{uuid.uuid4()}",
                    novel_id=novel_id,
                    subject_type="character",
                    subject_id=char_id,
                    predicate="常驻于",
                    object_type="location",
                    object_id=loc_id,
                    confidence=0.8,
                    source_type="auto_inferred"
                )
                triples.append(triple)

        # 3. 分析人物-道具持有关系
        item_stats = await self._analyze_character_items(novel_id)
        for (char_id, item_id), chapters in item_stats.items():
            if len(chapters) >= 3 and self._is_consecutive(chapters):
                # 生成"持有"关系
                triple = Triple(
                    id=f"triple-{uuid.uuid4()}",
                    novel_id=novel_id,
                    subject_type="character",
                    subject_id=char_id,
                    predicate="持有",
                    object_type="item",
                    object_id=item_id,
                    confidence=0.7,
                    source_type="auto_inferred",
                    related_chapters=chapters
                )
                triples.append(triple)

        return triples

    async def _analyze_co_appearance(self, novel_id: str) -> Dict[tuple, int]:
        """分析人物共同出场频率"""
        # 查询所有章节的人物关联
        query = """
        SELECT
            a.element_id as char_a,
            b.element_id as char_b,
            COUNT(DISTINCT a.chapter_id) as count
        FROM chapter_elements a
        JOIN chapter_elements b ON a.chapter_id = b.chapter_id
        JOIN story_nodes c ON a.chapter_id = c.id
        WHERE c.novel_id = ?
        AND a.element_type = 'character'
        AND b.element_type = 'character'
        AND a.element_id < b.element_id
        AND a.relation_type = 'appears'
        AND b.relation_type = 'appears'
        GROUP BY a.element_id, b.element_id
        """
        # 执行查询并返回结果
        # ...

    async def _save_or_update_triple(self, triple: Triple):
        """保存或更新三元组"""
        # 1. 检查是否已存在
        existing = await self.triple_repo.find_by_relation(
            triple.novel_id,
            triple.subject_type,
            triple.subject_id,
            triple.predicate,
            triple.object_type,
            triple.object_id
        )

        if existing:
            # 2. 如果已存在，更新相关章节列表和置信度
            if triple.source_chapter_id:
                related = json.loads(existing.related_chapters or "[]")
                if triple.source_chapter_id not in related:
                    related.append(triple.source_chapter_id)
                    existing.related_chapters = json.dumps(related)

            # 提高置信度（但不超过 1.0）
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.updated_at = datetime.now()

            await self.triple_repo.update(existing)
        else:
            # 3. 如果不存在，创建新三元组
            await self.triple_repo.save(triple)

    def _merge_triples(self, triples: List[Triple]) -> List[Triple]:
        """合并重复的三元组"""
        merged = {}
        for triple in triples:
            key = (
                triple.subject_type,
                triple.subject_id,
                triple.predicate,
                triple.object_type,
                triple.object_id
            )
            if key in merged:
                # 合并相关章节
                existing = merged[key]
                existing_chapters = json.loads(existing.related_chapters or "[]")
                new_chapters = json.loads(triple.related_chapters or "[]")
                existing.related_chapters = json.dumps(
                    list(set(existing_chapters + new_chapters))
                )
                # 取较高的置信度
                existing.confidence = max(existing.confidence, triple.confidence)
            else:
                merged[key] = triple

        return list(merged.values())
```

---

## API 设计

### 1. 手动触发推断

```
POST /api/v1/knowledge-graph/novels/{novel_id}/infer
Response:
{
  "total_chapters": 50,
  "inferred_triples": 127,
  "updated_triples": 23,
  "execution_time": 2.5
}
```

### 2. 章节级推断

```
POST /api/v1/knowledge-graph/chapters/{chapter_id}/infer
Response:
{
  "chapter_id": "chapter-1",
  "inferred_triples": 5,
  "triples": [
    {
      "subject": "李明",
      "predicate": "认识",
      "object": "神秘老人",
      "confidence": 0.6,
      "source": "auto_inferred"
    }
  ]
}
```

### 3. 查询推断的三元组

```
GET /api/v1/knowledge-graph/novels/{novel_id}/triples?source_type=auto_inferred&min_confidence=0.7

Response:
{
  "triples": [
    {
      "id": "triple-1",
      "subject": "李明",
      "predicate": "熟悉",
      "object": "神秘老人",
      "confidence": 0.8,
      "source_type": "auto_inferred",
      "related_chapters": ["第1章", "第3章", "第5章"]
    }
  ]
}
```

### 4. 确认或拒绝推断

```
POST /api/v1/knowledge-graph/triples/{triple_id}/confirm
Response: { "confirmed": true, "confidence": 1.0 }

DELETE /api/v1/knowledge-graph/triples/{triple_id}
Response: { "deleted": true }
```

---

## 前端展示

### 1. 知识图谱页面（显示推断的关系）

```
┌─────────────────────────────────────────┐
│ 知识图谱                                 │
├─────────────────────────────────────────┤
│ [手动] [AI生成] [自动推断 ✓]             │
│ 置信度: [0.7 ━━━━━━━━━━ 1.0]            │
├─────────────────────────────────────────┤
│ 李明 ──认识──> 神秘老人                  │
│   📊 置信度: 0.6                         │
│   📍 首次出现: 第1章                     │
│   [✓ 确认] [✗ 拒绝]                     │
│                                         │
│ 李明 ──熟悉──> 神秘老人                  │
│   📊 置信度: 0.8                         │
│   📍 相关章节: 第1章, 第3章, 第5章       │
│   [✓ 确认] [✗ 拒绝]                     │
│                                         │
│ 李明 ──常驻于──> 破旧酒馆                │
│   📊 置信度: 0.8                         │
│   📍 相关章节: 第1-7章                   │
│   [✓ 确认] [✗ 拒绝]                     │
└─────────────────────────────────────────┘
```

### 2. 章节详情页（显示自动推断）

```
┌─────────────────────────────────────────┐
│ 第1章：酒馆相遇                          │
├─────────────────────────────────────────┤
│ 自动推断的关系 (3)                       │
│   💡 李明 认识 神秘老人 (置信度: 0.6)    │
│   💡 李明 到访过 破旧酒馆 (置信度: 0.9)  │
│   💡 李明 使用过 古老地图 (置信度: 0.8)  │
│   [批量确认]                             │
└─────────────────────────────────────────┘
```

---

## 自动触发机制

### 触发时机

1. **章节元素添加时**
   ```python
   async def add_chapter_element(chapter_id: str, element: ChapterElement):
       # 1. 保存元素
       await chapter_element_repo.save(element)

       # 2. 触发推断
       await knowledge_graph_service.infer_from_chapter(chapter_id)
   ```

2. **章节确认规划时**
   ```python
   async def confirm_act_plan(act_id: str, chapters: List[dict]):
       # 1. 创建章节和元素
       for chapter_data in chapters:
           chapter = await create_chapter(chapter_data)
           await create_chapter_elements(chapter.id, chapter_data["elements"])

       # 2. 批量推断
       for chapter in created_chapters:
           await knowledge_graph_service.infer_from_chapter(chapter.id)
   ```

3. **用户手动触发**
   ```python
   # 用户点击"重新分析知识图谱"按钮
   await knowledge_graph_service.infer_from_novel(novel_id)
   ```

---

## 配置选项

### 用户可配置的推断规则

```python
# 在小说设置中
novel_settings = {
    "knowledge_graph": {
        "auto_infer": True,  # 是否自动推断
        "min_confidence": 0.6,  # 最低置信度阈值
        "rules": {
            "co_appearance_acquaintance": True,  # 启用共同出场推断
            "frequent_co_appearance_familiar": True,  # 启用频繁出场推断
            "character_location_residence": True,  # 启用常驻地点推断
            "character_item_possession": True,  # 启用道具持有推断
        },
        "thresholds": {
            "familiar_threshold": 3,  # 多少次共同出场算"熟悉"
            "residence_threshold": 5,  # 多少次出场算"常驻"
            "possession_threshold": 3,  # 多少次使用算"持有"
        }
    }
}
```

---

## 总结

### 核心优势

1. **自动化**：章节关联元素后，自动推断三元组
2. **可追溯**：每个推断都记录来源章节和置信度
3. **可验证**：用户可以确认或拒绝推断结果
4. **动态更新**：随着章节增加，关系自动强化
5. **全局分析**：跨章节分析，发现深层模式

### 实现优先级

1. ✅ triples 表已存在
2. ⬜ 扩展 triples 表（添加 confidence、source_type 等字段）
3. ⬜ 实现 KnowledgeGraphService
4. ⬜ 实现推断规则引擎
5. ⬜ 集成到章节元素添加流程
6. ⬜ 前端展示推断结果

这样，知识图谱就能"感知"到章节中的关系，并自动构建和更新！
