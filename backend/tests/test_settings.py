import pytest
from pydantic import ValidationError

from backend.app.settings import Settings


def test_settings_use_safe_defaults_for_test_environment() -> None:
    settings = Settings(environment="test")

    assert settings.app_name == "AI Lab Portal API"
    assert settings.service_name == "ai-lab-portal-api"
    assert settings.environment == "test"
    assert str(settings.database_url).startswith("postgresql+psycopg://")
    assert str(settings.redis_url).startswith("redis://")


def test_settings_reject_blank_environment() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="")


def test_settings_reject_non_postgres_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="sqlite:///local.db")


def test_settings_reject_non_redis_url() -> None:
    with pytest.raises(ValidationError):
        Settings(redis_url="http://localhost:6379/0")
