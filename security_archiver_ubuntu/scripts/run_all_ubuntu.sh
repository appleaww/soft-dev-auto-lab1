#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports
bash scripts/build_ubuntu.sh 2>&1 | tee reports/build_and_tests.log
bash scripts/run_sast.sh 2>&1 | tee reports/sast_run.log
bash scripts/run_sca.sh 2>&1 | tee reports/sca_run.log
printf '\nFinish: open reports/COMPARISON.md, reports/SCA_COMPARISON.md, report/REPORT.md\n'
