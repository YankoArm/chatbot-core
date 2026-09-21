#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE_NAME="${FLOWFORGE_SERVICE:-flowforge}"
BRANCH="${FLOWFORGE_BRANCH:-feature/flowforge-architecture}"
HEALTH_URL="${FLOWFORGE_HEALTH_URL:-http://127.0.0.1:8000/ready}"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

if [[ "$(id -u)" -ne 0 ]]; then
    fail "Ejecuta este actualizador como root."
fi

for command in git systemctl curl; do
    command -v "$command" >/dev/null 2>&1 ||
        fail "No se encuentra el comando requerido: $command"
done

APP_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

cd "$APP_DIR"

if ! git diff --quiet || ! git diff --cached --quiet; then
    fail "Hay cambios locales versionados. Revísalos antes de actualizar."
fi

CURRENT_BRANCH="$(git branch --show-current)"

if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
    fail "La rama actual es $CURRENT_BRANCH; se esperaba $BRANCH."
fi

echo "Buscando actualizaciones de FlowForge..."
git fetch origin "$BRANCH"

LOCAL_COMMIT="$(git rev-parse HEAD)"
REMOTE_COMMIT="$(git rev-parse "origin/$BRANCH")"

if [[ "$LOCAL_COMMIT" == "$REMOTE_COMMIT" ]]; then
    echo "FlowForge ya está actualizado."
    exit 0
fi

REQUIREMENTS_CHANGED=false

if ! git diff --quiet \
    "$LOCAL_COMMIT" \
    "$REMOTE_COMMIT" \
    -- requirements.txt; then
    REQUIREMENTS_CHANGED=true
fi

echo "Aplicando actualización..."
git merge --ff-only "origin/$BRANCH"

if [[ "$REQUIREMENTS_CHANGED" == true ]]; then
    PYTHON="$APP_DIR/.venv/bin/python"

    [[ -x "$PYTHON" ]] ||
        fail "No se encuentra el entorno virtual de FlowForge."

    echo "Actualizando dependencias..."
    "$PYTHON" -m pip install \
        --disable-pip-version-check \
        --requirement requirements.txt
fi

echo "Reiniciando FlowForge..."
systemctl restart "$SERVICE_NAME"

for attempt in {1..10}; do
    if curl --fail --silent \
        "$HEALTH_URL" >/dev/null; then
        echo "FlowForge actualizado y operativo."
        exit 0
    fi

    sleep 1
done

systemctl --no-pager --full status \
    "$SERVICE_NAME" || true

fail "FlowForge no respondió correctamente después de actualizar."