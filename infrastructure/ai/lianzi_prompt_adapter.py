import logging
import re
from typing import Any, Dict, Optional

from domain.ai.value_objects.prompt import Prompt

logger = logging.getLogger(__name__)

LIANZI_OFFICIAL_PROMPTS = {
    "worldbuilding": "lzgf-cml4lxlg20a6d25sad46lb0o3",
    "macro_outline": "lzgf-cmj55agx200011368xh3u7mwv",
    "volume_outline": "lzgf-cmnkbg3u50xjzi4v6pg812xj3",
    "chapter_outline": "lzgf-cmj55agxr00051368t7gip8q4",
    "chapter_generation": "lzgf-cmj55agy4000713685lf4wgep",
    "review": "lzgf-cml7g1yis0v4b5dju8vi53ola",
    "polishing": "lzgf-cmj6t0h2e003kkmuymccadv6w",
    "style": "lzgf-cml99t1w70056gvwe48v1w5dm",
    "state_update": "lzgf-cmldq5saw0njb68j8sarph6e8",
}

_PLACEHOLDER_RE = re.compile(r"[@＠]([一-鿿A-Za-z0-9_\-]{1,30})")


def render_lianzi_prompt_template(template: str, variables: Dict[str, Any]) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1)
        return str(variables.get(key, match.group(0)) or "")

    return _PLACEHOLDER_RE.sub(replace, template or "")


def build_prompt_from_lianzi_node(
    node_key: str,
    variables: Dict[str, Any],
    *,
    fallback_system: str = "你是专业网络小说创作助手，请严格按要求输出。",
    suffix: str = "",
) -> Optional[Prompt]:
    try:
        from infrastructure.ai.prompt_manager import get_prompt_manager

        manager = get_prompt_manager()
        manager.ensure_seeded()
        node = manager.get_node(node_key, by_key=True)
        if not node:
            logger.warning("炼字工坊提示词不存在，回退内置模板: %s", node_key)
            return None
        detail = node.to_detail_dict()
        template = detail.get("user_template", "")
        if not template.strip():
            logger.warning("炼字工坊提示词为空，回退内置模板: %s", node_key)
            return None
        rendered = render_lianzi_prompt_template(template, variables).strip()
        if suffix:
            rendered = f"{rendered}\n\n{suffix.strip()}" if rendered else suffix.strip()
        system = detail.get("system", "") or fallback_system
        logger.info("使用炼字工坊官方提示词: %s / %s", node_key, detail.get("name", ""))
        return Prompt(system=system, user=rendered)
    except Exception as exc:
        logger.warning("炼字工坊提示词渲染失败，回退内置模板: %s", exc)
        return None
