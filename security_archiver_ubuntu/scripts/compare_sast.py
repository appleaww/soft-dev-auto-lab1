#!/usr/bin/env python3
"""Summarise whether scanners actually emitted a diagnostic for known lab sites.
NOT a replacement for manual TP/FP review; all raw reports are preserved.
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parent.parent
reports = root / 'reports'


def get_semgrep(kind):
    file = reports / f'semgrep_{kind}.json'
    if not file.exists():
        return None
    try:
        findings = json.loads(file.read_text()).get('results', [])
        ids = [r.get('check_id', '') for r in findings]
        return ('yes' if any('cwe120-' in x for x in ids) else 'no',
                'yes' if any('cwe22-' in x for x in ids) else 'no',
                len(findings))
    except (ValueError, TypeError):
        return None


def get_cppcheck(kind):
    file = reports / f'cppcheck_{kind}.xml'
    if not file.exists():
        return None
    try:
        errors = ET.fromstring(file.read_text()).findall('.//error')
        # A cppcheck report is a TP for a known location only if the line matches.
        main = (root / f'src_{kind}' / 'main.cpp').read_text().splitlines()
        targets = {
            'memory': {i for i, s in enumerate(main, 1) if 'std::strcpy(label, argv' in s},
            'path': {i for i, s in enumerate(main, 1) if 'fs::path("output") / output_file' in s}
        }
        matched = {'memory': False, 'path': False}
        for e in errors:
            for loc in e.findall('location'):
                if not loc.attrib.get('file', '').endswith(f'src_{kind}/main.cpp'):
                    continue
                line = int(loc.get('line', 0))
                for key in matched:
                    if line in targets[key]:
                        matched[key] = True
        return ('yes' if matched['memory'] else 'no',
                'yes' if matched['path'] else 'no', len(errors))
    except (ValueError, ET.ParseError):
        return None


def get_flawfinder(kind):
    file = reports / f'flawfinder_{kind}.txt'
    if not file.exists():
        return None
    text = file.read_text(errors='replace')
    # Presence of an explicit source-location warning is evidence only, not TP verdict.
    memory = bool(re.search(r'src_'+kind+r'/main\.cpp:\d+.*\bstrcpy\b', text, re.I))
    path = bool(re.search(r'src_'+kind+r'/main\.cpp:\d+.*\b(?:path traversal|directory traversal)\b', text, re.I))
    return ('yes' if memory else 'no', 'yes' if path else 'no', len(text.splitlines()))

print('# Сравнение SAST по фактическим файлам отчётов\n')
print('«yes» означает **есть диагностическое сообщение в соответствующем месте**, а не автоматическое доказательство уязвимости.')
print('«no» означает, что сканер не сообщил о конкретной намеренной ошибке (кандидат FN).\n')
print('| Версия | Анализатор | CWE-120 (strcpy) | CWE-22 (output path) | Всего записей/строк |')
print('|---|---|---|---|---:|')
for kind in ['vulnerable', 'fixed']:
    for label, method in [('Semgrep (локальные правила)', get_semgrep), ('Cppcheck', get_cppcheck), ('Flawfinder', get_flawfinder)]:
        val = method(kind)
        print(f'| {kind} | {label} | {val[0] if val else "не запускался/ошибка"} | '
              f'{val[1] if val else "не запускался/ошибка"} | {val[2] if val else "—"} |')
print('\nДля FP/FN откройте сырые отчёты и подтвердите путь, строку, поток данных и исправление. '
      'Количество строк Flawfinder не равно количеству находок. Результат SAST не доказывает отсутствие других ошибок.')
