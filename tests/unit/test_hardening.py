"""Unit and integration tests for production hardening findings."""

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.llm.openai import OpenAIProvider, close_openai_clients, get_shared_openai_client
from app.main import create_app
from app.repositories.cache import (
    RedisCache,
    close_redis_client,
    get_in_memory_cache,
    get_redis_client,
)
from app.services.qualification_service import get_qualification_cache


def test_request_body_size_middleware_rejects_payload_exceeding_1mb() -> None:
    app = create_app(Settings(environment="test"))
    client = TestClient(app)

    # Payload slightly over 1 MB (1,048,577 bytes)
    over_limit_data = "a" * (1_048_577 - 20)
    json_payload = {"company": "Acme", "message": over_limit_data}

    response = client.post("/api/v1/lead/qualify", json=json_payload)

    assert response.status_code == 413
    body = response.json()
    assert body["error"]["code"] == "REQUEST_TOO_LARGE"
    assert "1 MB" in body["error"]["message"]
    assert response.headers["X-Request-ID"] == body["error"]["request_id"]


def test_in_memory_cache_singleton_lifecycle() -> None:
    cache1 = get_in_memory_cache()
    cache2 = get_in_memory_cache()

    assert cache1 is cache2

    settings = Settings(cache_enabled=True, cache_backend="memory")
    instance1 = get_qualification_cache(settings)
    instance2 = get_qualification_cache(settings)

    assert instance1 is instance2


def test_redis_client_singleton_lifecycle() -> None:
    client1 = get_redis_client("redis://localhost:6379/0")
    client2 = get_redis_client("redis://localhost:6379/0")

    assert client1 is client2

    settings = Settings(
        cache_enabled=True, cache_backend="redis", redis_url="redis://localhost:6379/0"
    )
    cache1 = get_qualification_cache(settings)
    cache2 = get_qualification_cache(settings)

    assert isinstance(cache1, RedisCache)
    assert isinstance(cache2, RedisCache)
    assert cache1._client is cache2._client


def test_async_openai_client_shared_lifecycle() -> None:
    client1 = get_shared_openai_client("sk-test-key", 20.0)
    client2 = get_shared_openai_client("sk-test-key", 20.0)

    assert client1 is client2

    provider1 = OpenAIProvider(
        Settings(OPENAI_API_KEY=SecretStr("sk-test-key"), llm_timeout_seconds=20.0)
    )
    provider2 = OpenAIProvider(
        Settings(OPENAI_API_KEY=SecretStr("sk-test-key"), llm_timeout_seconds=20.0)
    )

    assert provider1._client is provider2._client
    assert provider1._client is client1


@pytest.mark.asyncio
async def test_shutdown_cleanup_helpers() -> None:
    # Ensure close functions execute cleanly without raising errors
    await close_redis_client()
    await close_openai_clients()
