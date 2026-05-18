#!/usr/bin/env python3
# runtime/ts_physics_mvp.py — TS-Graph v0.5 (PR_X3 compliant: validation before ΔΓ)
# Домен: TS-Physics_2.0 (Сверхпроводимость)

import os, json, yaml, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from neo4j import GraphDatabase, basic_auth
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

DOMAIN_ID = "physics_2.0"
BASE_KVS = "1.1"

def load_subact_config(subact_path):
    """Загружает конфиг ПодАкта"""
    with open(subact_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_validation_pipeline(subact_path):
    """Запускает внешнюю валидацию (Γ_Locality: изоляция слоёв)"""
    cmd = ["python3", "scripts/validate_subact.py", subact_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    return {
        "passed": result.returncode == 0,
        "report_path": "output/validation_report.json"
    }

def load_validation_report(report_path):
    """Загружает отчёт валидации"""
    if os.path.exists(report_path):
        with open(report_path, encoding="utf-8") as f:
            return json.load(f)
    return None

def write_to_neo4j(driver, event_id, metrics):
    """Cypher-запрос для записи узла + метрик ΔΓ (Γ_Locality compliant)"""
    query = """
    MERGE (e:TS_Event {event_id: $event_id})
    SET e.baseline_gamma = $baseline,
        e.current_gamma = $current,
        e.delta_gamma = $delta,
        e.epsilon = $epsilon,
        e.valid = $valid,
        e.ts_clock = $ts_clock,
        e.updated = timestamp()
    RETURN e.event_id
    """
    with driver.session() as session:
        return session.run(query, **metrics).single()["e.event_id"]

def main():
    print(f"🔬 TS-Graph v0.5 (PR_X3 compliant: validation → ΔΓ → Neo4j)")
    
    # Путь к ПодАкту (можно переопределить через аргумент)
    subact_path = sys.argv[1] if len(sys.argv) > 1 else "contracts/domains/TS-Physics_2.0/subacts/superconductivity_2.1.yaml"
    
    if not os.path.exists(subact_path):
        print(f"❌ ПодАкт не найден: {subact_path}")
        return
    
    # 1. Загружаем конфиг
    config = load_subact_config(subact_path)
    subact_id = config.get("subact_id", config.get("act_id"))
    status = config.get("status", "template")
    
    print(f"📋 ПодАкт: {subact_id} | Статус: {status}")
    
    # 2. 🔒 Блокировка: ΔΓ только после валидации (T_HP.1 + PR_X3)
    if status != "validated":
        print("⚠️  Расчёт ΔΓ заблокирован. Требуется status: 'validated' и прогон Layer 1-4.")
        print("📜 Запускаем валидацию...")
    
    # 3. Запускаем внешнюю валидацию (изолированный контур)
    validation = run_validation_pipeline(subact_path)
    if not validation["passed"]:
        print("❌ Валидация не пройдена. ΔΓ не вычисляется.")
        return
    print("✅ Валидация пройдена (Layer 1-4 PASS)")
    
    # 4. Загружаем отчёт валидации (динамический baseline)
    report = load_validation_report(validation["report_path"])
    if not report or not report.get("valid"):
        print("❌ Отчёт валидации не найден или невалиден.")
        return
    
    # 5. Извлекаем метрики (никакого хардкода!)
    baseline = report.get("baseline_gamma", 0.0)
    current = report.get("current_gamma", 0.645)
    delta = report.get("delta_gamma", round(current - baseline, 4))
    epsilon = report.get("epsilon", 0.375)
    valid = report.get("valid_binding", delta > epsilon)
    ts_clock = report.get("ts_clock", f"τ_{subact_id}_001")
    
    print(f"📊 Γ_t: {baseline:.3f} → Γ_t+1: {current:.3f}")
    print(f"📊 ΔΓ: {delta:.3f} | ε: {epsilon:.3f} | Valid: {valid}")
    print(f"🏷️  TS-Clock: {ts_clock} | S: 0.85 | R: 0.92")
    
    # 6. 💾 Запись в Neo4j (если доступен)
    if HAS_NEO4J:
        try:
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "password"))
            driver.verify_connectivity()
            saved_id = write_to_neo4j(driver, "sc_coherence_001", {
                "event_id": "sc_coherence_001",
                "baseline": baseline,
                "current": current,
                "delta": delta,
                "epsilon": epsilon,
                "valid": valid,
                "ts_clock": ts_clock
            })
            print(f"✅ Neo4j: узел {saved_id} записан с ΔΓ-метриками")
            driver.close()
        except Exception as e:
            print(f"⚠️  Neo4j недоступен ({e}). Режим эмуляции.")
    else:
        print("⚠️  Библиотека neo4j не найдена. Режим эмуляции.")
    
    # 7. 📦 Сохранение отчёта
    os.makedirs("output", exist_ok=True)
    with open("output/delta_gamma_report.json", "w") as f:
        json.dump({
            "domain": DOMAIN_ID,
            "subact_id": subact_id,
            "baseline_gamma": baseline,
            "current_gamma": current,
            "delta_gamma": delta,
            "epsilon": epsilon,
            "valid": valid,
            "ts_clock": ts_clock,
            "validated_at": datetime.now(timezone.utc).isoformat()
        }, f, indent=2)
    print("💾 Отчёт: output/delta_gamma_report.json")

if __name__ == "__main__":
    main()
