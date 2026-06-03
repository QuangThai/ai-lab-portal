from backend.app.celery_app import create_celery_app
from backend.app.settings import Settings
from backend.app.tasks import foundation_smoke


def test_celery_app_uses_redis_for_broker_and_results() -> None:
    app = create_celery_app(Settings(redis_url="redis://localhost:6379/1"))

    assert app.conf.broker_url == "redis://localhost:6379/1"
    assert app.conf.result_backend == "redis://localhost:6379/1"
    assert app.conf.task_default_queue == "ai_lab_portal"


def test_foundation_smoke_task_runs_eagerly() -> None:
    foundation_smoke.app.conf.task_always_eager = True
    foundation_smoke.app.conf.task_store_eager_result = True

    result = foundation_smoke.delay()

    assert result.get(timeout=1) == {"status": "ok", "task": "foundation.smoke"}
