import asyncio
import sys
from unittest.mock import AsyncMock, call

import pytest

from app.capabilities.profile import CapabilityProfile
from app.core.settings import settings
from app.models.ai_model import AIModel
from app.providers.lmstudio import LMStudioProvider


@pytest.fixture
def provider() -> LMStudioProvider:
    return LMStudioProvider()


@pytest.fixture(autouse=True)
def autostart_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_LM_STUDIO_AUTOSTART", True)


def test_ensure_ready_noop_when_autostart_disabled(provider, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_LM_STUDIO_AUTOSTART", False)
    probe = AsyncMock()
    run_lms = AsyncMock()
    monkeypatch.setattr(provider, "_probe_loaded_model_ids", probe)
    monkeypatch.setattr(provider, "_run_lms", run_lms)

    asyncio.run(provider._ensure_ready("some-model"))

    probe.assert_not_called()
    run_lms.assert_not_called()


def test_ensure_ready_skips_remediation_when_already_up_and_loaded(provider, monkeypatch):
    probe = AsyncMock(return_value={"model-a"})
    run_lms = AsyncMock(return_value=True)
    monkeypatch.setattr(provider, "_probe_loaded_model_ids", probe)
    monkeypatch.setattr(provider, "_run_lms", run_lms)

    asyncio.run(provider._ensure_ready("model-a"))

    run_lms.assert_not_called()
    assert probe.await_count == 2


def test_ensure_ready_starts_server_and_loads_model_when_both_needed(provider, monkeypatch):
    probe = AsyncMock(side_effect=[None, set()])
    run_lms = AsyncMock(return_value=True)
    monkeypatch.setattr(provider, "_probe_loaded_model_ids", probe)
    monkeypatch.setattr(provider, "_run_lms", run_lms)

    asyncio.run(provider._ensure_ready("model-a"))

    assert run_lms.await_args_list == [
        call("server", "start"),
        call("load", "model-a", "-y"),
    ]


def test_ensure_ready_skips_load_when_server_stays_unreachable(provider, monkeypatch):
    probe = AsyncMock(return_value=None)
    run_lms = AsyncMock(return_value=False)
    monkeypatch.setattr(provider, "_probe_loaded_model_ids", probe)
    monkeypatch.setattr(provider, "_run_lms", run_lms)

    asyncio.run(provider._ensure_ready("model-a"))

    run_lms.assert_called_once_with("server", "start")


def test_list_models_recovers_after_native_api_becomes_reachable(provider, monkeypatch):
    recovered = [
        AIModel(
            id="model-a",
            provider="lmstudio",
            profile=CapabilityProfile(
                model_id="model-a", provider="lmstudio", capabilities=[]
            ),
        )
    ]

    native = AsyncMock(side_effect=[RuntimeError("down"), recovered])
    ensure_started = AsyncMock()
    monkeypatch.setattr(provider, "_list_models_native", native)
    monkeypatch.setattr(provider, "_ensure_server_started_if_down", ensure_started)

    result = asyncio.run(provider.list_models())

    ensure_started.assert_called_once()
    assert result == recovered


def test_list_models_falls_back_when_still_unreachable_after_recovery_attempt(
    provider, monkeypatch
):
    native = AsyncMock(side_effect=RuntimeError("down"))
    ensure_started = AsyncMock()
    fallback = AsyncMock(return_value=[])
    monkeypatch.setattr(provider, "_list_models_native", native)
    monkeypatch.setattr(provider, "_ensure_server_started_if_down", ensure_started)
    monkeypatch.setattr(provider, "_list_models_fallback", fallback)

    result = asyncio.run(provider.list_models())

    ensure_started.assert_called_once()
    fallback.assert_called_once()
    assert result == []


def test_list_models_returns_empty_when_fallback_also_fails(provider, monkeypatch):
    native = AsyncMock(side_effect=RuntimeError("down"))
    ensure_started = AsyncMock()
    fallback = AsyncMock(side_effect=RuntimeError("still down"))
    monkeypatch.setattr(provider, "_list_models_native", native)
    monkeypatch.setattr(provider, "_ensure_server_started_if_down", ensure_started)
    monkeypatch.setattr(provider, "_list_models_fallback", fallback)

    result = asyncio.run(provider.list_models())

    assert result == []


def test_complete_calls_ensure_ready_before_the_request(provider, monkeypatch):
    ensure_ready = AsyncMock()
    monkeypatch.setattr(provider, "_ensure_ready", ensure_ready)

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 1, "prompt_tokens": 1},
            }

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *args, **kwargs):
            return _Response()

    monkeypatch.setattr(
        "app.providers.lmstudio.httpx.AsyncClient", lambda *a, **k: _Client()
    )

    asyncio.run(provider.complete("model-a", [{"role": "user", "content": "hi"}]))

    ensure_ready.assert_called_once_with("model-a")


def test_run_lms_returns_true_on_zero_exit(provider, monkeypatch):
    monkeypatch.setattr(settings, "LMS_CLI_PATH", sys.executable)

    result = asyncio.run(provider._run_lms("-c", "import sys; sys.exit(0)"))

    assert result is True


def test_run_lms_returns_false_on_nonzero_exit(provider, monkeypatch):
    monkeypatch.setattr(settings, "LMS_CLI_PATH", sys.executable)

    result = asyncio.run(provider._run_lms("-c", "import sys; sys.exit(1)"))

    assert result is False


def test_run_lms_returns_false_when_binary_missing(provider, monkeypatch):
    monkeypatch.setattr(settings, "LMS_CLI_PATH", "this-binary-does-not-exist-xyz")

    result = asyncio.run(provider._run_lms("server", "start"))

    assert result is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific event loop bug")
def test_run_lms_works_under_windows_selector_event_loop(provider, monkeypatch):
    """
    Regression test for a bug found in production: uvicorn's --reload
    worker runs under WindowsSelectorEventLoopPolicy, under which
    asyncio.create_subprocess_exec raises a bare NotImplementedError.
    _run_lms must keep working there since it uses subprocess.run in a
    thread instead, which doesn't depend on loop subprocess support.
    """
    monkeypatch.setattr(settings, "LMS_CLI_PATH", sys.executable)

    policy = asyncio.WindowsSelectorEventLoopPolicy()
    loop = policy.new_event_loop()
    try:
        result = loop.run_until_complete(
            provider._run_lms("-c", "import sys; sys.exit(0)")
        )
    finally:
        loop.close()

    assert result is True
