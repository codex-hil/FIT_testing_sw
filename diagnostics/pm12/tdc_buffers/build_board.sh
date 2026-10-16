#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 prepare_board.py
export PYTHONPATH="${FIT_LITEX_ROOT:-/home/codex-hil/fit-bringup/sources/litex-eth-check}:${FIT_LITEETH_ROOT:-/home/codex-hil/fit-bringup/sources/liteeth-eth-check}:${FIT_LITEICLINK_ROOT:-/home/codex-hil/fit-bringup/sources/liteiclink-eth-check}${PYTHONPATH:+:$PYTHONPATH}"
cd generated/board
"${FIT_HDL_PYTHON:-/srv/codex-hil-data/artiq-zynqmp/venv/bin/python}" generate.py
vivado -mode batch -source build.tcl
python3 ../../tools/summarize_build.py
mkdir -p ../audit
cd ../audit
vivado -mode batch -source ../../tools/audit_routed.tcl
