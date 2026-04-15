"""测试依赖注入配置"""
import os
import pytest
from unittest.mock import patch, MagicMock
from interfaces.api.dependencies import get_vector_store


class TestGetVectorStore:
    """测试 get_vector_store 依赖注入函数"""

    def test_get_vector_store_returns_none_when_no_env(self):
        """未设置环境变量时返回 None"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_vector_store()
            assert result is None

    def test_get_vector_store_returns_none_when_disabled(self):
        """QDRANT_ENABLED 为 false 时返回 None"""
        with patch.dict(os.environ, {"QDRANT_ENABLED": "false"}, clear=True):
            result = get_vector_store()
            assert result is None

    def test_get_vector_store_returns_qdrant_when_env_set(self):
        """设置环境变量时返回 QdrantVectorStore 实例"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333"
        }, clear=True):
            # Mock QdrantVectorStore to avoid actual connection
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                # 验证返回了实例
                assert result is mock_instance
                # 验证使用正确的参数初始化
                mock_qdrant.assert_called_once_with(
                    host="localhost",
                    port=6333,
                    api_key=None
                )

    def test_get_vector_store_with_custom_host_port(self):
        """使用自定义 host 和 port"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true",
            "QDRANT_HOST": "qdrant.example.com",
            "QDRANT_PORT": "6334"
        }, clear=True):
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                mock_qdrant.assert_called_once_with(
                    host="qdrant.example.com",
                    port=6334,
                    api_key=None
                )

    def test_get_vector_store_with_api_key(self):
        """使用 API key"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333",
            "QDRANT_API_KEY": "test-api-key"
        }, clear=True):
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                mock_qdrant.assert_called_once_with(
                    host="localhost",
                    port=6333,
                    api_key="test-api-key"
                )

    def test_get_vector_store_uses_default_values(self):
        """只设置 QDRANT_ENABLED，使用默认值"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true"
        }, clear=True):
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                # 验证使用默认值
                mock_qdrant.assert_called_once_with(
                    host="localhost",
                    port=6333,
                    api_key=None
                )
