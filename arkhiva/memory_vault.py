"""Bóveda de memoria local-first de ARKHIVA.

La memoria de trabajo del agente vive dentro del workspace privado de la app
(``<data>/workspace/memory/MEMORY.md``), que en Android es inaccesible desde
fuera del UID. Este módulo añade la *bóveda*: un árbol Markdown plano, legible
por el usuario, en el almacenamiento externo privado de la aplicación
(``Android/data/<applicationId>/files/Vault_Memoria``), que no requiere ningún
permiso de almacenamiento y sobrevive a la desinstalación solo si el usuario lo
copia — a diferencia de ``getExternalStorageDirectory()``, que en Android 10+
está vetado sin MANAGE_EXTERNAL_STORAGE.

Qué es y qué no es:

* **Es** una superficie de consolidación legible: los cuatro archivos canónicos
  existen desde el primer arranque, con cabecera y fecha de inicialización, y
  ``mirror_workspace_memory`` vuelca en ellos lo que el agente ya sabe.
* **No es** la fuente de verdad en caliente. El agente sigue leyendo y
  escribiendo ``memory/`` dentro del workspace; la bóveda es el espejo
  exportable. Invertir esa relación obligaría a que cada lectura de memoria
  pasara por almacenamiento externo (más lento y con otro ciclo de vida), y a
  reimplementar la consolidación de Dream sobre dos sitios a la vez.

Se inicializa una sola vez por arranque (``initialize_vault``), es idempotente y
nunca levanta: si el almacenamiento externo no está montado —lo normal mientras
el teléfono arranca— el gateway debe seguir funcionando con la memoria del
workspace.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

VAULT_DIRNAME = "Vault_Memoria"

#: Los cuatro documentos canónicos de la plantilla ARKHIVA. El orden importa
#: solo para los logs; ninguno depende de otro.
CANONICAL_FILES: tuple[str, ...] = (
    "perfil_usuario.md",
    "bitacora_cognitiva.md",
    "habilidades_registradas.md",
    "cron_planificador.md",
)

#: Archivos del workspace que se espejan en la bóveda, y con qué nombre.
#: ``MEMORY.md`` es el conocimiento consolidado por Dream; ``USER.md`` el perfil
#: estable; ``SOUL.md`` el carácter que el usuario haya editado.
WORKSPACE_MIRROR: tuple[tuple[str, str], ...] = (
    ("memory/MEMORY.md", "bitacora_cognitiva.md"),
    ("USER.md", "perfil_usuario.md"),
    ("SOUL.md", "caracter_soberano.md"),
)


def resolve_vault_dir(android_context: object | None = None) -> Path | None:
    """Devuelve el directorio de la bóveda, o ``None`` si no hay almacenamiento.

    En Android se usa ``getExternalFilesDir(null)``: propiedad de la app, fuera
    del sandbox de datos, sin permisos. En escritorio (tests, CLI) no hay
    contexto Android y se devuelve ``None`` a propósito — la bóveda es una
    superficie del dispositivo, no del runtime de desarrollo.
    """
    getter = getattr(android_context, "getExternalFilesDir", None) if android_context else None
    if getter is None:
        return None
    try:
        base = getter(None)
    except Exception:  # noqa: BLE001 - un Context de prueba puede no implementarlo
        logger.opt(exception=True).debug("getExternalFilesDir falló; bóveda deshabilitada")
        return None
    if base is None:
        return None
    return Path(str(base)) / VAULT_DIRNAME


def _header(filename: str) -> str:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return (
        f"# ARKHIVA Ω · {filename}\n\n"
        f"> Documento canónico de la bóveda local. Inicializado: {stamp}\n\n"
    )


def initialize_vault_structure(vault_dir: Path) -> list[Path]:
    """Crea los documentos canónicos que falten. Idempotente.

    No sobrescribe nunca: un archivo existente es contenido del usuario o del
    agente, y la plantilla solo exige que el esqueleto exista.
    """
    vault_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for name in CANONICAL_FILES:
        path = vault_dir / name
        if not path.exists():
            path.write_text(_header(name), encoding="utf-8")
            created.append(path)
    return created


def initialize_vault(android_context: object | None = None) -> Path | None:
    """Punto de entrada desde ``android_entry``: best-effort, nunca levanta."""
    vault_dir = resolve_vault_dir(android_context)
    if vault_dir is None:
        return None
    try:
        created = initialize_vault_structure(vault_dir)
    except OSError as exc:
        logger.warning("No se pudo inicializar la bóveda en {}: {}", vault_dir, exc)
        return None
    logger.info(
        "Bóveda local lista en {} ({} documento(s) creado(s))", vault_dir, len(created)
    )
    return vault_dir


def _strip_frontmatter(text: str) -> str:
    """Quita un bloque YAML inicial, si lo hay, sin tocar el resto."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4 :].lstrip("\n")


def _safe_section(text: str) -> str:
    """Normaliza el texto para incrustarlo bajo un encabezado de nivel 2."""
    text = _strip_frontmatter(text).strip()
    # Un ``#`` de nivel 1 dentro de la sección rompería la jerarquía del
    # documento; se degrada a nivel 2.
    return re.sub(r"(?m)^# ", "## ", text)


def mirror_workspace_memory(workspace: Path, vault_dir: Path) -> list[Path]:
    """Vuelca memoria, perfil y carácter del workspace en la bóveda.

    Escribe **solo** las secciones de la bóveda que le corresponden, y lo hace
    de forma atómica (``tmp`` + ``replace``) para que una lectura concurrente
    del usuario desde otro gestor de archivos nunca vea un documento a medias.
    Devuelve los archivos efectivamente escritos.
    """
    initialize_vault_structure(vault_dir)
    written: list[Path] = []
    for source_rel, target_name in WORKSPACE_MIRROR:
        source = workspace / source_rel
        if not source.is_file():
            continue
        body = _safe_section(source.read_text(encoding="utf-8", errors="replace"))
        if not body:
            continue
        target = vault_dir / target_name
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        document = (
            f"{_header(target_name)}"
            f"## Consolidado desde `{source_rel}`\n\n"
            f"_Actualizado: {stamp}_\n\n"
            f"{body}\n"
        )
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(document, encoding="utf-8")
        tmp.replace(target)
        written.append(target)
    return written
