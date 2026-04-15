# 百万字全托管写作引擎 - 战役一验证原型

## 📋 文件清单

```
scripts/
├── VALIDATION_STRATEGY.md          # 👈 从这里开始！验证策略总览
├── README_PROTOTYPE.md             # 真实版原型说明
├── prototype_mock.py               # 模拟版原型（5分钟，零成本）
├── prototype_continuous_planning.py # 真实版原型（30-60分钟，需API费用）
├── run_prototype_mock.bat          # 模拟版启动脚本（推荐先跑）
└── run_prototype.bat               # 真实版启动脚本

data/prototype_results/             # 验证报告输出目录
├── mock_prototype_report_*.json    # 模拟版报告
├── prototype_report_*.json         # 真实版报告
└── prototype_novel_*.txt           # 真实版生成的完整小说
```

## 🎯 核心验证目标

### 假设 1：持续规划不会导致逻辑断裂
**问题**：写完一幕再规划下一幕，会不会导致剧情脱节？

**验证方法**：
- 生成 3 幕 × 10 章 = 30 章
- 重点检查第 10→11 章、第 20→21 章的衔接
- 看是否出现"主角刚掉悬崖，下一章在客栈喝茶"的断层

**成功标准**：
- ✅ 30 章全部生成
- ✅ 幕与幕之间逻辑连贯
- ✅ 没有明显的剧情断裂

### 假设 2：伏笔账本能自动埋设和回收
**问题**：系统能否自动检测伏笔，并在合适的章节回收？

**验证方法**：
- 模拟版：硬塞 5 个伏笔，验证回收逻辑
- 真实版：自动提取伏笔，验证回收率

**成功标准**：
- ✅ 模拟版：回收率 = 100%（硬编码）
- ✅ 真实版：回收率 >= 60%

## 🚀 快速开始

### 第一步：模拟版（推荐先跑）

**为什么先跑模拟版？**
- 零成本，不调用真实 LLM
- 5 分钟内完成
- 验证架构流程是否通顺

**运行方式**：
```bash
# Windows
双击 scripts\run_prototype_mock.bat

# Linux/Mac
python scripts/prototype_mock.py
```

**预期输出**：
```
========================================
🚀 启动全托管验证原型（模拟版）：目标 30 章
========================================

阶段 1: 建立初始宏观骨架 (Macro Plan)
  → 调用 PlanningService.generate_macro_plan()
  ✓ 宏观骨架已生成：3 幕，每幕 10 章

🎬 开始执行幕: act_001

✍️  正在生成: 第 1 章
  → 调用 ContextBuilder.build_structured_context()
  ✓ 上下文已构建: 35K tokens
  → 调用 BeatSheetService.generate()
  ✓ 节拍表已生成: 5 个动作
  → 调用 GenerationService.generate_chapter_stream()
  ✓ 正文已生成: 2500 字
  🔄 [后台] 章节 1 异步扇出开始
  ✓ [后台] 章节 1 异步扇出完成

...（重复 30 次）

========================================
验证报告
========================================

总章节数: 30
总字数: 75,000

伏笔统计:
  总埋设: 5
  已回收: 5
  待回收: 0
  回收率: 100.0%

断层检查:
  第 10 章 → 第 11 章: 幕级跨越
  第 20 章 → 第 21 章: 幕级跨越

========================================
核心验证结论
========================================
✅ 伏笔账本验证通过：回收率 >= 60%
✅ 持续规划验证通过：成功生成 30 章

架构流程验证完成！可以进入真实 LLM 测试。
```

### 第二步：真实版（模拟版通过后）

**运行方式**：
```bash
# Windows
双击 scripts\run_prototype.bat

# Linux/Mac
python scripts/prototype_continuous_planning.py
```

**预计耗时**：30-60 分钟
**预计费用**：$5-10 USD

## 📊 如何阅读验证报告

### 模拟版报告示例
```json
{
  "mode": "mock",
  "total_chapters": 30,
  "total_words": 75000,
  "foreshadowing": {
    "total_planted": 5,
    "resolved": 5,
    "pending": 0,
    "resolve_rate": "100.0%"
  },
  "pending_foreshadows": [],
  "resolved_foreshadows": [
    {
      "id": "f1",
      "chapter": 3,
      "hint": "一把刻着'林'字的断剑掉进了下水道",
      "resolve_at": 12,
      "resolved_chapter": 12
    }
  ]
}
```

### 真实版报告示例
```json
{
  "total_chapters": 30,
  "total_words": 62000,
  "acts_planned": 3,
  "foreshadowing": {
    "total_planted": 12,
    "resolved": 8,
    "pending": 4,
    "resolve_rate": "66.7%"
  },
  "chapters": [
    {
      "chapter": 1,
      "act": 1,
      "content": "...",
      "word_count": 2100,
      "outline": "..."
    }
  ]
}
```

## ✅ 成功标准

### 模拟版
- [x] 30 章全部生成
- [x] 伏笔回收率 = 100%
- [x] 没有异常或崩溃
- [x] 状态机流转正常

### 真实版
- [x] 30 章全部生成（约 6 万字）
- [x] 伏笔回收率 >= 60%
- [x] 幕与幕之间没有明显逻辑断裂
- [x] 文风基本一致

## ❌ 如果验证失败

### 模拟版失败
**说明**：架构流程有问题

**排查方向**：
1. 状态机流转逻辑
2. 幕级跨越逻辑
3. 伏笔账本数据结构

### 真实版失败：伏笔回收率 < 60%
**原因**：伏笔提取逻辑太简单（只检测关键词）

**解决方案**：
1. 在生成 Prompt 中明确要求埋设伏笔
2. 使用 LLM 提取伏笔（调用 StateExtractor）
3. 在回收时强制要求 LLM 回应伏笔

### 真实版失败：逻辑断裂
**原因**：幕与幕之间的上下文传递不足

**解决方案**：
1. 增加前情摘要的详细程度
2. 在规划下一幕时，提供更多前一幕的细节
3. 引入"幕级记忆"机制

## 🎯 下一步

### 如果两个验证都通过
进入**战役二：搭建调度中心**
- 实现状态机 (novel.stage)
- 实现 Context Assembly
- 实现异步扇出队列

### 如果验证失败
优化原型，直到通过。

## 💡 关键设计理念

### 1. 数据即真理
大模型没有记忆，所有设定必须实体化为数据库字段。

### 2. 渐进式分形生长
绝不一次性推演过多内容。按照"全书骨架 → 幕级大纲 → 章节点 → 节拍表 → 场景正文"的分形逻辑，逐层降维。

### 3. 主线冲锋，副线扇出
写作主流程必须极快（只负责写）。写完后，知识图谱推断、文风计算、伏笔更新等沉淀工作，全部扔给后台异步队列。

## 📞 需要帮助？

如果遇到问题，请检查：
1. Python 版本 >= 3.9
2. 已安装依赖：`pip install -r requirements.txt`
3. 已配置 `.env` 文件（真实版需要 ANTHROPIC_API_KEY）

---

**现在就开始**：双击 `scripts\run_prototype_mock.bat` 🚀
