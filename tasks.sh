#!/usr/bin/env bash
# Movie Match developer tasks. Works in Git Bash on Windows, and on macOS/Linux.
#
#   ./tasks.sh install     install API and web dependencies
#   ./tasks.sh dev-api     run the API with reload
#   ./tasks.sh dev-web     run the web dev server
#   ./tasks.sh lint        lint both projects
#   ./tasks.sh test        THE PHASE GATE - lint, typecheck, build, tests
#   ./tasks.sh migrate     apply database migrations
#   ./tasks.sh doctor      check that the required tools are installed
#
# `test` stops at the first failing command, so a green run means every step passed.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API="$ROOT/services/api"
WEB="$ROOT/apps/web"

# Windows venvs put the interpreter in Scripts/, POSIX ones in bin/.
venv_python() {
  if [ -x "$API/.venv/Scripts/python.exe" ]; then
    echo "$API/.venv/Scripts/python.exe"
  elif [ -x "$API/.venv/bin/python" ]; then
    echo "$API/.venv/bin/python"
  else
    echo ""
  fi
}

# The system interpreter to build the venv with. Needs 3.12+.
# Never runs `py`, and skips anything under WindowsApps: on Windows those are aliases
# for the Python install manager, which can start downloading a Python when invoked.
system_python() {
  candidates=""
  if [ -n "${LOCALAPPDATA:-}" ]; then
    for v in 312 313; do
      candidates="$candidates $(cygpath -u "$LOCALAPPDATA" 2>/dev/null)/Programs/Python/Python$v/python.exe"
    done
  fi
  for name in python3.12 python3.13 python3 python; do
    candidates="$candidates $(command -v "$name" 2>/dev/null)"
  done
  for candidate in $candidates; do
    case "$candidate" in *WindowsApps*) continue ;; esac
    [ -x "$candidate" ] || continue
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
      echo "$candidate"
      return
    fi
  done
  echo ""
}

step() {
  printf '\n=== %s ===\n' "$1"
}

require_venv() {
  PY="$(venv_python)"
  if [ -z "$PY" ]; then
    echo "No virtualenv found. Run: ./tasks.sh install" >&2
    exit 1
  fi
}

cmd_doctor() {
  step "tool check"
  local ok=1

  local sys_py
  sys_py="$(system_python)"
  if [ -n "$sys_py" ]; then
    echo "  ok    python: $("$sys_py" --version 2>&1) ($sys_py)"
  else
    echo "  MISSING  Python 3.12+ — install from python.org, tick 'Add to PATH'"
    ok=0
  fi

  if command -v node >/dev/null 2>&1; then
    local major
    major="$(node -p 'process.versions.node.split(".")[0]')"
    if [ "$major" -ge 20 ]; then
      echo "  ok    node: $(node --version)"
    else
      echo "  OLD   node: $(node --version) — need 20 or newer"
      ok=0
    fi
  else
    echo "  MISSING  Node 20+ — install from nodejs.org"
    ok=0
  fi

  command -v npm >/dev/null 2>&1 && echo "  ok    npm: $(npm --version)" || { echo "  MISSING  npm"; ok=0; }
  command -v git >/dev/null 2>&1 && echo "  ok    git: $(git --version)" || { echo "  MISSING  git"; ok=0; }

  local venv
  venv="$(venv_python)"
  [ -n "$venv" ] && echo "  ok    virtualenv: $venv" || echo "  note  no virtualenv yet — run ./tasks.sh install"

  echo
  if [ "$ok" -eq 1 ]; then
    echo "All required tools present."
  else
    echo "Install what is marked MISSING, reopen the terminal, then run ./tasks.sh doctor again."
    exit 1
  fi
}

cmd_install() {
  local sys_py
  sys_py="$(system_python)"
  if [ -z "$sys_py" ]; then
    echo "Python 3.12+ not found. Run ./tasks.sh doctor for details." >&2
    exit 1
  fi

  step "create virtualenv ($sys_py)"
  (cd "$API" && "$sys_py" -m venv .venv)

  PY="$(venv_python)"
  step "install api dependencies"
  (cd "$API" && "$PY" -m pip install --upgrade pip && "$PY" -m pip install -e ".[dev]")

  step "install web dependencies"
  (cd "$WEB" && npm install)

  printf '\nDone. Copy the .env.example files to .env and fill them in.\n'
}

cmd_lint() {
  require_venv
  step "ruff check";        (cd "$API" && "$PY" -m ruff check .)
  step "ruff format check"; (cd "$API" && "$PY" -m ruff format --check .)
  step "eslint";            (cd "$WEB" && npm run lint)
}

cmd_test() {
  require_venv
  step "ruff check";        (cd "$API" && "$PY" -m ruff check .)
  step "ruff format check"; (cd "$API" && "$PY" -m ruff format --check .)
  step "pytest";            (cd "$API" && "$PY" -m pytest -q)
  step "eslint";            (cd "$WEB" && npm run lint)
  step "typecheck";         (cd "$WEB" && npm run typecheck)
  step "build";             (cd "$WEB" && npm run build)
  step "vitest";            (cd "$WEB" && npm test)
  printf '\nGATE PASSED - every command exited 0.\n'
}

cmd_dev_api() { require_venv; (cd "$API" && "$PY" -m uvicorn app.main:app --reload); }
cmd_dev_web() { (cd "$WEB" && npm run dev); }
cmd_migrate() { require_venv; (cd "$API" && "$PY" -m alembic upgrade head); }

case "${1:-help}" in
  doctor)  cmd_doctor ;;
  install) cmd_install ;;
  lint)    cmd_lint ;;
  test)    cmd_test ;;
  dev-api) cmd_dev_api ;;
  dev-web) cmd_dev_web ;;
  migrate) cmd_migrate ;;
  *)
    sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    ;;
esac
