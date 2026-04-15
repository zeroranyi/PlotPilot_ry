# tests/unit/infrastructure/ai/test_qdrant_vector_store_unit.py
import pytest
from unittest.mock import Mock, MagicMock
from infrastructure.ai.qdrant_vector_store import QdrantVectorStore
from qdrant_client.models import Distance, VectorParams


@pytest.fixture
def mock_client():
    """创建 mock Qdrant 客户端"""
    return Mock()


@pytest.fixture
def vector_store(mock_client, monkeypatch):
    """创建带 mock 客户端的 VectorStore"""
    def mock_init(self, host="localhost", port=6333):
        self.client = mock_client

    monkeypatch.setattr(QdrantVectorStore, "__init__", mock_init)
    store = QdrantVectorStore()
    store.__init__()
    return store


@pytest.mark.asyncio
async def test_insert_calls_client_upsert(vector_store, mock_client):
    """测试 insert 调用客户端的 upsert 方法"""
    await vector_store.insert(
        collection="test",
        id="vec1",
        vector=[1.0, 0.0, 0.0],
        payload={"text": "test"}
    )

    assert mock_client.upsert.called
    call_args = mock_client.upsert.call_args
    assert call_args.kwargs["collection_name"] == "test"
    assert len(call_args.kwargs["points"]) == 1


@pytest.mark.asyncio
async def test_search_calls_client_search(vector_store, mock_client):
    """测试 search 调用客户端的 search 方法"""
    # Mock 返回值
    mock_result = Mock()
    mock_result.id = "vec1"
    mock_result.score = 0.95
    mock_result.payload = {"text": "test"}
    mock_client.search.return_value = [mock_result]

    results = await vector_store.search(
        collection="test",
        query_vector=[1.0, 0.0, 0.0],
        limit=5
    )

    assert mock_client.search.called
    assert len(results) == 1
    assert results[0]["id"] == "vec1"
    assert results[0]["score"] == 0.95


@pytest.mark.asyncio
async def test_delete_calls_client_delete(vector_store, mock_client):
    """测试 delete 调用客户端的 delete 方法"""
    await vector_store.delete(collection="test", id="vec1")

    assert mock_client.delete.called
    call_args = mock_client.delete.call_args
    assert call_args.kwargs["collection_name"] == "test"
    assert call_args.kwargs["points_selector"] == ["vec1"]


@pytest.mark.asyncio
async def test_create_collection_calls_client(vector_store, mock_client):
    """测试 create_collection 调用客户端方法"""
    await vector_store.create_collection(collection="test", dimension=384)

    assert mock_client.create_collection.called
    call_args = mock_client.create_collection.call_args
    assert call_args.kwargs["collection_name"] == "test"


@pytest.mark.asyncio
async def test_list_collections_returns_names(vector_store, mock_client):
    """测试 list_collections 返回集合名称列表"""
    # Mock 返回值
    mock_collection = Mock()
    mock_collection.name = "test_collection"
    mock_collections = Mock()
    mock_collections.collections = [mock_collection]
    mock_client.get_collections.return_value = mock_collections

    collections = await vector_store.list_collections()

    assert mock_client.get_collections.called
    assert collections == ["test_collection"]
