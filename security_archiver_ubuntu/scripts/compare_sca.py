#!/usr/bin/env python3
import json
from pathlib import Path
root = Path(__file__).resolve().parent.parent
print('# Сравнение SCA (Grype)\n')
print('| Сборка | zlib в SBOM | Обнаружена CVE-2018-25032 | Число записей о найденных уязвимостях |')
print('|---|---|---|---:|')
for kind in ['vulnerable', 'fixed']:
    sbom = json.loads((root / 'security' / f'sbom-{kind}.cdx.json').read_text())
    version = sbom['components'][0]['version']
    path = root / 'reports' / f'grype_{kind}.json'
    if not path.exists():
        print(f'| {kind} | {version} | анализ не выполнен | — |')
        continue
    try:
        matches = json.loads(path.read_text())['matches']
        cves = [x.get('vulnerability', {}).get('id', '') for x in matches]
        detected = 'да' if 'CVE-2018-25032' in cves else 'нет (проверь базу и тип пакета)'
        print(f'| {kind} | {version} | {detected} | {len(matches)} |')
    except (ValueError, KeyError):
        print(f'| {kind} | {version} | ошибка чтения JSON | — |')
print('\nНеобнаружение CVE сканером не отменяет заключение NVD о zlib до 1.2.12. '
      'Для подтверждения исправления проверяйте реальные версии библиотек и результаты повторного анализа.')
