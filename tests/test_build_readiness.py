"""El APK se puede compilar y firmar: la configuración lo dice, y no miente.

Este test no compila nada — en CI no hay JDK ni Android SDK, y un `assemble`
verde en una máquina no prueba lo que prueba un `assembleRelease` firmado en la
tuya. Lo que sí se puede fijar aquí es **el contrato de compilación**:

- la identidad que va dentro del APK (`namespace`, `applicationId`, versión);
- que la firma de release salga de credenciales fuera del repositorio, con
  repliegue a APK **sin firmar** en vez de un fallo;
- que ninguna credencial esté versionada;
- que las dos variantes (`foss`, `play`) sigan existiendo con la extensión de
  Drive solo en `play`;
- que los insumos del build (lock de Chaquopy, reglas de ProGuard, manifiestos
  de assets) estén donde el build los busca.

Un fallo aquí significa que el `assembleRelease` del README no produciría el
artefacto que el README promete.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android"
GRADLE = ANDROID / "app" / "build.gradle.kts"
PROGUARD = ANDROID / "app" / "proguard-rules.pro"
GITIGNORE = ROOT / ".gitignore"
LOCK = ROOT / "requirements-android.lock.txt"


def _gradle() -> str:
    return GRADLE.read_text(encoding="utf-8")


def test_the_apk_identity_is_the_sovereign_one() -> None:
    gradle = _gradle()
    assert 'namespace = "org.buhonet.agente.arkhiva"' in gradle
    assert 'applicationId = "org.buhonet.agente.arkhiva"' in gradle
    assert "versionCode = 100" in gradle
    assert 'versionName = "1.0.0-SOBERANO"' in gradle


def test_the_supported_android_range_is_declared() -> None:
    gradle = _gradle()
    assert "compileSdk = 35" in gradle
    assert "targetSdk = 35" in gradle
    assert "minSdk = 26" in gradle


def test_the_version_name_tracks_the_python_package() -> None:
    """`versionName` y `pyproject.toml` no pueden separarse: el updater y el
    about dicen cosas distintas si se separan (v. `test_package_version`)."""
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
    declared = re.search(r'versionName = "([^"]+)"', _gradle()).group(1)
    assert declared.split("-")[0] == version, (declared, version)


def test_release_signing_reads_credentials_from_outside_the_repo() -> None:
    gradle = _gradle()
    assert 'rootProject.file("keystore.properties")' in gradle
    for env in (
        "ARKHIVA_KEYSTORE_PATH",
        "ARKHIVA_KEYSTORE_PASSWORD",
        "ARKHIVA_KEY_ALIAS",
        "ARKHIVA_KEY_PASSWORD",
    ):
        assert env in gradle, env
    # Ninguna contraseña escrita en el build.
    assert not re.search(r'(storePassword|keyPassword)\s*=\s*"', gradle)


def test_an_unconfigured_release_still_builds_unsigned() -> None:
    gradle = _gradle()
    assert "val hasReleaseSigning" in gradle
    assert "if (hasReleaseSigning) {" in gradle
    assert "signingConfig = signingConfigs.findByName(\"release\")" in gradle


def test_signing_schemes_are_declared_explicitly() -> None:
    gradle = _gradle()
    assert "enableV1Signing = false" in gradle
    assert "enableV2Signing = true" in gradle
    assert "enableV3Signing = true" in gradle


def test_no_signing_material_is_versioned() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    leaked = [
        name for name in tracked
        if name.endswith((".jks", ".keystore")) or name.endswith("keystore.properties")
    ]
    assert not leaked, leaked
    ignore = GITIGNORE.read_text(encoding="utf-8")
    for pattern in ("keystore.properties", "*.jks", "*.keystore"):
        assert pattern in ignore, pattern


def test_proguard_rules_are_not_empty() -> None:
    rules = [line for line in PROGUARD.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.strip().startswith("#")]
    assert rules, "un release con minify y sin reglas quita lo que no debe"


def test_both_flavors_exist_and_drive_lives_only_in_play() -> None:
    gradle = _gradle()
    assert 'create("foss") { dimension = "store" }' in gradle
    assert 'create("play") { dimension = "store" }' in gradle
    play = ANDROID / "app" / "src" / "play" / "java" / "org" / "buhonet" / "agente" / "arkhiva"
    assert (play / "DriveBridge.kt").is_file()
    assert not (ANDROID / "app" / "src" / "foss" / "java" / "org" / "buhonet" / "agente" / "arkhiva" / "DriveBridge.kt").exists()


def test_chaquopy_installs_the_pinned_python_lock() -> None:
    gradle = _gradle()
    assert 'version = "3.11"' in gradle
    assert 'install("-r", "../../requirements-android.lock.txt")' in gradle
    assert LOCK.is_file() and LOCK.stat().st_size > 0


def test_every_kotlin_source_is_under_the_new_package() -> None:
    stray = [
        str(path.relative_to(ROOT))
        for path in (ANDROID / "app" / "src").rglob("*.kt")
        if "org/buhonet/agente/arkhiva" not in path.as_posix()
    ]
    assert not stray, stray
