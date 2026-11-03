#!/usr/bin/env bash
# Preflight para compilar ARKHIVA Mobile: dice qué falta antes de gastar 10 minutos.
#
# No compila: comprueba las tres cosas que hacen fallar un `assembleRelease` en
# una máquina nueva — JDK, Android SDK y credenciales de firma — y la identidad
# que va dentro del APK. Sin credenciales el build sale igualmente, **sin
# firmar**: eso es una elección del Gradle, no un fallo, y aquí se avisa.
set -u

ok=0; warn=0; bad=0
say()  { printf '%-6s %s\n' "$1" "$2"; }
pass() { say "OK"   "$1"; ok=$((ok+1)); }
note() { say "AVISO" "$1"; warn=$((warn+1)); }
fail() { say "FALLO" "$1"; bad=$((bad+1)); }
have() { command -v "$1" >/dev/null 2>&1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRADLE="$ROOT/android/app/build.gradle.kts"

echo "ARKHIVA Mobile — preflight de compilación"
echo

# ── JDK 17 ──
if have java; then
  version=$(java -version 2>&1 | head -1)
  case "$version" in
    *\"17*|*\"21*) pass "JDK: $version" ;;
    *) note "JDK distinto de 17/21: $version" ;;
  esac
else
  fail "java no está en PATH (hace falta JDK 17)"
fi

# ── Android SDK 35 ──
sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
if [ -n "$sdk" ] && [ -d "$sdk/platforms/android-35" ]; then
  pass "Android SDK: $sdk (platform 35)"
elif [ -n "$sdk" ] && [ -d "$sdk" ]; then
  note "Android SDK en $sdk, pero sin platforms/android-35"
elif have sdkmanager; then
  note "sdkmanager presente; instala platforms;android-35"
else
  fail "Android SDK no configurado (ANDROID_HOME/ANDROID_SDK_ROOT)"
fi

# ── Gradle wrapper ──
if [ -x "$ROOT/android/gradlew" ] || [ -x "$ROOT/gradlew" ]; then
  pass "Gradle wrapper presente"
else
  fail "no hay gradlew"
fi

# ── Firma ──
props="$ROOT/android/keystore.properties"
if [ -f "$props" ]; then
  pass "keystore.properties presente (release firmado)"
  grep -q '^storeFile=' "$props" || note "keystore.properties sin storeFile="
elif [ -n "${ARKHIVA_KEYSTORE_PATH:-}" ]; then
  pass "credenciales por entorno (ARKHIVA_KEYSTORE_PATH)"
else
  note "sin credenciales: assembleRelease producirá un APK SIN FIRMAR"
fi
for f in "$ROOT"/*.jks "$ROOT"/android/*.jks; do
  [ -e "$f" ] && note "keystore en el árbol de trabajo: $(basename "$f") (no lo commitees)"
done

# ── Identidad que va dentro del APK ──
if [ -f "$GRADLE" ]; then
  for needle in 'applicationId = "org.buhonet.agente.arkhiva"' \
                'versionCode = 100' 'versionName = "1.0.0-SOBERANO"' \
                'compileSdk = 35'; do
    grep -qF "$needle" "$GRADLE" && pass "gradle: $needle" || fail "gradle: falta $needle"
  done
else
  fail "no encuentro android/app/build.gradle.kts"
fi

# ── Auditoría de identidad ──
if have python3; then
  if python3 "$ROOT/scripts/audit_rebrand.py" >/dev/null 2>&1; then
    pass "auditoría de identidad limpia"
  else
    fail "la auditoría de identidad encuentra rastros (python3 scripts/audit_rebrand.py)"
  fi
fi

echo
echo "resumen: $ok ok, $warn avisos, $bad fallos"
echo "compilar:  ./gradlew :app:assembleFossRelease    # variante sin Google"
echo "           ./gradlew :app:assemblePlayRelease    # variante con Drive"
[ "$bad" -eq 0 ]
