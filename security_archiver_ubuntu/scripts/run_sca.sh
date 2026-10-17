#!/usr/bin/env bash
# Scans two manifest-derived CycloneDX SBOMs with the independent SCA engine Grype.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
if ! command -v grype >/dev/null; then
  echo "Please install grype (see README.md)" >&2
  exit 1
fi
mkdir -p reports
{
  date -u '+Date: %Y-%m-%dT%H:%M:%SZ'
  grype version
  grype db status
} > reports/sca_environment.txt 2>&1
for v in vulnerable fixed; do
  echo "Scanning: security/sbom-${v}.cdx.json"
  grype "sbom:security/sbom-${v}.cdx.json" -o json \
    > "reports/grype_${v}.json" 2> "reports/grype_${v}.stderr"
  status=$?
  if [ "$status" -ne 0 ]; then
    echo "Grype failed for $v with status $status; inspect reports/grype_${v}.stderr" >&2
    exit "$status"
  fi
  grype "sbom:security/sbom-${v}.cdx.json" -o table \
    > "reports/grype_${v}.txt" 2>> "reports/grype_${v}.stderr"
done
python3 scripts/compare_sca.py > reports/SCA_COMPARISON.md
printf 'Done. See reports/SCA_COMPARISON.md and raw Grype JSON and text reports.\n'
