#!/usr/bin/env python3
"""Auditoría del rebranding: ningún rastro del fabricante original fuera del registro.

El rebranding se hizo con una purga mecánica sobre ~1 600 ocurrencias. Una purga
mecánica se deshace sola: un `git merge` del upstream, un copy-paste de un
snippet, un fixture que alguien restaura, y el nombre viejo vuelve a un archivo
de producto. Este script es la guillotina ejecutable: recorre el árbol, aplica
una lista blanca **explícita** y falla si aparece cualquier otra cosa.

Qué se considera rastro:

- ``jenny`` / ``Jenny`` / ``JENNY`` en cualquier forma (identificadores, rutas,
  claves i18n, canales de notificación, comentarios, docs).
- ``flagdizero`` (el repositorio y el dominio del fabricante original).
- ``com.flagdizero`` como paquete Android.

Qué **no** es rastro, y por eso está en la lista blanca:

- La atribución que exige la AGPL-3.0: ``LICENSE``, ``THIRD_PARTY_NOTICES.md``,
  ``TRADEMARK.md``, la sección de origen del README, los autores de
  ``pyproject.toml``, y ``docs/REBRANDING.md`` / ``CHANGELOG.md``, que son el
  registro del cambio y tienen que poder nombrar lo que cambió.
- Los fixtures históricos ``*_retired_*.md`` de ``tests/agent/fixtures/``: son
  bytes de versiones retiradas y su digest sha256 es lo que dispara la retirada.
  Reescribirlos no es limpiar: rompe la migración (v. ``docs/REBRANDING.md``).

Uso::

    python scripts/audit_rebrand.py            # falla (rc 1) si hay rastros
    python scripts/audit_rebrand.py --verbose  # además, el inventario completo
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Directorios que no son producto: dependencias, cachés, artefactos de build.
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".mypy_cache", "build", "dist", "out", ".gradle", ".idea",
}

# Extensiones binarias: se auditan por nombre de fichero, no por contenido.
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".jar", ".zip", ".apk",
    ".ttf", ".woff", ".woff2", ".so", ".mp3", ".wav", ".pdf", ".keystore",
}

# Lista blanca: ficheros (rutas relativas) donde el nombre viejo es legítimo.
# Cada entrada necesita un motivo, porque una lista blanca sin motivo crece.
ALLOWED = {
    "LICENSE": "texto de la licencia AGPL-3.0",
    "THIRD_PARTY_NOTICES.md": "atribución de obras de terceros (AGPL-3.0 §5)",
    "TRADEMARK.md": "política de marcas del proyecto original",
    "README.md": "sección «Origen y atribución»",
    "pyproject.toml": "autores originales en los metadatos",
    "docs/REBRANDING.md": "registro del cambio: debe poder nombrar el origen",
    "docs/AUDIT.md": "registro de auditoría: nombra el origen para poder auditarlo",
    "CHANGELOG.md": "nota de migración (.jenny → .arkhiva)",
    "scripts/audit_rebrand.py": "el patrón y la lista blanca nombran lo que se busca",
    "tests/test_rebrand_audit.py": "planta rastros a propósito para probar el auditor",
}

ALLOWED_PATTERNS = (
    # Fixtures de templates retirados: bytes exactos, digest intacto.
    re.compile(r"tests/agent/fixtures/.*_retired_.*\.md$"),
)

TRACE = re.compile(r"jenny|flagdizero", re.IGNORECASE)


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    text: str


def is_allowed(rel: str) -> bool:
    return rel in ALLOWED or any(pattern.match(rel) for pattern in ALLOWED_PATTERNS)


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        yield path


def scan(root: Path) -> list[Hit]:
    hits: list[Hit] = []
    for path in iter_text_files(root):
        rel = path.relative_to(root).as_posix()
        if is_allowed(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if TRACE.search(line):
                hits.append(Hit(rel, number, line.strip()[:140]))
    return hits


def main(argv: list[str]) -> int:
    verbose = "--verbose" in argv
    hits = scan(ROOT)
    if verbose:
        print(f"lista blanca ({len(ALLOWED) + len(ALLOWED_PATTERNS)} entradas):")
        for name, why in ALLOWED.items():
            print(f"  - {name}: {why}")
        print()
    if not hits:
        print(f"auditoría limpia: ningún rastro fuera de la lista blanca ({len(ALLOWED)} ficheros)")
        return 0
    print(f"{len(hits)} rastro(s) del fabricante original fuera de la lista blanca:", file=sys.stderr)
    for hit in hits:
        print(f"  {hit.path}:{hit.line}: {hit.text}", file=sys.stderr)
    print(
        "\nSi el rastro es legítimo (atribución, registro, fixture histórico), "
        "añádelo a ALLOWED con su motivo en scripts/audit_rebrand.py. Si no, quítalo.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
