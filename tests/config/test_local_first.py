"""Perfil de inferencia local-first: valores por defecto y sobrescritura por entorno."""

from __future__ import annotations

import pytest

from arkhiva.config.local_first import EngineConfiguration, local_first_provider


def test_defaults_describe_a_loopback_openai_compatible_endpoint() -> None:
    cfg = EngineConfiguration()
    assert cfg.base_url == "http://127.0.0.1:11434/v1/"
    assert cfg.selected_model == "qwen2.5-coder:3b"
    assert cfg.timeout_seconds == 120
    assert cfg.local_fallback_enabled is True
    # La clave local no debe filtrarse en logs ni en reprs.
    assert cfg.api_key not in repr(cfg)


def test_provider_structure_matches_the_config_schema() -> None:
    provider = local_first_provider()
    assert provider["format"] == "openai_compat"
    assert provider["api_base"] == "http://127.0.0.1:11434/v1/"
    assert provider["name"] == "local"


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARKHIVA_LOCAL_BASE_URL", "https://10.8.0.1:11434/v1/")
    monkeypatch.setenv("ARKHIVA_LOCAL_MODEL", "qwen2.5-coder:7b")
    monkeypatch.setenv("ARKHIVA_LOCAL_API_KEY", "token-de-enclave")
    monkeypatch.setenv("ARKHIVA_LOCAL_TIMEOUT", "45")

    cfg = EngineConfiguration.from_env()

    assert cfg.base_url == "https://10.8.0.1:11434/v1/"
    assert cfg.selected_model == "qwen2.5-coder:7b"
    assert cfg.api_key == "token-de-enclave"
    assert cfg.timeout_seconds == 45
