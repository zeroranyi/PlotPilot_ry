"""
Sandbox dialogue service for managing dialogue whitelist.
"""

from typing import Optional
from application.workbench.dtos.sandbox_dto import DialogueEntry, DialogueWhitelistResponse


class SandboxDialogueService:
    """Service for managing sandbox dialogue whitelist."""

    def __init__(self, narrative_event_repository):
        """
        Initialize the service.

        Args:
            narrative_event_repository: Repository for accessing narrative events
        """
        self.narrative_event_repository = narrative_event_repository

    def get_dialogue_whitelist(
        self,
        novel_id: str,
        chapter_number: Optional[int] = None,
        speaker: Optional[str] = None
    ) -> DialogueWhitelistResponse:
        """
        Get dialogue whitelist for sandbox simulation.

        Args:
            novel_id: Novel ID
            chapter_number: Optional chapter filter
            speaker: Optional speaker filter

        Returns:
            DialogueWhitelistResponse containing filtered dialogues
        """
        # Fetch all events up to the latest chapter
        # Using a large number to get all events
        events = self.narrative_event_repository.list_up_to_chapter(
            novel_id, max_chapter_inclusive=9999
        )

        dialogues = []

        for event in events:
            # Extract tags, handle None case
            tags = event.get("tags") or []

            # Filter events with dialogue tags（兼容 "对话:" 和旧版 "对白:"）
            dialogue_tags = [tag for tag in tags if tag.startswith("对话:") or tag.startswith("对白:")]

            if not dialogue_tags:
                continue

            # Extract speaker from tag (format: "对话:张三" or "对白:张三")
            event_speaker = dialogue_tags[0].split(":", 1)[1] if ":" in dialogue_tags[0] else ""

            # Apply chapter filter
            if chapter_number is not None and event.get("chapter_number") != chapter_number:
                continue

            # Apply speaker filter
            if speaker is not None and event_speaker != speaker:
                continue

            # Build DialogueEntry
            dialogue_entry = DialogueEntry(
                dialogue_id=event.get("event_id", ""),
                chapter=event.get("chapter_number", 0),
                speaker=event_speaker,
                content=event.get("event_summary", ""),
                context=event.get("event_summary", ""),  # Using summary as context for now
                tags=tags
            )

            dialogues.append(dialogue_entry)

        return DialogueWhitelistResponse(
            dialogues=dialogues,
            total_count=len(dialogues)
        )
