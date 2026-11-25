#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

SERVICE_NAME="${FLOWFORGE_SERVICE:-flowforge}"
BRANCH="${FLOWFORGE_BRANCH:-feature/flowforge-architecture}"
HEALTH_URL="${FLOWFORGE_HEALTH_URL:-http://127.0.0.1:8000/ready}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${FLOWFORGE_DEPLOY_STATE:-$(dirname "$APP_DIR")/.flowforge-deploy-$(basename "$APP_DIR")}"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ "$(id -u)" -eq 0 ]] || fail "Ejecuta como root."

for command in git systemctl curl flock tar; do
    command -v "$command" >/dev/null || fail "Falta: $command"
done

mkdir -p "$STATE_DIR"
exec 9>"$STATE_DIR/update.lock"
flock -n 9 || {
    echo "Otra actualizacion esta en curso."
    exit 0
}

cd "$APP_DIR"
git diff --quiet && git diff --cached --quiet ||
    fail "Hay cambios locales versionados."

[[ "$(git branch --show-current)" == "$BRANCH" ]] ||
    fail "La rama actual no coincide con $BRANCH."

[[ -x "$APP_DIR/.venv/bin/python" ]] ||
    fail "No existe el entorno virtual."

[[ ! -e "$STATE_DIR/previous-venv" && ! -L "$STATE_DIR/previous-venv" ]] ||
    fail "Existe una recuperacion pendiente en $STATE_DIR/previous-venv."

git fetch origin "refs/heads/$BRANCH"
OLD_COMMIT="$(git rev-parse HEAD)"
NEW_COMMIT="$(git rev-parse FETCH_HEAD)"

if [[ "$OLD_COMMIT" == "$NEW_COMMIT" ]]; then
    echo "FlowForge ya esta actualizado: $OLD_COMMIT"
    exit 0
fi

git merge-base --is-ancestor "$OLD_COMMIT" "$NEW_COMMIT" ||
    fail "La actualizacion no es un avance directo."

"$APP_DIR/.venv/bin/python" "$APP_DIR/scripts/check_flowforge_ci.py" \
    --commit "$NEW_COMMIT" --branch "$BRANCH"

RELEASE_DIR="$STATE_DIR/releases/$NEW_COMMIT"
mkdir -p "$RELEASE_DIR"
SOURCE_DIR="$(mktemp -d "$STATE_DIR/source.XXXXXX")"
SWITCH_STARTED=false

healthy() {
    local attempt
    for attempt in {1..15}; do
        if systemctl is-active --quiet "$SERVICE_NAME" &&
            curl --fail --silent --show-error \
                --connect-timeout 2 --max-time 5 \
                "$HEALTH_URL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

finish() {
    local result=$?
    trap - EXIT
    if [[ "$result" -ne 0 && "$SWITCH_STARTED" == true ]]; then
        echo "Fallo de despliegue. Recuperando $OLD_COMMIT..." >&2

        # Restore files only after the candidate process has stopped.
        if ! systemctl stop "$SERVICE_NAME"; then
            echo "ERROR: no se pudo detener el servicio. Recuperacion manual requerida." >&2
            exit 1
        fi

        if ! git reset --keep "$OLD_COMMIT"; then
            echo "ERROR: no se pudo recuperar el codigo." >&2
            exit 1
        fi

        if [[ -e "$STATE_DIR/previous-venv" || -L "$STATE_DIR/previous-venv" ]]; then
            if [[ -L "$APP_DIR/.venv" ]]; then
                rm "$APP_DIR/.venv"
            elif [[ -e "$APP_DIR/.venv" ]]; then
                echo "ERROR: entorno inesperado. Recuperacion manual requerida." >&2
                exit 1
            fi
            mv "$STATE_DIR/previous-venv" "$APP_DIR/.venv"
        fi

        if systemctl start "$SERVICE_NAME" && healthy; then
            echo "Version anterior recuperada." >&2
        else
            echo "ERROR: la version anterior requiere revision manual." >&2
        fi
    fi

    rm -rf -- "$SOURCE_DIR"
    exit "$result"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "Preparando dependencias de $NEW_COMMIT..."
git archive "$NEW_COMMIT" | tar -x -C "$SOURCE_DIR"

# Rebuild a candidate environment left by a failed preparation.
rm -rf -- "$RELEASE_DIR/venv"
# Permit service users to traverse the deployment directories.
# Control files remain private under the global umask 077.
chmod a+x "$STATE_DIR" "$STATE_DIR/releases" "$RELEASE_DIR"

(
    # Runtime dependencies need to be readable by the service user.
    umask 022
    "$APP_DIR/.venv/bin/python" -m venv "$RELEASE_DIR/venv" --copies
    cd "$SOURCE_DIR"
    "$RELEASE_DIR/venv/bin/python" -m pip install \
        --disable-pip-version-check -r requirements.txt
)
"$RELEASE_DIR/venv/bin/python" -m pip check

# Recheck the checkout after dependency preparation.
[[ "$(git rev-parse HEAD)" == "$OLD_COMMIT" ]] ||
    fail "El commit local cambio durante la preparacion."
git diff --quiet && git diff --cached --quiet ||
    fail "El codigo local cambio durante la preparacion."

echo "Instalando $NEW_COMMIT..."
SWITCH_STARTED=true
systemctl stop "$SERVICE_NAME"

git merge --ff-only "$NEW_COMMIT"
mv "$APP_DIR/.venv" "$STATE_DIR/previous-venv"
ln -s "$RELEASE_DIR/venv" "$APP_DIR/.venv"

systemctl start "$SERVICE_NAME"
healthy || fail "La nueva version no supera la comprobacion de salud."

printf '%s\n' "$NEW_COMMIT" > "$STATE_DIR/installed-commit"
printf '%s\n' "$OLD_COMMIT" > "$STATE_DIR/previous-commit"

# Keep the previous environment available for diagnosis and recovery.
mv "$STATE_DIR/previous-venv" \
    "$STATE_DIR/venv-before-${NEW_COMMIT}-$(date +%s)"

SWITCH_STARTED=false
echo "FlowForge actualizado y operativo: $NEW_COMMIT"
