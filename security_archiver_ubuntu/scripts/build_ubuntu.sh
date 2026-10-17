#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build-vulnerable -DCMAKE_BUILD_TYPE=Debug -DLAB_FIXED=OFF
cmake --build build-vulnerable --parallel 4
cmake -S . -B build-fixed -DCMAKE_BUILD_TYPE=Debug -DLAB_FIXED=ON
cmake --build build-fixed --parallel 4
python3 tests/test_behavior.py ./build-vulnerable/security_archiver ./build-fixed/security_archiver
