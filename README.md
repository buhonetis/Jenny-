# ARKHIVA Ω · ARKHIVA Mobile

**Agente cognitivo soberano, local-first, que vive en tu teléfono Android.**

ARKHIVA Mobile es la distribución móvil de ARKHIVA Ω: un agente que recuerda de forma
permanente, actúa por su cuenta cuando se lo pides, escribe sus propias mini-apps y puede
ser la pantalla de inicio del teléfono. La memoria, los archivos y las conversaciones no
salen del dispositivo: inferencia local por defecto (`127.0.0.1:11434`) y proveedor remoto
solo si tú lo configuras, con tu propia clave.

- **Paquete / applicationId:** `org.buhonet.agente.arkhiva`
- **Etiqueta visible:** ARKHIVA Mobile
- **Versión:** `1.0.0-SOBERANO` (`versionCode 100`)
- **Licencia:** AGPL-3.0 (ver [LICENSE](LICENSE)) — se mantiene AGPL-3.0 íntegra

---

## Doctrina

ARKHIVA Ω se rige por un extracto canónico propio (`Ω-EXTRACT-BUHONET-001`,
v4.1.0-MOONSHOT). Los cuatro pilares que tocan este repositorio:

| Pilar | Qué significa aquí |
|---|---|
| **Freno Epistemológico** | El agente no afirma lo que no puede verificar: distingue lo observado, lo inferido y lo que ignora. Nunca inventa una herramienta, un archivo ni un resultado. |
| **WORM** | La memoria se escribe una vez y se versiona; no se reescribe el pasado para tapar un error. Los archivos canónicos viven en `Vault_Memoria/`. |
| **MAREA / VRAM** | Presupuesto explícito de contexto y de llamadas al modelo. Cuando se agota, el agente para y lo dice, en vez de degradarse en silencio. |
| **Enjambre** | Papeles especializados (ECCO, LadyBITx, WATCHDOG, NOXIA, NAMAAH, JOLLYROGERS) sobre el mismo bus de herramientas, sin privilegios implícitos. |

## Qué hace

- **Memoria permanente** en Markdown legible, dentro de `Vault_Memoria/`, con consolidación
  periódica (Dream) y mantenimiento de cuadernos (Gardener).
- **Cuadernos (notebooks)** como wikis locales con páginas, tablero, recordatorios y chat
  propio; el chat personal es el cuaderno raíz.
- **Trabajo programado**: recordatorios, comprobaciones recurrentes y alertas condicionales
  mediante trabajos `cron`, con modo `reminder` y modo `monitor`.
- **Mini-apps** construidas a petición, con su propia interfaz y datos locales.
- **Pantalla de inicio** completa: la WebUI puede sustituir al launcher.

## Primera puesta en marcha

1. Instala el APK (sideload) o compílalo (ver abajo).
2. Si vas a usar inferencia local, arranca un servidor compatible con OpenAI Chat
   Completions y deja que escuche en el teléfono o en la máquina que declares:
   ```bash
   ollama serve            # por defecto 127.0.0.1:11434
   ollama pull qwen2.5-coder:3b
   ```
3. Abre ARKHIVA Mobile. El perfil local-first apunta a `http://127.0.0.1:11434/v1/` con el
   modelo `qwen2.5-coder:3b`; puedes cambiarlo por entorno:

   | Variable | Efecto |
   |---|---|
   | `ARKHIVA_LOCAL_BASE_URL` | Endpoint compatible con OpenAI |
   | `ARKHIVA_LOCAL_MODEL` | Modelo por defecto |
   | `ARKHIVA_LOCAL_API_KEY` | Clave (irrelevante en servidores locales) |
   | `ARKHIVA_LOCAL_TIMEOUT` | Timeout en segundos |

   Los nombres de estos *knobs* están centralizados en `arkhiva/config/runtime_env.py`.
4. La red del APK solo permite tráfico en claro hacia el gateway local y los hosts
   enumerados en `android/app/src/main/res/xml/network_security_config.xml`
   (`127.0.0.1`, `localhost`, `10.0.2.2`, `10.8.0.1`, `100.120.133.77`). Cualquier otro
   servicio debe ser HTTPS.

## Compilar

Requisitos: JDK 17, Android SDK 35, Python 3.11 para los tests.

```bash
# APK de depuración
./gradlew :app:assembleDebug

# APK de release firmado (sideload) — crea antes tu keystore
keytool -genkeypair -v -keystore arkhiva-release.jks -alias arkhiva \
        -keyalg RSA -keysize 4096 -validity 10000
# declara las credenciales en android/keystore.properties (no se versiona)
./gradlew :app:assembleRelease
```

El keystore y sus contraseñas **no** se versionan: `android/keystore.properties` y
`*.jks` están ignorados. Si redistribuyes el APK, usa tu propia firma.

## Tests

```bash
python -m pytest -q
```

Estado actual de la migración (ver [docs/REBRANDING.md](docs/REBRANDING.md)): 14 366 pasan,
393 se omiten y **226 fallan**. Todos los fallos restantes son expectativas de test que
fijan la redacción **inglesa o italiana** de los prompts; el corpus se tradujo al español
por decisión de producto (`todo_es`). No son regresiones de comportamiento y su triaje está
en curso.

## Privacidad y seguridad

- Sin telemetría. Sin cuenta. Sin servicio en la nube por defecto.
- La memoria y los cuadernos son Markdown en el almacenamiento de la app, en
  `Vault_Memoria/`, accesible al usuario.
- Regla de no exfiltración en el corpus cognitivo: el agente no envía datos del dispositivo
  a terceros, ni los incluye en llamadas a herramientas que no sean las declaradas.
- El sandbox del workspace está activo y el acceso a red de la app es una lista blanca.

## Origen y atribución

ARKHIVA Mobile es una bifurcación de **jenny-android-ai-agent**, obra original de
**flagdizero** (<https://github.com/flagdizero/jenny-android-ai-agent>), publicada bajo
AGPL-3.0.

Este repositorio conserva la licencia AGPL-3.0 y **debe seguir siendo AGPL-3.0** si se
redistribuye o se expone como servicio en red. Todos los cambios respecto al original están
documentados en [docs/REBRANDING.md](docs/REBRANDING.md) y en [CHANGELOG.md](CHANGELOG.md).
Las marcas, el nombre y la identidad visual del proyecto original pertenecen a su autor y no
se reclaman aquí.

> Nota de cumplimiento: al ser una obra derivada de código AGPL-3.0, la distribución de este
> APK obliga a ofrecer el código fuente correspondiente. Si publicas una release, publica
> también el tag exacto desde el que se compiló.
