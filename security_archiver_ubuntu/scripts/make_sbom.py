#!/usr/bin/env python3
"""Generate CycloneDX direct-dependency inventory from pinned CMake metadata.
This is a MANIFEST SBOM, not binary reverse engineering; see report/REPORT.md.
"""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
cmake = (root / 'CMakeLists.txt').read_text(encoding='utf-8')
assert '1.2.11' in cmake and '1.3.2' in cmake

def make(version, digest, kind):
    app_id = f'lab-archiver-{kind}'
    library_id = f'pkg:generic/zlib@{version}'
    return {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.5',
        'version': 1,
        'metadata': {
            'component': {
                'type': 'application', 'bom-ref': app_id,
                'name': 'security_archiver', 'version': f'1.0-{kind}'
            }
        },
        'components': [{
            'type': 'library', 'bom-ref': library_id,
            'name': 'zlib', 'version': version,
            'purl': library_id,
            'cpe': f'cpe:2.3:a:zlib:zlib:{version}:*:*:*:*:*:*:*',
            'hashes': [{'alg': 'SHA-256', 'content': digest}],
            'externalReferences': [{
                'type': 'distribution',
                'url': f'https://zlib.net/fossils/zlib-{version}.tar.gz'
            }]
        }],
        'dependencies': [
            {'ref': app_id, 'dependsOn': [library_id]},
            {'ref': library_id, 'dependsOn': []}
        ]
    }

for kind, version in [('vulnerable', '1.2.11'), ('fixed', '1.3.2')]:
    block = re.search(
        r'if\(LAB_FIXED\)(.*?)else\(\)(.*?)endif\(\)', cmake, re.S
    )
    if not block:
        raise RuntimeError('Cannot parse CMake version pins')
    cmake_block = block.group(1) if kind == 'fixed' else block.group(2)
    ver = re.search(r'set\(ZLIB_VERSION_PIN "([^"]+)"\)', cmake_block).group(1)
    digest = re.search(r'set\(ZLIB_SHA256 "([^"]+)"\)', cmake_block).group(1)
    if version != ver:
        raise RuntimeError('Pinned version differs from expected version')
    dest = root / 'security' / f'sbom-{kind}.cdx.json'
    dest.write_text(json.dumps(make(version, digest, kind), indent=2) + '\n', encoding='utf-8')
    print(dest.relative_to(root))
