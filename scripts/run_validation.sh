#!/bin/bash
cd "$(dirname "$0")/.."
mkdir -p output

echo "🔍 Layer 1–3: CoreCheck + GammaCheck + LanguageCheck..."
if python3 validator/ts_validator.py validator/config/validator_config.yaml contracts/bridges/m4_bridge_contract.yaml > output/layer1-3.log 2>&1; then
  echo "✅ Layer 1–3: PASS"
else
  echo "❌ Layer 1–3: FAIL — см. output/layer1-3.log"
  exit 1
fi

echo "🔍 Запуск D-self-play sandbox..."
if python3 validator/ts_d_sandbox.py > output/sandbox.log 2>&1; then
  echo "✅ D-sandbox: завершён"
else
  echo "❌ D-sandbox: ошибка — см. output/sandbox.log"
  exit 1
fi

echo "🔍 Layer 4: MetaCheck..."
python3 validator/ts_layer4_metacheck.py > output/layer4.log 2>&1
echo "✅ Валидация завершена! Логи в output/"
