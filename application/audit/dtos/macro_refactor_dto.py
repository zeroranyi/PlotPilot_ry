"""Macro Refactor DTOs"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class LogicBreakpoint:
    """逻辑断点 - 人设冲突点"""
    event_id: str
    chapter: int
    reason: str  # 冲突原因描述
    tags: List[str]  # 匹配的冲突标签


@dataclass
class BreakpointScanRequest:
    """断点扫描请求"""
    trait: str  # 目标人设标签，如 "冷酷"
    conflict_tags: Optional[List[str]] = None  # 冲突标签列表，如 ["动机:冲动"]


@dataclass
class RefactorProposalRequest:
    """重构提案请求"""
    event_id: str
    author_intent: str  # 作者意图描述
    current_event_summary: str  # 当前事件摘要
    current_tags: List[str]  # 当前标签


@dataclass
class RefactorProposal:
    """重构提案"""
    natural_language_suggestion: str  # 自然语言建议
    suggested_mutations: List[Dict[str, Any]]  # 建议的 mutations
    suggested_tags: List[str]  # 建议的新标签
    reasoning: str  # 推理过程


@dataclass
class ApplyMutationRequest:
    """应用 Mutation 请求"""
    event_id: str
    mutations: List[Dict[str, Any]]  # mutation 列表
    reason: Optional[str] = None  # 修改原因


@dataclass
class ApplyMutationResponse:
    """应用 Mutation 响应"""
    success: bool
    updated_event: Dict[str, Any]  # 更新后的事件
    applied_mutations: List[Dict[str, Any]]  # 已应用的 mutations
