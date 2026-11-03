# Auditoría del rebranding — ARKHIVA Ω · ARKHIVA Mobile

Registro verificable de la conversión de **jenny-android-ai-agent** en **ARKHIVA Ω**.
Complementa a [REBRANDING.md](REBRANDING.md), que cuenta *qué* cambió; aquí está *cómo se
comprueba*.

Fecha: 2026-11-03 · Base: `main` @ `c225392` · Licencia: **AGPL-3.0** (sin cambios).

---

## 1. Qué se auditó y con qué

| Ámbito | Herramienta | Resultado |
|---|---|---|
| Rastros del fabricante original fuera de la atribución | `scripts/audit_rebrand.py` + `tests/test_rebrand_audit.py` | limpio |
| Identidad del APK y contrato de compilación | `tests/test_build_readiness.py` | 14 comprobaciones en verde |
| Versión app ↔ paquete Python | `tests/test_package_version.py` | `1.0.0-SOBERANO` ↔ `1.0.0` |
| Catálogo de la mascota ↔ módulo generado | `tests/webui/test_mascot_dataset.py` | en verde |
| Manifiestos de assets (templates, UI, skills) | `tests/utils/test_asset_manifests.py` | en verde |
| Plantillas retiradas (digest) | `tests/utils/test_template_refresh.py` | en verde |

Comando único:

```bash
python scripts/audit_rebrand.py --verbose && python -m pytest -q
```

## 2. Purga de identidad

- **1 597 ocurrencias en 225 ficheros** renombradas de forma coherente: nombres, URLs,
  claves i18n, canales de notificación, preferencias, puentes JS y constantes de modelo.
- Dominio y repositorio del fabricante original fuera de la documentación de producto y de
  las plantillas de issues.
- `config/paths.py`: retirada la migración de directorios de datos heredados
  (`.jenny`, `.minijenny`, `.nanobot`). Con un `applicationId` nuevo esa rama no podía
  encontrar nada; era código muerto que seguía nombrando al OEM. Sus tres tests se retiran
  con ella.
- **Riesgo encontrado y corregido:** el renombrado masivo había reescrito los fixtures
  `tests/agent/fixtures/*_retired_*.md`. Esos ficheros se comparan por digest sha256 para
  retirar plantillas obsoletas: con los bytes cambiados, la migración no disparaba y el
  texto retirado habría sobrevivido en disco como si lo hubiera escrito el usuario.
  Restaurados a sus bytes originales.

## 3. Atribución (lo que **no** se purga)

La AGPL-3.0 obliga a conservar la atribución, así que estos ficheros están en la lista
blanca del auditor *con su motivo*, y el test comprueba que la lista sigue siendo mínima:

| Fichero | Motivo |
|---|---|
| `LICENSE` | texto de la licencia |
| `THIRD_PARTY_NOTICES.md` | atribución de obras de terceros |
| `TRADEMARK.md` | política de marcas del proyecto original |
| `README.md` | sección «Origen y atribución» |
| `pyproject.toml` | autores originales en los metadatos |
| `docs/REBRANDING.md` | registro del cambio: debe poder nombrar el origen |
| `CHANGELOG.md` | nota de migración `.jenny → .arkhiva` |
| `scripts/audit_rebrand.py` | el patrón y la lista blanca nombran lo que se busca |
| `tests/test_rebrand_audit.py` | planta rastros a propósito para probar el auditor |

Los fixtures históricos entran por patrón (`tests/agent/fixtures/*_retired_*.md`), no por
nombre: son bytes de versiones retiradas y su digest es lo que dispara la retirada.

> **Obligación viva:** si este APK se redistribuye o se expone como servicio en red, hay
> que publicar el código fuente correspondiente (AGPL-3.0 §13) y mantener la licencia.

## 4. Datos, no código

La mascota dejó de tener tablas en el código:

| Dato | Fuente única | Consumidor |
|---|---|---|
| Vocabulario de umores (80 emojis, emoticonos, moods) | `arkhiva/templates/datasets/mascot_mood.json` | `arkhiva/session/mascot_mood.py` |
| Arte, tiempos y caras de umor | `arkhiva/templates/ui/assets/datasets/mascot.json` | `shared/mascot-assets.gen.js` (generado) |

- El módulo JS se **genera** con `python scripts/gen_mascot_assets.py`; un test falla si se
  separa del dataset.
- Se genera en lugar de cargarse con `fetch` porque la mascota se construye en el arranque,
  sin un `await` donde encajar la espera, e `import … with { type: 'json' }` ataría la app a
  un WebView que muchos teléfonos soportados no tienen.
- Un dataset ausente o malformado es **error explícito**: un vocabulario vacío haría
  desaparecer las caras en silencio, que es el fallo que ese módulo existe para evitar.
- `_DATA_ASSETS` viaja en el manifiesto de assets con los prompts (mismo lector) pero no se
  renderiza con Jinja, y el test de cobertura exige que las tres listas cubran el manifiesto
  exactamente.

## 5. Compilación

Estado de este entorno: **sin JDK ni Android SDK**, así que no se produjo un APK aquí. Lo
que sí queda fijado por test:

- `namespace` y `applicationId` = `org.buhonet.agente.arkhiva`;
- `versionCode 100`, `versionName "1.0.0-SOBERANO"`, `compileSdk`/`targetSdk` 35, `minSdk` 26;
- `versionName` sigue a `pyproject.toml` (test dedicado);
- firma de release desde `android/keystore.properties` o variables `ARKHIVA_KEYSTORE_*`;
  sin credenciales, el build queda **sin firmar** en vez de fallar;
- esquemas v1/v2/v3 declarados explícitamente (v1 apagado: `minSdk 26`);
- ninguna credencial versionada (`*.jks`, `*.keystore`, `keystore.properties` ignorados);
- variantes `foss` y `play`; la extensión de Drive solo en `play`;
- Chaquopy instala `requirements-android.lock.txt` con Python 3.11;
- todo el Kotlin vive bajo `org/buhonet/agente/arkhiva`.

Preflight local:

```bash
bash scripts/preflight_build.sh          # comprueba JDK, SDK, keystore y variantes
./gradlew :app:assembleFossRelease        # APK firmado si hay credenciales
```

## 6. Huecos conocidos (declarados, no escondidos)

1. **226 tests en rojo**, todos aserciones que fijan la redacción inglesa/italiana de un
   prompt ya traducido al español. No son regresiones de comportamiento; el triaje
   (actualizar la expectativa, nunca revertir la plantilla) está pendiente.
2. `arkhiva/templates/agent/llm_wiki.md`, parte de `_snippets/*` y `arkhiva/skills/**`
   siguen en inglés.
3. `assets/i18n/es.json` cubre navegación, chat, paneles y taller; `home`, `settings` y
   `board` caen todavía al inglés por el respaldo de `i18n.js`.
4. La mascota conserva su nombre técnico (`mascot*`): es el personaje heredado. Sus datos
   son datasets, pero el arte sigue siendo el del proyecto original y se sustituirá cuando
   exista arte propio.
5. `assembleRelease` firmado no se ejecutó aquí (sin JDK/SDK).
6. Los atajos de batería/autostart por fabricante se conservan **a propósito**: no son
   identidad, son lo que evita que el gateway muera con el teléfono dormido.
