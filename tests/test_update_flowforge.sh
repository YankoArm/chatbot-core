#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

trap 'echo "ERROR en linea $LINENO (escenario: ${TEST_MODE:-preparacion})" >&2; if [[ -n "${CASE_DIR:-}" && -f "$CASE_DIR/output.log" ]]; then cat "$CASE_DIR/output.log" >&2; fi' ERR


mkdir -p "$TEST_ROOT/bin"

cat > "$TEST_ROOT/bin/mock" <<'MOCK'
#!/usr/bin/env bash
set -eu

case "$(basename "$0")" in
    id)
        echo 0
        ;;
    flock|sleep)
        exit 0
        ;;
    git)
        case "$1" in
            diff|fetch|merge-base)
                exit 0
                ;;
            branch)
                echo feature/flowforge-architecture
                ;;
            rev-parse)
                if [[ "$2" == FETCH_HEAD ]]; then
                    echo new
                else
                    cat "$CASE_DIR/commit"
                fi
                ;;
            archive)
                tar -cf - --files-from /dev/null
                ;;
            merge)
                echo new > "$CASE_DIR/commit"
                ;;
            reset)
                echo old > "$CASE_DIR/commit"
                ;;
            *)
                echo "Unexpected git command: $*" >&2
                exit 99
                ;;
        esac
        ;;
    systemctl)
        echo "$1" >> "$CASE_DIR/service.log"
        case "$1" in
            stop)
                if [[ "$TEST_MODE" == stop_failure ]]; then
                    exit 1
                fi
                ;;
            start)
                if [[ "$TEST_MODE" == start_failure ]] &&
                    [[ "$(cat "$CASE_DIR/commit")" == new ]]; then
                    exit 1
                fi
                ;;
            is-active)
                exit 0
                ;;
            *)
                exit 99
                ;;
        esac
        ;;
    curl)
        if [[ "$TEST_MODE" == health_failure ]] &&
            [[ "$(cat "$CASE_DIR/commit")" == new ]]; then
            exit 1
        fi
        ;;
    *)
        exit 99
        ;;
esac
MOCK

chmod +x "$TEST_ROOT/bin/mock"
for command in id flock sleep git systemctl curl; do
    cp "$TEST_ROOT/bin/mock" "$TEST_ROOT/bin/$command"
done

run_case() {
    local mode="$1"
    export TEST_MODE="$mode"
    export CASE_DIR="$TEST_ROOT/$mode"
    export FLOWFORGE_DEPLOY_STATE="$CASE_DIR/state"

    mkdir -p "$CASE_DIR/app/scripts" "$CASE_DIR/app/.venv/bin"
    echo old > "$CASE_DIR/commit"
    : > "$CASE_DIR/service.log"

    cp "$PROJECT_DIR/scripts/update_flowforge.sh" \
        "$CASE_DIR/app/scripts/update_flowforge.sh"

    cat > "$CASE_DIR/app/.venv/bin/python" <<'PYTHON'
#!/usr/bin/env bash
set -eu

if [[ "$1" == -m && "$2" == venv ]]; then
    mkdir -p "$3/bin"
    cp "$0" "$3/bin/python"
    chmod +x "$3/bin/python"
elif [[ "$1" == -m && "$2" == pip ]]; then
    if [[ "$3" == install && "$TEST_MODE" == dependency_failure ]]; then
        exit 1
    fi
elif [[ "$TEST_MODE" == ci_failure ]]; then
    exit 1
fi
PYTHON
    chmod +x "$CASE_DIR/app/.venv/bin/python"

    local result=0
    PATH="$TEST_ROOT/bin:$PATH" \
        bash "$CASE_DIR/app/scripts/update_flowforge.sh" \
        > "$CASE_DIR/output.log" 2>&1 || result=$?

    case "$mode" in
        success)
            [[ "$result" -eq 0 ]]
            [[ "$(cat "$CASE_DIR/commit")" == new ]]
            [[ -L "$CASE_DIR/app/.venv" ]]
            [[ "$(cat "$CASE_DIR/state/installed-commit")" == new ]]
            [[ "$(cat "$CASE_DIR/state/previous-commit")" == old ]]
            [[ ! -e "$CASE_DIR/state/previous-venv" ]]
            ;;
        ci_failure|dependency_failure)
            [[ "$result" -ne 0 ]]
            [[ "$(cat "$CASE_DIR/commit")" == old ]]
            [[ ! -L "$CASE_DIR/app/.venv" ]]
            [[ -x "$CASE_DIR/app/.venv/bin/python" ]]
            [[ ! -s "$CASE_DIR/service.log" ]]
            ;;
        start_failure|health_failure)
            [[ "$result" -ne 0 ]]
            [[ "$(cat "$CASE_DIR/commit")" == old ]]
            [[ ! -L "$CASE_DIR/app/.venv" ]]
            [[ -x "$CASE_DIR/app/.venv/bin/python" ]]
            [[ ! -e "$CASE_DIR/state/previous-venv" ]]
            grep -q "Version anterior recuperada" "$CASE_DIR/output.log"
            ;;
        stop_failure)
            [[ "$result" -ne 0 ]]
            [[ "$(cat "$CASE_DIR/commit")" == old ]]
            [[ ! -L "$CASE_DIR/app/.venv" ]]
            ! grep -q '^start$' "$CASE_DIR/service.log"
            grep -q "Recuperacion manual requerida" "$CASE_DIR/output.log"
            ;;
    esac

    echo "PASS: $mode"
}

for scenario in success ci_failure dependency_failure \
    start_failure health_failure stop_failure; do
    run_case "$scenario"
done

echo "6 deployment scenarios passed."
