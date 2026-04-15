# 智能检索与上下文管理系统设计 - 技术实现部分

## 技术实现要点

### 后端架构

#### 1. 场记智能体服务

**技术栈：**
- 轻量级 LLM：Claude Haiku / GPT-4o-mini
- 异步任务队列：Celery / Redis
- 防抖触发：前端 debounce（2 秒）+ 后端任务调度

**API 设计：**

```python
POST /api/v1/novels/{slug}/scene-director/analyze
Request:
{
  "chapter_number": 52,
  "outline": "李明被激怒，拔出了腰间的武器..."
}

Response:
{
  "characters": ["李明", "王总"],
  "locations": ["废弃工厂"],
  "action_types": ["combat"],
  "trigger_keywords": ["武器", "战斗技能"],
  "emotional_state": "tense",
  "pov": "李明"
}
```

#### 2. 事件流溯源存储

**数据库设计：**

```sql
-- 静态基座
CREATE TABLE entity_base (
  id VARCHAR(64) PRIMARY KEY,
  novel_id VARCHAR(64) NOT NULL,
  entity_type VARCHAR(32), -- character, location, item
  name VARCHAR(255),
  core_attributes JSONB,
  created_at TIMESTAMP,
  INDEX idx_novel_entity (novel_id, entity_type)
);

-- 演化事件流
CREATE TABLE narrative_events (
  event_id VARCHAR(64) PRIMARY KEY,
  novel_id VARCHAR(64) NOT NULL,
  chapter_number INT,
  event_summary TEXT,
  mutations JSONB,
  timestamp TIMESTAMP,
  INDEX idx_novel_chapter (novel_id, chapter_number)
);
```

**时间线查询实现：**

```python
def get_entity_state_at_chapter(entity_id: str, chapter: int):
    # 1. 获取静态基座
    base = db.query(EntityBase).filter_by(id=entity_id).first()

    # 2. 获取该章节之前的所有事件
    events = db.query(NarrativeEvents).filter(
        NarrativeEvents.novel_id == base.novel_id,
        NarrativeEvents.chapter_number <= chapter
    ).order_by(NarrativeEvents.chapter_number).all()

    # 3. 重放事件流（Apply mutations）
    state = base.core_attributes.copy()
    for event in events:
        for mutation in event.mutations:
            if mutation['action'] == 'add':
                state[mutation['attribute']] = mutation['value']
            elif mutation['action'] == 'remove':
                state.pop(mutation['attribute'], None)

    return state
```

#### 3. 知识图谱召回

**向量存储：**
- Qdrant（已集成）
- Embedding 模型：text-embedding-3-small

**召回 API：**

```python
POST /api/v1/novels/{slug}/context/retrieve
Request:
{
  "chapter_number": 52,
  "outline": "...",
  "scene_director_result": {...},
  "max_tokens": 35000
}

Response:
{
  "layer1": {
    "novel_metadata": {...},
    "current_chapter": {...},
    "plot_arc": {...},
    "active_storylines": [...]
  },
  "layer2": {
    "characters": [...],
    "locations": [...],
    "triggered_settings": [...],
    "related_chapters": [...]
  },
  "layer3": {
    "recent_chapters": [...],
    "recent_activities": [...],
    "pending_foreshadows": [...]
  },
  "token_usage": {
    "layer1": 4800,
    "layer2": 19200,
    "layer3": 9500,
    "total": 33500
  }
}
```

#### 4. 冲突检测与批注

```python
def detect_conflicts(outline: str, scene_director_result: dict, entity_states: dict):
    conflicts = []

    # 检测设定冲突
    for entity_id, current_state in entity_states.items():
        # 从大纲中提取该实体的行为
        actions = extract_entity_actions(outline, entity_id)

        for action in actions:
            # 检查行为是否与当前状态冲突
            if is_conflicting(action, current_state):
                conflicts.append({
                    "type": "setting_conflict",
                    "entity": entity_id,
                    "expected": current_state,
                    "actual": action,
                    "severity": "warning"
                })

    return conflicts
```

#### 5. 伏笔账本管理

```sql
CREATE TABLE foreshadow_ledger (
  id VARCHAR(64) PRIMARY KEY,
  novel_id VARCHAR(64) NOT NULL,
  chapter_number INT,
  character_id VARCHAR(64),
  hidden_clue VARCHAR(255),
  sensory_anchors JSONB,
  generated_text TEXT,
  status VARCHAR(32), -- pending, consumed
  consumed_at_chapter INT,
  INDEX idx_novel_status (novel_id, status)
);
```

#### 6. 文风金库

```sql
CREATE TABLE voice_vault (
  id VARCHAR(64) PRIMARY KEY,
  author_id VARCHAR(64) NOT NULL,
  sample_id VARCHAR(64),
  chapter_number INT,
  scene_type VARCHAR(32),
  ai_original TEXT,
  author_refined TEXT,
  diff_analysis JSONB,
  created_at TIMESTAMP,
  INDEX idx_author (author_id)
);

CREATE TABLE voice_fingerprint (
  author_id VARCHAR(64) PRIMARY KEY,
  fingerprint JSONB,
  version INT,
  last_updated TIMESTAMP
);
```

---

## 用户体验流程

### 场景 1：章节生成（智能检索）

**用户操作流程：**

1. 用户在大纲编辑器中输入第 52 章大纲
2. 停止输入 2 秒后，后台自动调用场记智能体（用户无感知）
3. 用户点击"生成正文"按钮
4. 系统立即返回生成结果（体感延迟 0）
5. 如果检测到冲突，侧边栏显示幽灵批注（非侵入式）
6. 用户阅读正文，满意后点击"保存"
7. 如果有批注，用户可选择处理或忽略

**系统后台流程：**

```
用户输入大纲
    ↓
防抖触发（2秒）
    ↓
场记智能体分析（异步）
    ↓
知识图谱召回（基于场记结果）
    ↓
Token 预算截断
    ↓
缓存上下文
    ↓
用户点击"生成"
    ↓
主力模型生成（使用缓存的上下文）
    ↓
冲突检测
    ↓
文风过滤
    ↓
返回正文 + 批注（如有）
```

### 场景 2：手动查找（用户检索）

**用户操作流程：**

1. 用户在知识面板输入"李明"
2. 系统返回人物卡片：
   - 基本信息（性格、装备）
   - 出场章节（1, 2, 3, 5, 7...）
   - 关系网络（师徒→柳月，朋友→张三）
   - 相关事件（拜师、突破、觉醒火系）
3. 用户点击"查看关系图"，跳转到人物关系图页面
4. 用户点击"引用到输入框"，将人物描述插入到大纲编辑器

### 场景 3：全局大修（事件流重组）

**用户操作流程：**

1. 用户在设定面板将"男主性格"从"热血"改为"冷酷"
2. 系统扫描事件流，生成"逻辑断点拓扑图"
3. 系统弹出对话框，逐个询问如何处理冲突事件
4. 用户确认修改方案
5. 系统修改事件流，局部重渲染正文
6. 用户进入沙盘试读模式：
   - 查看"角色音轨切片"（50 句对白 + 20 个动作）
   - 查看"叙事心电图"，发现第 45 章异常
   - 点击异常节点，下潜到该章进行微调
7. 用户满意后，点击"合并至主时间线"
8. 系统归档旧版，应用新版

### 场景 4：卡文破局（张力弹弓）

**用户操作流程：**

1. 用户面对空白文档，点击"卡文破局"工具
2. 系统提示："描述一个最具画面感的瞬间"
3. 用户输入："大雪天，主角跪在地上，亲手斩下了恩师的头颅"
4. 系统生成 3 个"What If"变异
5. 用户选择"变异 2：恩师的血是瘟疫解药"
6. 系统倒推 3 个历史事件骨架
7. 用户基于骨架，开始填充细节

---

## 总结

这套**智能检索与上下文管理系统**的核心价值在于：

1. **信息降噪：** 不是给 AI"全部家当"，而是构建"单章执行简报"
2. **事件驱动：** 通过事件流溯源，保留因果关系，实现设定的血肉丰满
3. **精准召回：** 混合规则筛选 + 图谱遍历 + 向量搜索，只召回本章需要的设定
4. **冲突处理：** 大纲绝对意志 + 异步后置审查，不打断创作心流
5. **伏笔管理：** 感官锚点共振 + 一击致命法则，实现文学级的瞬间击穿
6. **防同化：** 文风金库 + 指纹对抗，保护作者的独特笔触
7. **全局大修：** 事件流基因重组，将"几十万字文本大修"变成"几十个事件审核"
8. **卡文破局：** 张力弹弓 + 叙事熵检测，在思维枯竭和结构疲软处注入变量

这套系统将 AI 定位为**"场记与剧务"**，而非"联合编剧"，真正实现了**作者主权**。

---

**设计完成日期：** 2026-04-05
**下一步：** 进入实现计划阶段
