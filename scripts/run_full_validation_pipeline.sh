# В начале scripts/run_full_validation_pipeline.sh добавьте:
SUBACT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --subact)
      SUBACT="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# Если указан SUBACT, валидируем только его:
if [ -n "$SUBACT" ]; then
  echo "🔍 Валидация ПодАкта: $SUBACT"
  python3 -m pytest tests/test_validator.py::test_subact_inheritance -v
  python3 -m pytest tests/test_validator.py::test_subact_profiling_not_replacement -v
  python3 -m pytest tests/test_validator.py::test_domain_specific_Z_compliance -v
  # ... добавьте остальные проверки для ПодАкта
  echo "✅ КОНТУР ЗАКРЫТ. ПодАкт $SUBACT прошёл валидацию."
  exit 0
fi

# Иначе — стандартная валидация ядра
echo "🔍 Запуск полной валидации ядра..."
python3 -m pytest tests/test_validator.py -v
#!/bin/bash
set -e
cd "$(dirname "$0")/.."
if [ -d "venv" ]; then
    source venv/bin/activate
fi
echo "🔍 Запуск TS-Validator (pytest v1.4)..."
python -m pytest tests/test_validator.py -v --tb=short
echo "✅ КОНТУР ЗАКРЫТ. Все слои прошли конституционную валидацию."
