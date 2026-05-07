from application.world.services.chapter_narrative_sync import persist_bundle_triples_and_foreshadows
from domain.novel.entities.foreshadowing_registry import ForeshadowingRegistry
from domain.novel.value_objects.foreshadowing import Foreshadowing, ForeshadowingStatus, ImportanceLevel
from domain.novel.value_objects.novel_id import NovelId


class ForeshadowingRepoStub:
    def __init__(self, registry):
        self.registry = registry
        self.saved = False

    def get_by_novel_id(self, novel_id):
        return self.registry

    def save(self, registry):
        self.registry = registry
        self.saved = True


def test_persist_consumed_foreshadow_without_new_hints():
    registry = ForeshadowingRegistry("fr-1", NovelId("novel-1"))
    registry.register(
        Foreshadowing(
            id="f-1",
            planted_in_chapter=1,
            description="主角身世之谜",
            importance=ImportanceLevel.HIGH,
            status=ForeshadowingStatus.PLANTED,
        )
    )
    repo = ForeshadowingRepoStub(registry)

    persist_bundle_triples_and_foreshadows(
        "novel-1",
        5,
        {
            "relation_triples": [],
            "foreshadow_hints": [],
            "consumed_foreshadows": ["主角身世之谜"],
        },
        None,
        repo,
    )

    assert repo.saved is True
    resolved = repo.registry.get_by_id("f-1")
    assert resolved.status == ForeshadowingStatus.RESOLVED
    assert resolved.resolved_in_chapter == 5


def test_persist_skips_duplicate_unresolved_hints():
    registry = ForeshadowingRegistry("fr-1", NovelId("novel-1"))
    registry.register(
        Foreshadowing(
            id="f-1",
            planted_in_chapter=1,
            description="主角身世之谜",
            importance=ImportanceLevel.HIGH,
            status=ForeshadowingStatus.PLANTED,
        )
    )
    repo = ForeshadowingRepoStub(registry)

    persist_bundle_triples_and_foreshadows(
        "novel-1",
        2,
        {
            "relation_triples": [],
            "foreshadow_hints": [{"description": "主角身世之谜"}],
            "consumed_foreshadows": [],
        },
        None,
        repo,
    )

    assert len(repo.registry.get_unresolved()) == 1
