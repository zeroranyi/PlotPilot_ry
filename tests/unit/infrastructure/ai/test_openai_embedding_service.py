"""OpenAIEmbeddingService 测试"""
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
from infrastructure.ai.openai_embedding_service import OpenAIEmbeddingService


class TestOpenAIEmbeddingService:
    """OpenAIEmbeddingService 测试"""

    @pytest.fixture
    def service(self):
        """创建 service 实例"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
            service = OpenAIEmbeddingService()
            yield service

    def test_initialization(self, service):
        """测试初始化"""
        assert service.client is not None
        assert service.model == "text-embedding-3-small"

    def test_get_dimension(self, service):
        """测试获取向量维度"""
        assert service.get_dimension() == 1536

    @pytest.mark.asyncio
    async def test_embed_single_text(self, service):
        """测试单个文本嵌入"""
        text = "Hello, world!"

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]

        with patch.object(service.client.embeddings, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await service.embed(text)

            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)
            assert result[0] == 0.1

            mock_create.assert_called_once_with(
                model="text-embedding-3-small",
                input=text
            )

    @pytest.mark.asyncio
    async def test_embed_batch(self, service):
        """测试批量文本嵌入"""
        texts = ["Hello", "World", "Test"]

        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536),
            Mock(embedding=[0.3] * 1536)
        ]

        with patch.object(service.client.embeddings, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await service.embed_batch(texts)

            assert len(result) == 3
            assert all(len(embedding) == 1536 for embedding in result)
            assert result[0][0] == 0.1
            assert result[1][0] == 0.2
            assert result[2][0] == 0.3

            mock_create.assert_called_once_with(
                model="text-embedding-3-small",
                input=texts
            )

    @pytest.mark.asyncio
    async def test_embed_empty_text(self, service):
        """测试空文本嵌入"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await service.embed("")

    @pytest.mark.asyncio
    async def test_embed_batch_empty_list(self, service):
        """测试空列表批量嵌入"""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            await service.embed_batch([])

    @pytest.mark.asyncio
    async def test_embed_batch_with_empty_text(self, service):
        """测试包含空文本的批量嵌入"""
        texts = ["Hello", "", "World"]

        with pytest.raises(ValueError, match="All texts must be non-empty"):
            await service.embed_batch(texts)

    @pytest.mark.asyncio
    async def test_embed_api_error(self, service):
        """测试 API 错误处理"""
        text = "Hello"

        with patch.object(service.client.embeddings, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("OpenAI API Error")

            with pytest.raises(RuntimeError, match="Failed to generate embedding"):
                await service.embed(text)

    def test_missing_api_key(self):
        """测试缺少 API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                OpenAIEmbeddingService()


@pytest.mark.skipif(
    os.getenv("OPENAI_API_KEY") is None,
    reason="OPENAI_API_KEY not set"
)
class TestOpenAIEmbeddingServiceIntegration:
    """OpenAIEmbeddingService 集成测试（需要真实 API key）"""

    @pytest.fixture
    def service(self):
        """创建真实 service 实例"""
        return OpenAIEmbeddingService()

    @pytest.mark.asyncio
    async def test_real_embed_single(self, service):
        """测试真实单个文本嵌入"""
        text = "This is a test sentence."
        result = await service.embed(text)

        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_real_embed_batch(self, service):
        """测试真实批量文本嵌入"""
        texts = ["First sentence.", "Second sentence.", "Third sentence."]
        result = await service.embed_batch(texts)

        assert len(result) == 3
        assert all(len(embedding) == 1536 for embedding in result)
        assert all(isinstance(x, float) for embedding in result for x in embedding)

    @pytest.mark.asyncio
    async def test_real_dimension(self, service):
        """测试真实维度"""
        assert service.get_dimension() == 1536
