# tests/integration/infrastructure/ai/test_qdrant_vector_store.py
import pytest
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from infrastructure.ai.qdrant_vector_store import QdrantVectorStore


@pytest.fixture
def qdrant_available():
    """检查 Qdrant 是否可用"""
    try:
        client = QdrantClient(host="localhost", port=6333, timeout=2)
        client.get_collections()
        return True
    except Exception:
        return False


@pytest.fixture
async def vector_store(qdrant_available):
    """创建 VectorStore 实例"""
    if not qdrant_available:
        pytest.skip("Qdrant is not running")

    store = QdrantVectorStore(host="localhost", port=6333)

    # 清理测试集合
    try:
        await store.delete_collection("test_collection")
    except Exception:
        pass

    yield store

    # 清理
    try:
        await store.delete_collection("test_collection")
    except Exception:
        pass


@pytest.mark.asyncio
async def test_create_collection(vector_store):
    """测试创建集合"""
    await vector_store.create_collection("test_collection", dimension=384)

    # 验证集合已创建
    collections = await vector_store.list_collections()
    assert "test_collection" in collections


@pytest.mark.asyncio
async def test_insert_and_search(vector_store):
    """测试插入和搜索向量"""
    # 创建集合
    await vector_store.create_collection("test_collection", dimension=3)

    # 插入向量
    vector1 = [1.0, 0.0, 0.0]
    vector2 = [0.0, 1.0, 0.0]
    vector3 = [0.9, 0.1, 0.0]

    await vector_store.insert(
        collection="test_collection",
        id="vec1",
        vector=vector1,
        payload={"text": "first vector"}
    )

    await vector_store.insert(
        collection="test_collection",
        id="vec2",
        vector=vector2,
        payload={"text": "second vector"}
    )

    await vector_store.insert(
        collection="test_collection",
        id="vec3",
        vector=vector3,
        payload={"text": "third vector"}
    )

    # 搜索相似向量
    results = await vector_store.search(
        collection="test_collection",
        query_vector=[1.0, 0.0, 0.0],
        limit=2
    )

    # 验证结果
    assert len(results) == 2
    assert results[0]["id"] == "vec1"
    assert results[0]["payload"]["text"] == "first vector"
    assert results[1]["id"] == "vec3"
    assert results[1]["payload"]["text"] == "third vector"


@pytest.mark.asyncio
async def test_delete(vector_store):
    """测试删除向量"""
    # 创建集合并插入向量
    await vector_store.create_collection("test_collection", dimension=3)

    await vector_store.insert(
        collection="test_collection",
        id="vec1",
        vector=[1.0, 0.0, 0.0],
        payload={"text": "test"}
    )

    # 删除向量
    await vector_store.delete(collection="test_collection", id="vec1")

    # 验证已删除
    results = await vector_store.search(
        collection="test_collection",
        query_vector=[1.0, 0.0, 0.0],
        limit=1
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_error_handling_collection_not_found(vector_store):
    """测试集合不存在时的错误处理"""
    with pytest.raises(Exception):
        await vector_store.insert(
            collection="nonexistent_collection",
            id="vec1",
            vector=[1.0, 0.0, 0.0],
            payload={}
        )


@pytest.mark.asyncio
async def test_error_handling_dimension_mismatch(vector_store):
    """测试维度不匹配时的错误处理"""
    await vector_store.create_collection("test_collection", dimension=3)

    with pytest.raises(Exception):
        await vector_store.insert(
            collection="test_collection",
            id="vec1",
            vector=[1.0, 0.0],  # 维度不匹配
            payload={}
        )
