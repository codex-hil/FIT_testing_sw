#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Serial-only portable simulation. See Python runner for explicit startup model.
exec python3 test_receiver_ghdl.py --ghdl "${GHDL:-ghdl}"
