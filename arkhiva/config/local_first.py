"""Configuración de inferencia local-first de ARKHIVA.

El runtime es agnóstico de proveedor: cualquier endpoint compatible con OpenAI
Chat Completions sirve. Este módulo no cambia ese diseño; fija el **perfil por
defecto del enclave** para que configurar inferencia local sea una decisión
explícita y no una cadena de valores por defecto dispersa en la documentación.

Los valores se pueden sobrescribir por entorno sin tocar el código — útil en
CI, en pruebas de comportamiento y en el arranque por ADB:

* ``ARKHIVA_LOCAL_BASE_URL``
* ``ARKHIVA_LOCAL_MODEL``
* ``ARKHIVA_LOCAL_API_KEY``
* ``ARKHIVA_LOCAL_TIMEOUT``

Ninguno de estos valores se aplica solo: ``local_first_provider()`` devuelve la
estructura que un operador (o la pantalla de configuración) puede sembrar. Un
primer arranque que apunte en silencio a ``127.0.0.1:11434`` fallaría en
cualquier teléfono sin Ollama instalado, y ese fallo se leería como «la app no
funciona» en vez de «falta el servidor de inferencia».
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field

from arkhiva.config.runtime_env import (
    LOCAL_API_KEY_ENV,
    LOCAL_BASE_URL_ENV,
    LOCAL_MODEL_ENV,
    LOCAL_TIMEOUT_ENV,
)


@dataclass(frozen=True)
class EngineConfiguration:
    """Perfil de conexión al motor de inferencia.

    ``base_url`` incluye ``/v1/`` porque el cliente usa la ruta de Chat
    Completions de OpenAI tal cual. ``api_key`` no es un secreto en un servidor
    local (Ollama y vLLM la ignoran), pero el campo debe existir porque algunos
    gateways rechazan la petición sin cabecera ``Authorization``.
    """

    base_url: str = "http://127.0.0.1:11434/v1/"
    selected_model: str = "qwen2.5-coder:3b"
    api_key: str = field(default="NO_KEY_LOCAL", repr=False)
    timeout_seconds: int = 120
    local_fallback_enabled: bool = True

    @classmethod
    def from_env(cls) -> "EngineConfiguration":
        defaults = cls()
        return cls(
            base_url=os.environ.get(LOCAL_BASE_URL_ENV, defaults.base_url),
            selected_model=os.environ.get(LOCAL_MODEL_ENV, defaults.selected_model),
            api_key=os.environ.get(LOCAL_API_KEY_ENV, defaults.api_key),
            timeout_seconds=int(
                os.environ.get(LOCAL_TIMEOUT_ENV, defaults.timeout_seconds)
            ),
            local_fallback_enabled=defaults.local_fallback_enabled,
        )

    def as_provider(self, name: str = "local") -> dict[str, object]:
        """Estructura lista para ``providers.providers[]`` de ``config.json``."""
        data = asdict(self)
        return {
            "name": name,
            "format": "openai_compat",
            "api_base": data["base_url"],
            "api_key": data["api_key"],
        }


def local_first_provider() -> dict[str, object]:
    """Proveedor local listo para sembrar en la configuración."""
    return EngineConfiguration.from_env().as_provider()
