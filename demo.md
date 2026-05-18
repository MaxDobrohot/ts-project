# 🚀 Demo: TS-Engine v0.4 Pipeline

## 1. Локальная валидация
```bash
./scripts/run_full_validation_pipeline.sh
# Ожидается: 7 passed + ✅ КОНТУР ЗАКРЫТ

2. Запуск Runtime MVP
bash
python3 runtime/ts_physics_mvp.py
# Вывод: baseline Γ_t, current Γ_t+1, ΔΓ, TS-Clock, S/R/V/T

3. Neo4j-интеграция (локально)
1. Установите Neo4j Desktop или запустите:
bash
docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.20.0
2. В runtime/ts_physics_mvp.py укажите ваш пароль.
3. Запустите MVP → событие sc_coherence_001 запишется в граф.

4. Дашборд
Откройте: https://maxdobrohot.github.io/ts-project/ 
Статус: B-level snapshot (irreal time). X-метрики исключены per X_Commit_Lock. 
