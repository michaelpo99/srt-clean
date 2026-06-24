#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${HOME}/.venvs/srt-clean"
WRAPPER_DIR="${HOME}/bin"
WRAPPER_PATH="${WRAPPER_DIR}/srt-clean"
TRANSLATE_WRAPPER_PATH="${WRAPPER_DIR}/translate-with-ollama"
INSTALL_TARGET="."
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev)
      INSTALL_TARGET=".[dev]"
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    *)
      echo "error: unknown option: $1" >&2
      echo "usage: bash scripts/install.sh [--dev] [--force]" >&2
      exit 2
      ;;
  esac
done

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "error: python executable not found: $PYTHON_BIN" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 12):
    raise SystemExit("error: Python >= 3.12 is required")
PY

if [[ "$FORCE" -eq 1 && -d "$VENV_DIR" ]]; then
  rm -rf "$VENV_DIR"
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install -U pip setuptools wheel
pip install -e "${REPO_ROOT}${INSTALL_TARGET#.}"

mkdir -p "$WRAPPER_DIR"
cat >"$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "\$HOME/.venvs/srt-clean/bin/srt-clean" "\$@"
EOF
chmod +x "$WRAPPER_PATH"

cat >"$TRANSLATE_WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec bash "${REPO_ROOT}/bin/translate-with-ollama" "\$@"
EOF
chmod +x "$TRANSLATE_WRAPPER_PATH"

"$WRAPPER_PATH" --help >/dev/null
"$WRAPPER_PATH" --list-profiles >/dev/null
"$TRANSLATE_WRAPPER_PATH" --help >/dev/null

case ":${PATH}:" in
  *":${WRAPPER_DIR}:"*) ;;
  *)
    echo "warning: ${WRAPPER_DIR} is not in PATH" >&2
    ;;
esac

echo "installed srt-clean to ${VENV_DIR}"
echo "wrapper: ${WRAPPER_PATH}"
echo "wrapper: ${TRANSLATE_WRAPPER_PATH}"
