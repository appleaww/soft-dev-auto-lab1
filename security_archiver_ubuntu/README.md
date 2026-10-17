# Security Archiver — учебный проект на C++17 для Ubuntu (7/10)

> ⚠️ Исходная версия намеренно содержит CWE-120 и CWE-22. Запускайте без sudo, только на тестовых файлах. Не используйте в реальных проектах.

Приложение сжимает файл или stdin в **формат zlib** (это не ZIP).
В исходной версии закреплена zlib **1.2.11**, в исправленной — **1.3.2**.
При обычной сборке CMake скачивает исходники конкретной версии с zlib.net/fossils/ и проверяет SHA-256.
Нужен интернет при первой сборке.

## Первые действия на Ubuntu

```bash
sudo apt update
sudo apt install -y build-essential cmake python3 unzip curl git cppcheck flawfinder pipx
# Для свежей установки pipx может потребоваться новый вход в shell
pipx ensurepath
pipx install semgrep
```

Для установки Grype см. официальные инструкции: https://github.com/anchore/grype#installation
(в Ubuntu Grype обычно не устанавливается стандартным `apt install grype`).

После распаковки архива:

```bash
cd security_archiver_ubuntu
bash scripts/build_ubuntu.sh
```

**Если пока хочешь только сборку уязвимой версии**, используй команды:

```bash
cmake -S . -B build-vulnerable -DCMAKE_BUILD_TYPE=Debug -DLAB_FIXED=OFF
cmake --build build-vulnerable --parallel 4
./build-vulnerable/security_archiver --input samples/message.txt --output test.zlib --label demo
```

Когда установлены все анализаторы, запускай:

```bash
bash scripts/run_all_ubuntu.sh
```

Тогда скрипт соберёт обе версии, проведёт тесты и запускает 3 SAST (Cppcheck, Semgrep, Flawfinder) и 1 SCA (Grype), сохраняя отчёты в `reports/`.

Сканирование SBOM — это проверка известных уязвимостей в зависимостях; наличие правильной версии в SBOM само по себе не гарантирует, что Grype обнаружит конкретную CVE. Нужно приложить фактический вывод.

## Критерии и цель 7/10

- SAST №1: Cppcheck.
- SAST №2: Semgrep (локальные учебные правила `security/semgrep.yml`).
- SAST №3: Flawfinder.
- SCA: Grype + две SBOM CycloneDX.
- Намеренные дефекты: CWE-120 и CWE-22, обновление zlib 1.2.11 до 1.3.2, сравнение до/после.
- OWASP, БДУ ФСТЭК и анализ TP/FP/FN — в `report/REPORT.md`. Итог надо дополнить фактическими отчётами сканирования.

## Ручной запуск

```sh
./build-vulnerable/security_archiver --input samples/message.txt --output sample.zlib --label demo
printf 'Hello from stdin\n' | ./build-vulnerable/security_archiver --output stdin.zlib
./build-fixed/security_archiver --input samples/message.txt --output fixed.zlib --label demo
python3 -c 'from pathlib import Path; import zlib; print(zlib.decompress(Path("output/sample.zlib").read_bytes()).decode())'
```

Каждый архиватор печатает используемую версию zlib. Соответствие `1.2.11`/`1.3.2` принципиально для отчёта SCA; не подменяйте их системной библиотекой.

## Отдельные анализы и команды (их надо сохранить для сдачи)

```sh
bash scripts/run_sast.sh
bash scripts/run_sca.sh
cppcheck --version && semgrep --version && flawfinder --version && grype version
```

Проверка наличия CVE в фактическом JSON Grype:

```sh
python3 - <<'PY'
import json
for version in ['vulnerable', 'fixed']:
    x = json.load(open(f'reports/grype_{version}.json'))
    found = [m['vulnerability']['id'] for m in x.get('matches', [])]
    print(version, 'CVE-2018-25032' in found, len(found))
PY
```

> **Важно о точности:** Grype не обязан находить эту CVE при каждой версии базы/конфигурации. В таком случае следует писать «CVE подтверждена NVD, SCA вернул FN/не сопоставил компонент» и приложить сырые отчёты. Нельзя писать, что SCA её нашёл, если в JSON её нет.

## Структура

```text
security_archiver_7of10_macos/
├── CMakeLists.txt                   # выбор источника с зафиксированным SHA-256
├── src_common/archiver.{hpp,cpp}   # ввод и сжатие через zlib
├── src_vulnerable/main.cpp         # CWE-120 + CWE-22
├── src_fixed/main.cpp              # исправления, безопасная запись
├── samples/message.txt
├── security/semgrep.yml            # пользовательские SAST-правила
├── security/sbom-vulnerable.cdx.json
├── security/sbom-fixed.cdx.json
├── scripts/build_ubuntu.sh
├── scripts/run_sast.sh
├── scripts/run_sca.sh
├── scripts/run_all_ubuntu.sh
├── scripts/make_sbom.py
├── scripts/compare_sast.py
├── scripts/compare_sca.py
├── tests/test_behavior.py
├── reports/                        # заполняется при запуске
└── report/REPORT.md                # заготовка сдаваемого отчёта
```

## Что нужно приложить преподавателю

1. Этот проект в исходной и исправленной версии (в одном ZIP), промпт и название модели из `report/REPORT.md` — при желании замените формулировку промпта точной исходной.
2. `reports/` после локальных запусков на вашем Mac: `sast_environment.txt`, `sca_environment.txt`, все `*.json`, `*.xml`, `*.txt`, сравнения `*.md`, логи сборки и тестов.
3. `report/REPORT.md` с вашей интерпретацией реальных находок TP/FP/FN, привязкой к OWASP/БДУ; SBOM `security/*.cdx.json`.

**Проверено автором примера:** исходники обеих версий компилируются, выполняют сжатие и распаковку с системной zlib на Linux (offline-тест). **Не проверено здесь:** CMake-загрузка закреплённых архивов, сборка под macOS, запуски Semgrep/Cppcheck/Flawfinder/Grype; пользователь должен выполнить команды на Ubuntu. Выводы о результатах таких сканирований заранее не выдуманы.
