#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${HOME}/.venvs/srt-clean"
WRAPPER_PATH="${HOME}/bin/srt-clean"
TRANSLATE_WRAPPER_PATH="${HOME}/bin/translate-with-ollama"
ASSUME_YES=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes)
      ASSUME_YES=1
      shift
      ;;
    *)
      echo "error: unknown option: $1" >&2
      echo "usage: bash scripts/uninstall.sh [--yes]" >&2
      exit 2
      ;;
  esac
done

rm -f "$WRAPPER_PATH"
rm -f "$TRANSLATE_WRAPPER_PATH"

if [[ -d "$VENV_DIR" ]]; then
  if [[ "$ASSUME_YES" -eq 1 ]]; then
    rm -rf "$VENV_DIR"
  else
    read -r -p "Remove ${VENV_DIR}? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
      rm -rf "$VENV_DIR"
    fi
  fi
fi

echo "uninstalled srt-clean wrapper from ${WRAPPER_PATH}"
echo "uninstalled translate-with-ollama wrapper from ${TRANSLATE_WRAPPER_PATH}"
