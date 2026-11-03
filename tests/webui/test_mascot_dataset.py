"""El catálogo de la mascota es un dataset, y el módulo que lo publica concuerda.

La mascota tenía sus rutas de sprite, sus tiempos y sus umores escritos en
`shared/arkhiva-mascot.js`. Un dato así en el código se edita en un solo sitio y
se olvida en otro: el dataset es la fuente, `scripts/gen_mascot_assets.py` lo
convierte en módulo y este test impide que los dos se separen.

**Por qué generado y no `fetch`:** la mascota se construye en el arranque, donde
no hay un `await` donde encajar la espera, e `import ... with { type: 'json' }`
ata la app a una versión de WebView que muchos teléfonos soportados no tienen.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "arkhiva" / "templates" / "ui" / "assets"
DATASET = ASSETS / "datasets" / "mascot.json"
GENERATED = ASSETS / "shared" / "mascot-assets.gen.js"


def test_the_generated_module_matches_the_dataset() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gen_mascot_assets.py"), "--check"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_every_asset_the_dataset_names_ships() -> None:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    art = dataset["art"]
    sources = [
        art["side"], art["sideTalk"], art["sideBody"],
        *art["body"].values(), *art["face"].values(), *art["sideFace"].values(),
        *art["wave"].values(),
    ]
    missing = [
        src for src in sources
        if not (ASSETS / src.removeprefix("/html-mobile/assets/")).is_file()
    ]
    assert not missing, f"sprites declarados en el dataset y ausentes: {missing}"


def test_the_mascot_module_holds_no_art_table_of_its_own() -> None:
    source = (ASSETS / "shared" / "arkhiva-mascot.js").read_text(encoding="utf-8")
    assert "/html-mobile/assets/arkhiva-" not in source, "la tabla volvió al código"
    assert "from './mascot-assets.gen.js'" in source


def test_the_timings_come_from_the_dataset() -> None:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    source = (ASSETS / "shared" / "arkhiva-mascot.js").read_text(encoding="utf-8")
    for literal in dataset["timing"].values():
        assert f"= {literal}" not in source, f"tiempo hardcodeado: {literal}"
