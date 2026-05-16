#!/bin/bash
set -e
cd "$(dirname "$0")/.."
if [ -d "venv" ]; then
    source venv/bin/activate
fi
echo "🔍 Запуск TS-Validator (pytest v1.4)..."
python -m pytest tests/test_validator.py -v --tb=short
echo "✅ КОНТУР ЗАКРЫТ. Все слои прошли конституционную валидацию."
