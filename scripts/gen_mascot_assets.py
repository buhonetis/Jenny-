#!/usr/bin/env python3
"""Genera ``shared/mascot-assets.gen.js`` desde ``assets/datasets/mascot.json``.

El catálogo de la mascota —qué sprite es cada cuerpo, cada cara, cuánto dura un
parpadeo de boca— es **dato**, no código: vive en
``arkhiva/templates/ui/assets/datasets/mascot.json`` y este script lo convierte
en un módulo ES que el cliente importa de forma síncrona.

Se genera en vez de cargarse con ``fetch`` a propósito: la mascota se construye
en el arranque, antes de que exista un ``await`` donde encajar la espera, y un
``import ... with { type: 'json' }`` ata la app a una versión de WebView que
muchos teléfonos soportados no tienen. Un módulo generado y versionado conserva
las dos cosas: una sola fuente de verdad y cero asincronía en tiempo de
ejecución.

Uso::

    python scripts/gen_mascot_assets.py          # escribe el módulo
    python scripts/gen_mascot_assets.py --check  # falla si hay divergencia
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "arkhiva" / "templates" / "ui" / "assets"
DATASET = ASSETS / "datasets" / "mascot.json"
OUT = ASSETS / "shared" / "mascot-assets.gen.js"

HEADER = """\
/* GENERADO — no editar a mano.
 *
 * Fuente: `assets/datasets/mascot.json`.
 * Regenerar: `python scripts/gen_mascot_assets.py`.
 * Un test (`tests/webui/test_mascot_dataset.py`) falla si este archivo deja de
 * coincidir con el dataset, así que una edición a mano no sobrevive a la CI.
 */

"""


def render(dataset: dict) -> str:
    art = dataset["art"]
    timing = dataset["timing"]
    moods = dataset["moods"]

    def obj(mapping: dict) -> str:
        body = "".join(f"  {key}: {json.dumps(value)},\n" for key, value in mapping.items())
        return "{\n" + body + "}"

    return (
        HEADER
        + f"export const SIDE = {json.dumps(art['side'])};\n"
        + f"export const SIDE_TALK = {json.dumps(art['sideTalk'])};\n"
        + f"export const SIDE_BODY = {json.dumps(art['sideBody'])};\n"
        + f"export const BODY = {obj(art['body'])};\n"
        + f"export const FACE = {obj(art['face'])};\n"
        + f"export const SIDE_FACE = {obj(art['sideFace'])};\n"
        + f"export const WAVE = {obj(art['wave'])};\n"
        + f"export const MOOD_FACES = {json.dumps(moods)};\n"
        + f"export const MOUTH_FRAME_MS = {timing['mouthFrameMs']};\n"
        + f"export const TALK_ANIM_SWITCH_MS = {timing['talkSwitchMs']};\n"
        + f"export const TALK_QUIET_TO_THINK_MS = {timing['quietToThinkMs']};\n"
        + f"export const MOOD_HOLD_MS = {timing['moodHoldMs']};\n"
        + f"export const SLIDE_MS = {timing['slideMs']};\n"
    )


def main(argv: list[str]) -> int:
    rendered = render(json.loads(DATASET.read_text(encoding="utf-8")))
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if current != rendered:
            print(f"{OUT.relative_to(ROOT)} no coincide con {DATASET.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(rendered, encoding="utf-8")
    print(f"escrito {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
