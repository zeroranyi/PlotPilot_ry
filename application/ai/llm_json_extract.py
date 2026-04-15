"""从 LLM 文本中抽取 JSON 对象（去 fence、截最外层 {{…}}），供各契约模块复用。"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple


def strip_json_fences(raw: str) -> str:
    """去掉 ``` / ```json 代码块包装。"""
    content = raw.strip()
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0]
    return content.strip()


def extract_outer_json_object(text: str) -> str:
    """取第一个 '{' 与最后一个 '}' 之间的片段，容忍前后废话。"""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]


def parse_llm_json_to_dict(raw: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """解析为 dict。成功 (data, [])；失败 (None, [错误信息…])。"""
    try:
        cleaned = strip_json_fences(raw)
        cleaned = extract_outer_json_object(cleaned)
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, [f"JSON 解析失败: {e}"]
    except Exception as e:  # pragma: no cover
        return None, [f"预处理失败: {e}"]

    if not isinstance(data, dict):
        return None, ["根节点必须是 JSON 对象"]
    return data, []
