#!/usr/bin/env python3
"""Functional tests for both builds (safe test cases only; no overflow exploit)."""
from pathlib import Path
import subprocess
import os
import sys
import tempfile
import zlib


def run(binary, directory, args, input_bytes=None):
    return subprocess.run([str(binary), *args], input=input_bytes, cwd=directory,
                          capture_output=True, check=False)


def check(binary, expected_version, fixed):
    data = b'hello from security lab\n' * 200
    with tempfile.TemporaryDirectory(prefix='security-archiver-') as d:
        root = Path(d)
        input_path = root / 'input.bin'
        input_path.write_bytes(data)
        p = run(binary, root, ['--input', str(input_path), '--output', 'file.zlib', '--label', 'ok'])
        assert p.returncode == 0, p.stderr.decode(errors='replace')
        assert f'zlib version: {expected_version}'.encode() in p.stdout, p.stdout
        assert zlib.decompress((root / 'output/file.zlib').read_bytes()) == data
        p = run(binary, root, ['--output', 'stdin.zlib'], input_bytes=data)
        assert p.returncode == 0, p.stderr.decode(errors='replace')
        assert zlib.decompress((root / 'output/stdin.zlib').read_bytes()) == data
        # This path stays entirely inside the disposable temporary directory.
        p = run(binary, root, ['--input', str(input_path), '--output', '../escaped.zlib'])
        assert (p.returncode != 0) == fixed, (p.returncode, p.stderr)
        assert (root / 'escaped.zlib').exists() != fixed
        if fixed:
            # The fixed version must not follow a symlink inside output/.
            outside = root / 'outside.zlib'
            (root / 'output/link.zlib').symlink_to(outside)
            symlink_result = run(binary, root, ['--input', str(input_path), '--output', 'link.zlib'])
            assert symlink_result.returncode != 0 and not outside.exists()
            long_label_result = run(binary, root, ['--input', str(input_path), '--label', 'X'*1000])
            assert long_label_result.returncode == 0
        print(f'PASS: {binary.name}, zlib {expected_version}, fixed={fixed}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: test_behavior.py /abs/path/vulnerable /abs/path/fixed')
    if os.environ.get('LAB_TEST_SYSTEM_ZLIB') == '1':
        # OFFLINE core-logic test only; NOT evidence for the pinned-version SCA.
        versions = (zlib.ZLIB_RUNTIME_VERSION, zlib.ZLIB_RUNTIME_VERSION)
    else:
        versions = ('1.2.11', '1.3.2')
    check(Path(sys.argv[1]).resolve(), versions[0], False)
    check(Path(sys.argv[2]).resolve(), versions[1], True)
