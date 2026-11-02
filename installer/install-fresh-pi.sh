#!/usr/bin/env bash
# Compatibility wrapper: old staged installer is retired. Uses consolidated stable files.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${1:---check}" in
  --check|--preflight) exec python3 "$HERE/install-v331-stable.py" --check ;;
  --install) exec python3 "$HERE/install-v331-stable.py" --install ;;
  *) echo 'Use --check or --install. Rollback: python3 installer/install-v331-stable.py --rollback BACKUP' >&2; exit 2 ;;
esac
