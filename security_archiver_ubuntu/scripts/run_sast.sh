#!/usr/bin/env bash
# Three INDEPENDENT engines, each run on both versions; raw output is retained.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
mkdir -p reports
{
  printf 'Date: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'Host: %s\n' "$(uname -a)"
  printf 'cppcheck: '; cppcheck --version
  printf 'semgrep: '; semgrep --version
  printf 'flawfinder: '; flawfinder --version
} > reports/sast_environment.txt 2>&1

if ! command -v cppcheck >/dev/null || ! command -v semgrep >/dev/null || ! command -v flawfinder >/dev/null; then
  echo "Please install cppcheck, semgrep, flawfinder (see README.md)" >&2
  exit 1
fi

for v in vulnerable fixed; do
  main_folder="src_${v}"
  printf '\n== Scan %s ==\n' "$v"
  # Tool 1: Semgrep, with explicit local training rules.
  semgrep scan --config security/semgrep.yml --json "$main_folder" src_common \
    > "reports/semgrep_${v}.json" 2> "reports/semgrep_${v}.stderr"
  printf 'Semgrep status: %s\n' "$?"
  # Tool 2: Cppcheck. Diagnostic messages are XML on stderr.
  cppcheck --enable=all --inconclusive --std=c++17 --xml --xml-version=2 \
    --suppress=missingIncludeSystem "$main_folder" src_common \
    > "reports/cppcheck_${v}.stdout" 2> "reports/cppcheck_${v}.xml"
  printf 'Cppcheck status: %s\n' "$?"
  # Tool 3: Flawfinder. Purely heuristic, so false positives are normal.
  flawfinder --dataonly --minlevel=1 "$main_folder" src_common \
    > "reports/flawfinder_${v}.txt" 2> "reports/flawfinder_${v}.stderr"
  printf 'Flawfinder status: %s\n' "$?"
done
python3 scripts/compare_sast.py > reports/COMPARISON.md
printf '\nReports: reports/ (including COMPARISON.md)\n'
