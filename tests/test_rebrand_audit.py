"""Auditoría del rebranding, ejecutada como test.

`scripts/audit_rebrand.py` es la guillotina: recorre el árbol y falla si el
fabricante original reaparece fuera de la lista blanca. Aquí se prueba **el
auditor**, no solo el árbol:

- que el árbol esté limpio ahora;
- que el detector siga viendo lo que dice ver (un auditor roto pasa en verde
  sobre todo, y ese es el fallo que no se nota);
- que la lista blanca sea mínima y que cada entrada exista de verdad — una
  entrada para un fichero inexistente es una puerta abierta a futuro;
- que el paquete Android y la app no vuelvan al namespace viejo.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android"
GRADLE = ANDROID / "app" / "build.gradle.kts"
MANIFEST = ANDROID / "app" / "src" / "main" / "AndroidManifest.xml"

_spec = importlib.util.spec_from_file_location(
    "audit_rebrand", ROOT / "scripts" / "audit_rebrand.py"
)
audit = importlib.util.module_from_spec(_spec)
# ``dataclass`` resuelve las anotaciones diferidas a través de ``sys.modules``:
# sin registrar el módulo, el ``exec`` de aquí falla con un AttributeError que
# no tiene nada que ver con lo que se está probando.
sys.modules[_spec.name] = audit
_spec.loader.exec_module(audit)


def test_the_tree_carries_no_vendor_trace() -> None:
    hits = audit.scan(ROOT)
    assert not hits, "rastros del fabricante original:\n" + "\n".join(
        f"  {hit.path}:{hit.line}: {hit.text}" for hit in hits
    )


def test_the_scanner_still_sees_a_planted_trace(tmp_path: Path) -> None:
    """Un detector que no ve nada pasaría el test anterior en verde."""
    (tmp_path / "producto.py").write_text(
        "NAMESPACE = 'com.flagdizero.arkhiva'\nSIZE = 'Jenny'\n", encoding="utf-8"
    )
    hits = audit.scan(tmp_path)
    assert {hit.path for hit in hits} == {"producto.py"}
    assert len(hits) == 2


def test_the_allowlist_is_not_a_hiding_place(tmp_path: Path) -> None:
    """Lo permitido se permite por **ruta**, no por nombre de fichero: un
    ``README.md`` dentro de un paquete de producto no hereda el permiso del
    README de la raíz."""
    (tmp_path / "producto" / "README.md").parent.mkdir()
    (tmp_path / "producto" / "README.md").write_text("Jenny\n", encoding="utf-8")
    (tmp_path / "producto" / "notas.md").write_text("flagdizero\n", encoding="utf-8")
    hits = audit.scan(tmp_path)
    assert {hit.path for hit in hits} == {"producto/README.md", "producto/notas.md"}


def test_every_allowlisted_file_exists() -> None:
    missing = [name for name in audit.ALLOWED if not (ROOT / name).is_file()]
    assert not missing, f"entradas de lista blanca sin fichero: {missing}"


def test_the_allowlist_stays_small() -> None:
    """Si crece sin control, deja de ser una auditoría."""
    assert len(audit.ALLOWED) <= 10, sorted(audit.ALLOWED)


def test_the_allowlist_only_covers_legal_or_historical_files() -> None:
    for name in audit.ALLOWED:
        assert name in {
            "LICENSE", "THIRD_PARTY_NOTICES.md", "TRADEMARK.md", "README.md",
            "pyproject.toml", "docs/REBRANDING.md", "docs/AUDIT.md", "CHANGELOG.md",
            "scripts/audit_rebrand.py", "tests/test_rebrand_audit.py",
        }, name


def test_no_source_file_under_the_packages_names_the_vendor() -> None:
    sources = [
        *(ROOT / "arkhiva").rglob("*.py"),
        *(ROOT / "arkhiva" / "templates").rglob("*.md"),
        *(ROOT / "arkhiva" / "templates" / "ui" / "assets").rglob("*.js"),
        *(ANDROID / "app" / "src").rglob("*.kt"),
        *(ANDROID / "app" / "src").rglob("*.xml"),
    ]
    offenders = [
        str(path.relative_to(ROOT))
        for path in sources
        if re.search(r"jenny|flagdizero", path.read_text(encoding="utf-8", errors="ignore"), re.I)
    ]
    assert not offenders, offenders


def test_the_android_package_is_the_new_one() -> None:
    gradle = GRADLE.read_text(encoding="utf-8")
    assert 'namespace = "org.buhonet.agente.arkhiva"' in gradle
    assert 'applicationId = "org.buhonet.agente.arkhiva"' in gradle
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "com.flagdizero" not in manifest
    # El manifiesto no lleva `package=`: el namespace vive en Gradle, y las
    # clases se nombran relativas (".MainActivity"). Un `package=` viejo sería
    # un segundo sitio donde el paquete puede quedarse atrás.
    assert "package=" not in manifest
    assert 'android:name=".' in manifest
