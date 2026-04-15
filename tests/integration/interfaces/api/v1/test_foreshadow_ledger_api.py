# tests/integration/interfaces/api/v1/test_foreshadow_ledger_api.py
import pytest
from fastapi.testclient import TestClient

from domain.novel.value_objects.novel_id import NovelId
from interfaces.api.dependencies import get_foreshadowing_repository


class TestForeshadowLedgerAPI:
    """测试潜台词账本 API（SQLite 伏笔仓储）"""

    @pytest.fixture
    def novel_id(self):
        return "test-novel-123"

    @pytest.fixture
    def setup_registry(self, db, client, novel_id):
        """依赖 client，确保已 monkeypatch get_database，与内存库一致。"""
        db.execute(
            "INSERT OR IGNORE INTO novels (id, title, slug, target_chapters) VALUES (?, ?, ?, ?)",
            (novel_id, "Foreshadow Ledger Test", novel_id, 100),
        )
        db.get_connection().commit()

        repo = get_foreshadowing_repository()
        registry = repo.get_by_novel_id(NovelId(novel_id))
        assert registry is not None

        for e in list(registry.subtext_entries):
            try:
                registry.remove_subtext_entry(e.id)
            except Exception:
                pass
        repo.save(registry)

        yield registry

        registry = repo.get_by_novel_id(NovelId(novel_id))
        if registry:
            for e in list(registry.subtext_entries):
                try:
                    registry.remove_subtext_entry(e.id)
                except Exception:
                    pass
            repo.save(registry)

    def test_create_subtext_entry(self, client: TestClient, novel_id, setup_registry):
        response = client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-001",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "主角的秘密身份",
                "sensory_anchors": {
                    "visual": "红色围巾",
                    "auditory": "轻微的咳嗽声",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "entry-001"
        assert data["chapter"] == 5
        assert data["character_id"] == "char-001"
        assert data["hidden_clue"] == "主角的秘密身份"
        assert data["sensory_anchors"]["visual"] == "红色围巾"
        assert data["status"] == "pending"
        assert data["consumed_at_chapter"] is None

    def test_create_duplicate_entry(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-002",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "线索",
                "sensory_anchors": {"visual": "红色"},
            },
        )

        response = client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-002",
                "chapter": 6,
                "character_id": "char-002",
                "hidden_clue": "另一个线索",
                "sensory_anchors": {"visual": "蓝色"},
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_list_subtext_entries(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-003",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "线索1",
                "sensory_anchors": {"visual": "红色"},
            },
        )
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-004",
                "chapter": 6,
                "character_id": "char-002",
                "hidden_clue": "线索2",
                "sensory_anchors": {"visual": "蓝色"},
            },
        )

        response = client.get(f"/api/v1/novels/{novel_id}/foreshadow-ledger")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert any(e["id"] == "entry-003" for e in data)
        assert any(e["id"] == "entry-004" for e in data)

    def test_list_subtext_entries_by_status(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-005",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "线索",
                "sensory_anchors": {"visual": "红色"},
            },
        )

        response = client.get(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            params={"status": "pending"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(e["status"] == "pending" for e in data)

    def test_get_subtext_entry(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-006",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "线索",
                "sensory_anchors": {"visual": "红色"},
            },
        )

        response = client.get(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger/entry-006",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "entry-006"
        assert data["hidden_clue"] == "线索"

    def test_get_nonexistent_entry(self, client, novel_id, setup_registry):
        response = client.get(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger/nonexistent",
        )

        assert response.status_code == 404

    def test_update_subtext_entry(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-007",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "原始线索",
                "sensory_anchors": {"visual": "红色"},
            },
        )

        response = client.put(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger/entry-007",
            json={
                "hidden_clue": "更新后的线索",
                "status": "consumed",
                "consumed_at_chapter": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hidden_clue"] == "更新后的线索"
        assert data["status"] == "consumed"
        assert data["consumed_at_chapter"] == 10

    def test_delete_subtext_entry(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-008",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "线索",
                "sensory_anchors": {"visual": "红色"},
            },
        )

        response = client.delete(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger/entry-008",
        )

        assert response.status_code == 204

        response = client.get(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger/entry-008",
        )
        assert response.status_code == 404

    def test_match_subtext_entry(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-009",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "线索",
                "sensory_anchors": {
                    "visual": "红色围巾",
                    "auditory": "脚步声",
                },
            },
        )

        response = client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger/match",
            json={
                "current_anchors": {
                    "visual": "她戴着红色围巾走进房间",
                    "auditory": "远处传来脚步声",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is True
        assert data["entry"]["id"] == "entry-009"

    def test_match_no_result(self, client, novel_id, setup_registry):
        client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger",
            json={
                "entry_id": "entry-010",
                "chapter": 5,
                "character_id": "char-001",
                "hidden_clue": "线索",
                "sensory_anchors": {"visual": "红色围巾"},
            },
        )

        response = client.post(
            f"/api/v1/novels/{novel_id}/foreshadow-ledger/match",
            json={"current_anchors": {"visual": "蓝色帽子"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is False
        assert data["entry"] is None
