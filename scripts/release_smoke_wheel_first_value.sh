#!/usr/bin/env bash
# Installed-wheel first-value smoke (issue #625).
#
# Continuously proves the exact no-clone workflow promised on PyPI: build the
# wheel, install it into an isolated virtualenv, assess one local CSV with
# `martenweave start <csv> --no-open --json`, verify every persisted result
# surface from that single run (manifest, dataset profile, readiness report,
# unapplied draft proposal), and validate the local API/Workbench contract for
# the start-created workspace.  Everything runs from the installed wheel with
# the working directory inside a temporary workspace — never from the source
# tree.  Every failure line names the broken user-visible contract so the
# output is directly usable as release evidence.
#
# Requires: python3 (>=3.11) with the `build` package (the repo .venv
# qualifies), and network access so pip can resolve runtime dependencies —
# the same PyPI-equivalent install a user performs.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SMOKE_DIR="$(mktemp -d)"
WORKBENCH_PID=""

cleanup() {
    local status=$?
    if [[ -n "${WORKBENCH_PID}" ]] && kill -0 "${WORKBENCH_PID}" 2>/dev/null; then
        kill "${WORKBENCH_PID}" 2>/dev/null || true
        wait "${WORKBENCH_PID}" 2>/dev/null || true
    fi
    if [[ ${status} -eq 0 ]]; then
        rm -rf "${SMOKE_DIR}"
    else
        echo "Smoke evidence preserved at: ${SMOKE_DIR}"
    fi
}
trap cleanup EXIT

if python3 -c 'import build' >/dev/null 2>&1; then
    PYTHON=python3
elif [[ -x "${REPO_ROOT}/.venv/bin/python" ]] \
    && "${REPO_ROOT}/.venv/bin/python" -c 'import build' >/dev/null 2>&1; then
    PYTHON="${REPO_ROOT}/.venv/bin/python"
else
    echo "FAIL [wheel build] python 'build' package not found"
    echo "Install the dev extras first: pip install -e '.[dev]'"
    exit 1
fi

echo "SMOKE build wheel from current tree"
"${PYTHON}" -m build --wheel --outdir "${SMOKE_DIR}/dist" "${REPO_ROOT}" \
    >"${SMOKE_DIR}/build.log" 2>&1 || {
        echo "FAIL [wheel build] python -m build failed; last log lines:"
        tail -20 "${SMOKE_DIR}/build.log"
        exit 1
    }
WHEEL="$(ls "${SMOKE_DIR}"/dist/*.whl)"
echo "OK   [wheel build] $(basename "${WHEEL}")"

echo "SMOKE install wheel into isolated virtualenv"
"${PYTHON}" -m venv "${SMOKE_DIR}/venv"
VENV_PY="${SMOKE_DIR}/venv/bin/python"
"${VENV_PY}" -m pip install --quiet --upgrade pip
"${VENV_PY}" -m pip install --quiet "${WHEEL}" || {
    echo "FAIL [wheel install] pip could not install $(basename "${WHEEL}") with its dependencies"
    exit 1
}
MARTENWEAVE="${SMOKE_DIR}/venv/bin/martenweave"
if [[ ! -x "${MARTENWEAVE}" ]]; then
    echo "FAIL [console script] martenweave entry point missing after wheel install"
    exit 1
fi
echo "OK   [wheel install] wheel and console script installed into ${SMOKE_DIR}/venv"

echo "SMOKE martenweave start first_value.csv --no-open --json (installed wheel only)"
WORKDIR="${SMOKE_DIR}/workdir"
mkdir -p "${WORKDIR}"
cat >"${WORKDIR}/first_value.csv" <<'CSV'
customer_id,customer_group,sales_org
C10001,01,CH01
C10002,02,CH01
C10003,01,DE01
C10004,,CH01
C10005,03,DE01
CSV
cd "${WORKDIR}"
"${MARTENWEAVE}" start first_value.csv --no-open --json >start_stdout.json || {
    echo "FAIL [start command] martenweave start exited non-zero"
    cat start_stdout.json
    exit 1
}
WORKSPACE="${WORKDIR}/first_value-martenweave-workspace"

echo "SMOKE verify persisted result surfaces from the start run"
"${VENV_PY}" "${SCRIPT_DIR}/release_smoke_wheel_first_value.py" check-start \
    --workspace "${WORKSPACE}" \
    --stdout-json start_stdout.json

echo "SMOKE verify template discovery/validation from the installed wheel"
TEMPLATE_WS="${WORKDIR}/template-workspace"
"${MARTENWEAVE}" init "${TEMPLATE_WS}" --template sap_bp_customer_migration >/dev/null || {
    echo "FAIL [template discovery/validation] martenweave init --template exited non-zero"
    exit 1
}
"${MARTENWEAVE}" validate --repo "${TEMPLATE_WS}" --json >template_validate.json || true
"${VENV_PY}" "${SCRIPT_DIR}/release_smoke_wheel_first_value.py" check-template \
    --workspace "${TEMPLATE_WS}" \
    --validate-json template_validate.json

echo "SMOKE verify wheel loader and packaged assets"
"${VENV_PY}" "${SCRIPT_DIR}/release_smoke_wheel_first_value.py" check-loader \
    --workspace "${WORKSPACE}" \
    --input-name first_value.csv

echo "SMOKE verify local API/Workbench contract for the start-created workspace"
PORT="$("${VENV_PY}" -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')"
"${MARTENWEAVE}" workbench --repo "${WORKSPACE}" --no-open --port "${PORT}" \
    >"${SMOKE_DIR}/workbench.log" 2>&1 &
WORKBENCH_PID=$!
"${VENV_PY}" "${SCRIPT_DIR}/release_smoke_wheel_first_value.py" check-api \
    --workspace "${WORKSPACE}" \
    --base-url "http://127.0.0.1:${PORT}" \
    --input-name first_value.csv || {
        echo "Workbench server log:"
        cat "${SMOKE_DIR}/workbench.log"
        exit 1
    }
kill "${WORKBENCH_PID}" 2>/dev/null || true
wait "${WORKBENCH_PID}" 2>/dev/null || true
WORKBENCH_PID=""

echo "Wheel first-value smoke passed"
