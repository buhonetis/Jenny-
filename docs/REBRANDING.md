# Rebranding: jenny-android-ai-agent → ARKHIVA Ω (ARKHIVA Mobile)

Registro de cambios respecto al proyecto original. Protocolo aplicado:
`Ω-REBRAND-JENNY-001`, sobre la doctrina `Ω-EXTRACT-BUHONET-001` (v4.1.0-MOONSHOT).

Origen: **jenny-android-ai-agent**, de **flagdizero**
(<https://github.com/flagdizero/jenny-android-ai-agent>), AGPL-3.0. Esta obra derivada
conserva la licencia y la atribución; ver [LICENSE](../LICENSE) y
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Identidad

| Antes | Ahora |
|---|---|
| Nombre de producto | Jenny | **ARKHIVA Ω** / **ARKHIVA Mobile** |
| applicationId | `com.flagdizero.jenny` | **`org.buhonet.agente.arkhiva`** |
| Paquete Kotlin | `com.flagdizero.jenny` | `org.buhonet.agente.arkhiva` |
| Paquete Python | `jenny/` | `arkhiva/` |
| Directorio de datos | `.jenny` | `.arkhiva` |
| versionName | (heredado) | **`1.0.0-SOBERANO`** |
| versionCode | (heredado) | **100** |
| Tema nativo | `Theme.Jenny*` | `Theme.Arkhiva*` |
| Logo / símbolo | mascota | **Ω**, sin mascota |

Entrada del módulo Python: `python -m arkhiva`. Punto de arranque Android:
`arkhiva/android_entry.py`.

## Renombrado interno

- Árbol Java/Kotlin movido a `android/app/src/{main,foss,play,test}/java/org/buhonet/agente/arkhiva/`.
- Clases `Jenny*` → `Arkhiva*` (`JennyApplication.kt` → `ArkhivaApplication.kt`,
  `JennyBrowserBridge.kt` → `ArkhivaBrowserBridge.kt`, …).
- `AndroidManifest`, layouts, temas, drawables y canales de notificación actualizados al
  nuevo paquete y a la nueva identidad visual (`ic_launcher_arkhiva_*`, `ic_stat_arkhiva`).

## Interfaz

- **Paleta soberana**: obsidiana `#0F1115`, superficie `#161920`, acento cian `#00FFC2`,
  primario `#4A90E2`, texto `#ECEFF4` / `#9AA0A6`, error `#FF5252`
  (`res/values/colors.xml`, fuente única de color nativo).
- El tema por defecto de la WebUI (`synthwave`) pasa a `--bg: #0f1115` para no desalinearse
  del splash del sistema; los splash de `values-v31/themes.xml` resuelven el color por
  `@color/arkhiva_dark`.
- Cadenas nativas extraídas a recursos: `values/strings.xml` (inglés) y
  **`values-es/strings.xml`** (español). La pantalla de arranque y de error ya no llevan
  texto incrustado en el layout.
- Nuevo catálogo WebUI `assets/i18n/es.json` con **respaldo al inglés** en `i18n.js`
  (`locale actual → en → clave`). La traducción cubre navegación, chat, comandos, paneles,
  espacio de trabajo, ajustes iniciales, skills y taller; el resto del catálogo (home,
  settings, board) cae al inglés mientras se traduce.

## Capa cognitiva

Decisión de producto: **corpus de prompts íntegramente en español** (`todo_es`).

- Traducidos: `templates/SOUL.md`; `templates/agent/{identity, orchestrator, tidy,
  platform_policy, scheduling, readonly, project, project_init, subagent_system,
  subagent_announce, consolidator_archive, consolidator_handoff, diary_section,
  inflight_checkpoint, cron_reminder, cron_monitor, plan_step, plan_mode, board_pass,
  notebook_greeting, max_iterations_message, skills_section, apps_section,
  tool_inventory, tool_contract, dream, dream_review, gardener, …}.md`;
  `agent/_snippets/untrusted_content.md`; `agent/types/*.md`.
- Los **literales de parser** se conservan en inglés a propósito (`### Working state`,
  `**To research:**`, `**Before deleting**`, ids de herramientas y acciones como
  `board_propose_board`, `plan_propose`, `raw/notes/open-gaps.md`): son contrato con el
  código, no prosa.
- Presupuestos de tamaño respetados: `agent/readonly.md` ≤ 1500 caracteres,
  `agent/orchestrator.md` < 3200, `agent/scheduling.md` ≤ 1450.
- Desviación consciente respecto al original: el `SOUL.md` español elimina las reglas
  «soy humano / nunca admitas ser una IA» y las de emoji/nota de voz de WhatsApp; las
  sustituye por voz sobria y **Freno Epistemológico**.
- Pendiente: `agent/llm_wiki.md`, parte de `agent/_snippets/*` y las skills de
  `arkhiva/skills/**` siguen en inglés (las skills se dejan para una segunda pasada porque
  sus ejemplos son instrucciones ejecutables).

## Memoria soberana

- Nuevo `arkhiva/memory_vault.py`: `Vault_Memoria/` como directorio canónico de memoria,
  con `SOUL.md`, `USER.md`, `memory/MEMORY.md`, `AGENTS.md` y espejo del workspace.
- En Android, la bóveda se resuelve bajo `getExternalFilesDir(null)/Vault_Memoria`, de modo
  que el usuario puede abrirla, copiarla y versionarla con cualquier herramienta.
- Inicialización idempotente y escritura atómica (`.tmp` + `replace`); el espejo elimina el
  frontmatter y degrada `# ` a `## ` para no romper la jerarquía del documento destino.
- Orden de arranque (`android_entry`): workspace → `set_workspace_dir` →
  `sync_workspace_templates` → extracción de fuentes → `initialize_vault` →
  `ensure_minimal_config` → gateway con reintentos.

## Inferencia local

- `arkhiva/config/local_first.py`: perfil explícito, nunca aplicado en silencio.
  Base `http://127.0.0.1:11434/v1/`, modelo `qwen2.5-coder:3b`, `api_key` con
  `repr=False`, timeout 120 s.
- Los nombres de las variables `ARKHIVA_LOCAL_*` viven en `config/runtime_env.py`, el único
  lugar donde se declaran los *knobs* `ARKHIVA_*`.

## Tests

- Nuevos: `tests/test_memory_vault.py` (6), `tests/config/test_local_first.py` (4).
- Actualizados para el nuevo contrato: contratos de prompt (`readonly`, `plan`, `board`,
  `subagent_*`, `prompt_matches_offered_tools`, `cron_monitor`), `test_template_refresh`,
  `test_splash_themes_match_the_webui` (resuelve `@color/…`), `test_native_shell_contract`
  (nuevo paquete y strings por recurso), `test_extensions` (ruta `play/`), y
  `test_prompt_markdown_is_english` (el detector de italiano ahora mira solo `arkhiva/skills`).
- Restaurados los fixtures históricos `tests/agent/fixtures/*_retired_*.md`: el renombrado
  masivo los había reescrito y eso rompía la detección por *digest* de los templates
  retirados (riesgo real de resucitar texto obsoleto en el prompt).

### Fallos conocidos (226)

Todos son aserciones que fijan la redacción inglesa/italiana de un prompt traducido. Se
corrigen actualizando la *expectativa*, nunca revirtiendo el template. Distribución:

```
45 tests/agent/test_project_prompt_contract.py
24 tests/agent/test_plan_loop.py
20 tests/agent/test_platform_facts_upstream.py
16 tests/agent/test_dream.py
14 tests/agent/test_context_builder.py
13 tests/agent/test_project_tidy_command.py
12 tests/agent/test_notebook_gaps_go_to_research.py
11 tests/plan/test_driver.py
 8 tests/agent/test_inflight_compaction.py
 6 tests/agent/test_project_block_is_fed.py
 5 tests/agent/test_dream_review.py
 … (resto: subagentes, tablero, cron, tipos de agente)
```

## Pendiente

1. Triaje de las 226 aserciones de redacción (mecánico, archivo por archivo).
2. Traducir `agent/llm_wiki.md`, `_snippets` restantes y `arkhiva/skills/**`.
3. Completar `es.json` (home, settings, board) y añadir `es` a la paridad de claves.
4. `docs/reference/local-models.md`: la sección de tráfico en claro sigue describiendo el
   APK anterior.
5. `assembleRelease` firmado: bloqueado en este entorno por falta de JDK y Android SDK; el
   *runbook* está en el README.
6. Retirar la mascota de los recursos heredados que aún la referencian (`docs/img/`,
   capturas del README original).
