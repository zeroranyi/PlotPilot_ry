# 🎯 角色上下文调度模拟器

## 概述

这是一个交互式可视化工具，用于模拟和测试 `AppearanceScheduler` 和 `CharacterRegistry` 的角色调度算法。通过调整大纲条件和 Token 配额，实时观察系统如何决定"谁能进入最终 Prompt"。

## 访问方式

启动前端开发服务器后，访问：
```
http://localhost:5173/debug/scheduler
```

## 功能特性

### 1. 参数控制

- **大纲提及开关**：模拟章节大纲中是否提及某个角色
  - 艾达（Ada）：默认提及
  - 苏晴（Su Qing）：默认未提及

- **最大召回角色数量**：通过滑块调整（1-3）
  - 模拟 Token 预算限制
  - 默认值为 2

### 2. 角色库展示

显示三个预设角色的完整信息：

| 角色 | 重要性 | 活动度 | 心理状态 | 待机动作 |
|------|--------|--------|----------|----------|
| 林羽 | 主角 | 50 | NORMAL | 摸剑柄 |
| 艾达 | 次要角色 | 1 | 冷漠 | 擦拭机械臂 |
| 苏晴 | 主要配角 | 30 | 担忧 | 咬嘴唇 |

### 3. 调度队列

实时展示排序后的角色队列：
- ✅ **入选角色**：高亮显示，带有"✓ 入选"标记
- ❌ **超出配额**：灰色显示，带有"✗ 超出配额"标记
- 显示每个角色的排序原因（大纲提及/重要性/活动度）

### 4. 上下文生成

动态生成符合实际引擎的上下文 Prompt：
```
【角色设定约束】

角色：艾达
描述：次要角色
心理状态：冷漠
待机动作：擦拭机械臂
[连续性约束] 艾达 刚在上一章出场，需保持人设一致性。

角色：林羽
描述：主角
心理状态：NORMAL
待机动作：摸剑柄
```

### 5. 算法可视化

展示四步排序算法：
1. **第一优先级：大纲提及**
   - 大纲中提到的角色享有最高优先级
   
2. **第二优先级：角色重要性**
   - 主角 > 主要配角 > 重要配角 > 次要角色 > 背景角色
   
3. **第三优先级：活动度**
   - 出场次数越多，优先级越高
   
4. **截断策略**
   - 根据 Token 配额限制，从队列头部截取前 N 个角色

## 使用场景

### 场景 1：新角色刚登场

**设置：**
- 大纲提及艾达：✅
- 最大角色数：2

**预期结果：**
```
调度队列：
1. 艾达 (✓ 入选) - 大纲提及
2. 林羽 (✓ 入选) - 重要性: 主角
3. 苏晴 (✗ 超出配额) - 重要性: 主要配角
```

**验证点：**
- 艾达虽然是次要角色且活动度低，但因大纲提及而排名第一
- 林羽作为主角，在未提及角色中优先级最高
- 苏晴被截断，不会进入上下文

### 场景 2：常规章节（无新角色）

**设置：**
- 大纲提及艾达：❌
- 大纲提及苏晴：❌
- 最大角色数：2

**预期结果：**
```
调度队列：
1. 林羽 (✓ 入选) - 重要性: 主角
2. 苏晴 (✓ 入选) - 重要性: 主要配角
3. 艾达 (✗ 超出配额) - 重要性: 次要角色
```

**验证点：**
- 完全按重要性排序
- 活动度不影响结果（因为所有角色重要性不同）

### 场景 3：配角互动章节

**设置：**
- 大纲提及艾达：✅
- 大纲提及苏晴：✅
- 最大角色数：3

**预期结果：**
```
调度队列：
1. 艾达 (✓ 入选) - 大纲提及
2. 苏晴 (✓ 入选) - 大纲提及
3. 林羽 (✓ 入选) - 重要性: 主角
```

**验证点：**
- 两个提及的角色排在最前
- 主角虽然未提及，但仍被召回（重要性高）
- 所有角色都进入上下文

## 技术实现

### 排序算法核心代码

```typescript
const sortedQueue = computed(() => {
  const mentioned = []
  const notMentioned = []

  // 分类：提及 vs 未提及
  allCharacters.value.forEach(char => {
    if (isMentioned(char.name)) {
      mentioned.push(char)
    } else {
      notMentioned.push(char)
    }
  })

  // 对未提及的角色排序：重要性 > 活动度
  notMentioned.sort((a, b) => {
    const priorityDiff = importancePriority[a.importanceLevel] - importancePriority[b.importanceLevel]
    if (priorityDiff !== 0) return priorityDiff
    
    return b.activityCount - a.activityCount
  })

  // 合并：提及的角色 + 排序后的未提及角色
  return [...mentioned, ...notMentioned]
})
```

### 上下文生成模板

```typescript
const generatedContext = computed(() => {
  let context = '【角色设定约束】\n\n'

  selectedCharacters.value.forEach(char => {
    context += `角色：${char.name}\n`
    context += `描述：${char.importance}\n`
    context += `心理状态：${char.mentalState}\n`
    context += `待机动作：${char.idleBehavior}\n`

    // 如果角色刚登场，添加连续性约束
    if (char.activityCount <= 1) {
      context += `[连续性约束] ${char.name} 刚在上一章出场，需保持人设一致性。\n`
    }

    context += '\n'
  })

  return context
})
```

## 与实际引擎的对应关系

| 模拟器组件 | 实际代码 | 文件路径 |
|-----------|---------|---------|
| 排序算法 | `AppearanceScheduler.schedule_appearances()` | `domain/bible/services/appearance_scheduler.py` |
| 角色注册表 | `CharacterRegistry.get_characters_for_context()` | `domain/bible/entities/character_registry.py` |
| 活动度指标 | `ActivityMetrics` | `domain/bible/value_objects/activity_metrics.py` |
| 上下文生成 | `ContextBuilder.build_context()` | `application/engine/services/context_builder.py` |
| 角色锚点注入 | `BibleService.build_character_voice_anchor_section()` | `application/world/services/bible_service.py` |

## 验证要点

### ✅ 正确性验证

1. **大纲提及优先级最高**
   - 即使是次要角色，只要大纲提及，也应该排在主角之前

2. **重要性次级排序**
   - 未提及角色按：主角 > 主要配角 > 次要角色排序

3. **活动度第三级排序**
   - 同等重要性的角色，按活动度降序排列

4. **截断精准性**
   - 严格按队列顺序截断，不超过 maxCharacters

5. **连续性约束**
   - 刚登场的角色（activityCount <= 1）自动添加连续性提示

### 🎯 性能考量

- 排序算法时间复杂度：O(n log n)
- 空间复杂度：O(n)
- 响应式更新：使用 Vue 3 computed，避免不必要的重计算

## 后续扩展

### 计划中的功能

1. **关系图扩展**
   - 模拟 `RelationshipEngine` 的角色关系扩展
   - 如果选中角色A，自动召回与A关系密切的角色B

2. **动态 Token 预算**
   - 根据角色描述长度动态调整配额
   - 实现精确的 Token 估算（当前为粗略估算）

3. **历史对比**
   - 记录调度历史
   - 对比不同参数下的调度结果

4. **真实数据导入**
   - 从数据库加载真实的角色数据
   - 实时同步角色状态变化

## 相关文档

- [角色管理系统技术文档](./character-management-system.md)
- [上下文构建器设计](./context-builder-design.md)
- [AppearanceScheduler API 文档](./api/appearance-scheduler.md)

---

**开发者提示：** 这个模拟器不仅是一个可视化工具，更是一个单元测试的活文档。所有的排序逻辑都应该与 `test_appearance_scheduler.py` 中的测试用例保持一致。
