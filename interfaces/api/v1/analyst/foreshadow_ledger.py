"""Foreshadow Ledger API 路由"""
import re
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

from application.analyst.services.subtext_matching_service import SubtextMatchingService
from domain.novel.repositories.foreshadowing_repository import ForeshadowingRepository
from domain.novel.entities.subtext_ledger_entry import SubtextLedgerEntry
from domain.novel.value_objects.novel_id import NovelId
from domain.shared.exceptions import InvalidOperationError
from interfaces.api.dependencies import get_foreshadowing_repository


router = APIRouter(tags=["foreshadow-ledger"])


# Request Models
class CreateSubtextEntryRequest(BaseModel):
    """创建潜台词账本条目请求"""
    entry_id: str = Field(..., description="条目 ID")
    chapter: int = Field(..., ge=1, description="章节号")
    character_id: str = Field(..., description="角色 ID")
    hidden_clue: str = Field(..., min_length=1, description="隐藏线索")
    sensory_anchors: Dict[str, str] = Field(..., description="感官锚点")


class UpdateSubtextEntryRequest(BaseModel):
    """更新潜台词账本条目请求"""
    chapter: Optional[int] = Field(None, ge=1, description="章节号")
    character_id: Optional[str] = Field(None, description="角色 ID")
    hidden_clue: Optional[str] = Field(None, min_length=1, description="隐藏线索")
    sensory_anchors: Optional[Dict[str, str]] = Field(None, description="感官锚点")
    status: Optional[str] = Field(None, description="状态：pending | consumed")
    consumed_at_chapter: Optional[int] = Field(None, ge=1, description="消费章节号")


class MatchSubtextRequest(BaseModel):
    """匹配潜台词请求"""
    current_anchors: Dict[str, str] = Field(..., description="当前场景的感官锚点")


# Response Models
class SubtextEntryResponse(BaseModel):
    """潜台词账本条目响应"""
    id: str
    chapter: int
    character_id: str
    hidden_clue: str
    sensory_anchors: Dict[str, str]
    status: str
    consumed_at_chapter: Optional[int]
    suggested_resolve_chapter: Optional[int] = None  # 预期回收章节
    resolve_chapter_window: Optional[int] = None  # 宽容窗口
    importance: str = "medium"  # 重要性
    created_at: str


class MatchSubtextResponse(BaseModel):
    """匹配潜台词响应"""
    matched: bool
    entry: Optional[SubtextEntryResponse]


def _tokenize_for_overlap(text: str) -> set:
    if not text or not text.strip():
        return set()
    return set(re.findall(r"[\w\u4e00-\u9fff]+", text.lower()))


def _outline_clue_overlap_score(outline: str, clue: str) -> float:
    """词重叠启发式：与向量相似度的占位实现，后续可换 embedding。"""
    o, c = _tokenize_for_overlap(outline), _tokenize_for_overlap(clue)
    if not c:
        return 0.0
    inter = len(o & c)
    return inter / len(c)


class ChapterForeshadowSuggestionItem(BaseModel):
    entry: SubtextEntryResponse
    score: float
    reason: str


class ChapterForeshadowSuggestionsResponse(BaseModel):
    chapter_number: int
    outline_excerpt: str
    items: List[ChapterForeshadowSuggestionItem]
    note: str = "当前为词重叠启发式排序；接入向量库后将升级为语义相似度（>0.8 推送）。"


def _entry_to_response(entry: SubtextLedgerEntry) -> SubtextEntryResponse:
    """将 SubtextLedgerEntry 转换为响应模型"""
    return SubtextEntryResponse(
        id=entry.id,
        chapter=entry.chapter,
        character_id=entry.character_id,
        hidden_clue=entry.hidden_clue,
        sensory_anchors=entry.sensory_anchors,
        status=entry.status,
        consumed_at_chapter=entry.consumed_at_chapter,
        suggested_resolve_chapter=getattr(entry, 'suggested_resolve_chapter', None),
        resolve_chapter_window=getattr(entry, 'resolve_chapter_window', None),
        importance=getattr(entry, 'importance', 'medium'),
        created_at=entry.created_at.isoformat()
    )


@router.post("/novels/{novel_id}/foreshadow-ledger", response_model=SubtextEntryResponse, status_code=201)
def create_subtext_entry(
    novel_id: str = Path(..., description="小说 ID"),
    request: CreateSubtextEntryRequest = ...,
    repo: ForeshadowingRepository = Depends(get_foreshadowing_repository),
):
    """创建潜台词账本条目"""
    try:
        # 获取或创建 ForeshadowingRegistry
        registry = repo.get_by_novel_id(NovelId(novel_id))
        if not registry:
            raise HTTPException(status_code=404, detail=f"Novel {novel_id} not found")

        # 创建新条目
        entry = SubtextLedgerEntry(
            id=request.entry_id,
            chapter=request.chapter,
            character_id=request.character_id,
            hidden_clue=request.hidden_clue,
            sensory_anchors=request.sensory_anchors,
            status="pending"
        )

        # 添加到注册表
        registry.add_subtext_entry(entry)
        repo.save(registry)

        return _entry_to_response(entry)

    except InvalidOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/novels/{novel_id}/foreshadow-ledger", response_model=List[SubtextEntryResponse])
def list_subtext_entries(
    novel_id: str = Path(..., description="小说 ID"),
    status: Optional[str] = None,
    repo: ForeshadowingRepository = Depends(get_foreshadowing_repository),
):
    """列出所有伏笔账本条目（合并 foreshadowings 和 subtext_entries）"""
    try:
        registry = repo.get_by_novel_id(NovelId(novel_id))
        if not registry:
            raise HTTPException(status_code=404, detail=f"Novel {novel_id} not found")

        results = []

        # 1. 转换 foreshadowings（旧数据结构）为 SubtextEntryResponse 格式
        from domain.novel.value_objects.foreshadowing import ForeshadowingStatus
        for f in registry.foreshadowings:
            # 状态映射：planted -> pending, resolved -> consumed
            entry_status = "pending" if f.status == ForeshadowingStatus.PLANTED else "consumed"
            if status and entry_status != status:
                continue
            results.append(SubtextEntryResponse(
                id=f.id,
                chapter=f.planted_in_chapter,
                character_id="",  # 旧数据无角色 ID
                hidden_clue=f.description,
                sensory_anchors={},  # 旧数据无感官锚点
                status=entry_status,
                consumed_at_chapter=f.resolved_in_chapter,
                created_at=datetime.utcnow().isoformat(),  # 旧数据无创建时间
            ))

        # 2. 添加 subtext_entries（新数据结构）
        for e in registry.subtext_entries:
            if status and e.status != status:
                continue
            results.append(_entry_to_response(e))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/novels/{novel_id}/foreshadow-ledger/chapter-suggestions",
    response_model=ChapterForeshadowSuggestionsResponse,
)
def chapter_foreshadow_suggestions(
    novel_id: str = Path(..., description="小说 ID"),
    chapter_number: int = Query(..., ge=1, description="当前章号"),
    outline: str = Query("", description="本章大纲或要点，用于与 pending 伏笔文本比对"),
    min_score: float = Query(0.08, ge=0.0, le=1.0, description="最低重叠分"),
    limit: int = Query(12, ge=1, le=50, description="返回条数上限"),
    repo: ForeshadowingRepository = Depends(get_foreshadowing_repository),
):
    """本章建议回收：按预期回收章节临近度 + 大纲语义匹配排序。

    排序策略：
    1. 优先级1：已到期伏笔（suggested_resolve_chapter <= 当前章节）
    2. 优先级2：即将到期伏笔（suggested_resolve_chapter 在当前章节 +3 章内）
    3. 优先级3：待回收但未设置预期章节的伏笔（按词重叠分排序）
    4. 其他按（距离 - 词重叠分）综合排序
    """
    try:
        registry = repo.get_by_novel_id(NovelId(novel_id))
        if not registry:
            raise HTTPException(status_code=404, detail=f"Novel {novel_id} not found")

        # 合并 foreshadowings（旧）和 subtext_entries（新）
        all_pending: List[Tuple[str, float, int, str]] = []  # (id, score, priority, importance)
        entry_map: Dict[str, SubtextEntryResponse] = {}

        # 1. 从 foreshadowings 获取 pending 条目
        from domain.novel.value_objects.foreshadowing import ForeshadowingStatus
        for f in registry.foreshadowings:
            if f.status == ForeshadowingStatus.PLANTED:
                text = f.description
                sc = _outline_clue_overlap_score(outline, text)
                
                # 计算优先级（距离当前章节的临近度）
                if f.suggested_resolve_chapter:
                    if f.suggested_resolve_chapter <= chapter_number:
                        # 已到期，最高优先级
                        priority = 0
                    elif f.suggested_resolve_chapter <= chapter_number + 3:
                        # 即将到期（3章内），高优先级
                        priority = 1
                    else:
                        # 未到期，按距离排序（距离越小越靠前）
                        priority = 2 + (f.suggested_resolve_chapter - chapter_number)
                else:
                    # 无预期章节，默认优先级（放后面）
                    priority = 1000
                
                # 重要性加成
                importance_bonus = f.importance.value * 10  # 1-4 -> 10-40
                
                # 综合分数：优先级为主，词重叠和重要性为辅
                combined_score = -priority + sc * 100 + importance_bonus
                
                if sc >= min_score or priority <= 1:  # 已到期或即将到期的必返回
                    all_pending.append((f.id, combined_score, priority, f.importance.value))
                    entry_map[f.id] = SubtextEntryResponse(
                        id=f.id,
                        chapter=f.planted_in_chapter,
                        character_id="",
                        hidden_clue=f.description,
                        sensory_anchors={},
                        status="pending",
                        consumed_at_chapter=None,
                        created_at=datetime.utcnow().isoformat(),
                    )

        # 2. 从 subtext_entries 获取 pending 条目
        for e in registry.subtext_entries:
            if e.status == "pending":
                text = " ".join(
                    [e.hidden_clue, e.character_id, " ".join(e.sensory_anchors.values())]
                )
                sc = _outline_clue_overlap_score(outline, text)
                
                # 计算优先级
                if e.suggested_resolve_chapter:
                    if e.suggested_resolve_chapter <= chapter_number:
                        priority = 0  # 已到期
                    elif e.suggested_resolve_chapter <= chapter_number + 3:
                        priority = 1  # 即将到期
                    else:
                        priority = 2 + (e.suggested_resolve_chapter - chapter_number)
                else:
                    priority = 1000  # 无预期章节
                
                importance_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                importance_val = importance_map.get(getattr(e, 'importance', 'medium'), 2)
                importance_bonus = importance_val * 10
                
                combined_score = -priority + sc * 100 + importance_bonus
                
                if sc >= min_score or priority <= 1:
                    all_pending.append((e.id, combined_score, priority, importance_val))
                    entry_map[e.id] = _entry_to_response(e)

        # 按综合分数排序（分数越高越靠前）
        all_pending.sort(key=lambda x: x[1], reverse=True)
        top = all_pending[:limit]

        excerpt = outline.strip()
        if len(excerpt) > 200:
            excerpt = excerpt[:200] + "…"

        items = [
            ChapterForeshadowSuggestionItem(
                entry=entry_map[eid],
                score=round(sc, 4),
                reason=_build_suggestion_reason(priority, sc),
            )
            for eid, sc, priority, _ in top
        ]

        return ChapterForeshadowSuggestionsResponse(
            chapter_number=chapter_number,
            outline_excerpt=excerpt,
            items=items,
            note="排序规则：①已到期伏笔优先 ②即将到期次之 ③大纲语义匹配度 ④重要性加权",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _build_suggestion_reason(priority: int, overlap_score: float) -> str:
    """构建推荐原因说明。"""
    if priority == 0:
        return "⚠️ 已到期：预期回收章节已过，建议尽快回收"
    elif priority == 1:
        return "🔔 即将到期：预期在未来3章内回收"
    elif priority < 1000:
        return f"📋 预期在第 {priority - 1} 章后回收 · 词重叠:{overlap_score:.2f}"
    else:
        return f"📝 待回收 · 词重叠:{overlap_score:.2f}"


@router.get("/novels/{novel_id}/foreshadow-ledger/{entry_id}", response_model=SubtextEntryResponse)
def get_subtext_entry(
    novel_id: str = Path(..., description="小说 ID"),
    entry_id: str = Path(..., description="条目 ID"),
    repo: ForeshadowingRepository = Depends(get_foreshadowing_repository),
):
    """获取单个潜台词账本条目"""
    registry = repo.get_by_novel_id(NovelId(novel_id))
    if not registry:
        raise HTTPException(status_code=404, detail=f"Novel {novel_id} not found")

    entry = registry.get_subtext_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    return _entry_to_response(entry)


@router.put("/novels/{novel_id}/foreshadow-ledger/{entry_id}", response_model=SubtextEntryResponse)
def update_subtext_entry(
    novel_id: str = Path(..., description="小说 ID"),
    entry_id: str = Path(..., description="条目 ID"),
    request: UpdateSubtextEntryRequest = ...,
    repo: ForeshadowingRepository = Depends(get_foreshadowing_repository),
):
    """更新潜台词账本条目"""
    try:
        registry = repo.get_by_novel_id(NovelId(novel_id))
        if not registry:
            raise HTTPException(status_code=404, detail=f"Novel {novel_id} not found")

        entry = registry.get_subtext_entry_by_id(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

        # 构建更新后的条目（使用 dataclass replace）
        from dataclasses import replace

        updated_entry = replace(
            entry,
            chapter=request.chapter if request.chapter is not None else entry.chapter,
            character_id=request.character_id if request.character_id is not None else entry.character_id,
            hidden_clue=request.hidden_clue if request.hidden_clue is not None else entry.hidden_clue,
            sensory_anchors=request.sensory_anchors if request.sensory_anchors is not None else entry.sensory_anchors,
            status=request.status if request.status is not None else entry.status,
            consumed_at_chapter=request.consumed_at_chapter if request.consumed_at_chapter is not None else entry.consumed_at_chapter
        )

        registry.update_subtext_entry(entry_id, updated_entry)
        repo.save(registry)

        return _entry_to_response(updated_entry)

    except InvalidOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/novels/{novel_id}/foreshadow-ledger/{entry_id}", status_code=204)
def delete_subtext_entry(
    novel_id: str = Path(..., description="小说 ID"),
    entry_id: str = Path(..., description="条目 ID"),
    repo: ForeshadowingRepository = Depends(get_foreshadowing_repository),
):
    """删除潜台词账本条目"""
    try:
        registry = repo.get_by_novel_id(NovelId(novel_id))
        if not registry:
            raise HTTPException(status_code=404, detail=f"Novel {novel_id} not found")

        registry.remove_subtext_entry(entry_id)
        repo.save(registry)

    except InvalidOperationError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/novels/{novel_id}/foreshadow-ledger/match", response_model=MatchSubtextResponse)
def match_subtext_entry(
    novel_id: str = Path(..., description="小说 ID"),
    request: MatchSubtextRequest = ...,
    repo: ForeshadowingRepository = Depends(get_foreshadowing_repository),
):
    """查找匹配的潜台词账本条目"""
    try:
        registry = repo.get_by_novel_id(NovelId(novel_id))
        if not registry:
            raise HTTPException(status_code=404, detail=f"Novel {novel_id} not found")

        # 使用匹配服务查找最佳匹配
        matching_service = SubtextMatchingService()
        matched_entry = matching_service.find_best_anchor_match(
            request.current_anchors,
            registry.subtext_entries
        )

        if matched_entry:
            return MatchSubtextResponse(
                matched=True,
                entry=_entry_to_response(matched_entry)
            )
        else:
            return MatchSubtextResponse(
                matched=False,
                entry=None
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
