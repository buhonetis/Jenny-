#!/usr/bin/env python3
"""Sirve la WebUI real de ARKHIVA sin arrancar el agente.

Para qué sirve: mirar cómo queda la interfaz (cascarón, mascota, temas,
tarjetas de la casa) en un navegador de escritorio, sin proveedor de modelo,
sin workspace y sin teléfono. No es el gateway: no hay agente detrás, así que
la conversación queda vacía y el socket acepta pero no responde turnos.

Lo que **sí** es real: los ficheros servidos son `arkhiva/templates/ui/`, los
mismos que empuja el APK, y `/webui/bootstrap` devuelve la forma que espera
`shared/api-client.js`. Una diferencia de aspecto aquí es una diferencia de
aspecto en el teléfono.

Uso:
    python scripts/preview_ui.py --port 8000
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import pathlib
from typing import Any

from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.http11 import Request, Response

_ROOT = pathlib.Path(__file__).resolve().parents[1] / "arkhiva" / "templates" / "ui"
_PREFIXES = ("/html-mobile/", "/html-mobile", "/")
_INDEX_FILES = ("", "index.html")


def _json(payload: Any, status: int = 200) -> Response:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = Headers()
    headers["Content-Type"] = "application/json; charset=utf-8"
    headers["Cache-Control"] = "no-store"
    headers["Content-Length"] = str(len(body))
    return Response(status, "OK", headers, body)


def _file(path: pathlib.Path) -> Response | None:
    if not path.is_file():
        return None
    body = path.read_bytes()
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype in {"application/javascript", "application/json"}:
        ctype = f"{ctype}; charset=utf-8"
    headers = Headers()
    headers["Content-Type"] = ctype
    headers["Cache-Control"] = "no-store"
    headers["Content-Length"] = str(len(body))
    return Response(200, "OK", headers, body)


def _resolve(raw: str) -> pathlib.Path | None:
    """Traduce una ruta HTTP a un fichero de `templates/ui`, sin salir de él."""
    for prefix in _PREFIXES:
        if raw == prefix or (prefix == "/html-mobile/" and raw.startswith(prefix)):
            rest = raw[len(prefix):] if prefix != "/" else raw.lstrip("/")
            break
    else:
        return None
    candidate = (_ROOT / rest).resolve()
    if candidate != _ROOT and _ROOT not in candidate.parents:
        return None
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


def _bootstrap(request: Request) -> Response:
    from arkhiva import extensions
    from arkhiva.webui import ui_version

    host = request.headers.get("Host") or "localhost"
    # Detrás del proxy del sandbox la página llega por https: un ws:// ahí lo
    # bloquea el navegador como contenido mixto, y el cascarón se queda
    # «reconectando» aunque los ficheros hayan cargado bien.
    proto = (request.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
    scheme = "wss" if proto == "https" else "ws"
    return _json(
        {
            "ws_path": "/",
            "ws_url": f"{scheme}://{host}/",
            "model_name": "ARKHIVA",
            "provider": "preview",
            "remote": False,
            "extensions": extensions.bootstrap_info(),
            "ui_version": ui_version.current(),
            "boot": ui_version.BOOT_ID,
        }
    )


def process_request(connection: Any, request: Request) -> Response | None:
    # Lo que no sea HTTP aquí es el socket de chat: None lo deja subir.
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return None

    path = request.path.split("?", 1)[0]
    if path == "/webui/bootstrap":
        return _bootstrap(request)
    if path.startswith("/api/") or path.startswith("/webui/"):
        # Ningún backend detrás: las pantallas que piden datos pintan su
        # estado vacío en lugar de quedarse girando.
        return _json({})
    target = _resolve(path)
    if target is None:
        return Response(404, "Not Found", Headers(), b"not found")
    found = _file(target)
    if found is not None:
        return found
    index = _file(_ROOT / "index.html")
    return index if index is not None else Response(404, "Not Found", Headers(), b"not found")


async def handler(connection: Any) -> None:
    """El socket de chat: acepta, escucha y no responde turnos."""
    try:
        async for _ in connection:
            pass
    except Exception:  # noqa: BLE001 - un cliente que se va no es un fallo
        pass


async def main(port: int, host: str) -> None:
    async with serve(handler, host, port, process_request=process_request) as server:
        paths = {conn.request.path for conn in server.connections}
        print(f"ARKHIVA WebUI (preview) en http://{host}:{port}/  — {_ROOT}")
        if paths:
            print(f"conexiones abiertas: {len(paths)}")
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    import asyncio

    asyncio.run(main(args.port, args.host))
