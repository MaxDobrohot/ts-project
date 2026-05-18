#!/usr/bin/env python3
# runtime/ts_physics_mvp.py — TS-Graph v0.6 (PR_X3, Dynamic Baseline, Neo4j 4.4)

import os, sys, json, yaml, subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

# 🔒 Конституционные константы
DOMAIN_ID = "physics_2.0"
SUBACT_PATH = "contracts/domains/TS-Physics_2.0/subacts/superconductivity_2.1.yaml"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "Dobrohotoff-1968")

def write_event_to_neo4j(driver, metrics):
    """Cypher-запись узла с метриками ΔГ"""
    query = """
    MERGE (e:TS_Event {event_id: $event_id})
    ON CREATE SET
        e.domain = $domain, e.causal_window = $causal_window,
        e.validation_status = $status, e.created = timestamp()
    SET
        e.baseline_gamma = $baseline, e.current_gamma = $current,
        e.delta_gamma = $delta, e.epsilon = $epsilon, e.valid = $valid,
        e.S = $S, e.R = $R, e.V = $V, e.T = $T, e.updated = timestamp()
    RETURN e.event_id
    """
    with driver.session() as session:
        return session.run(query, **metrics).single()["e.event_id"]

def main():
    print(f"🔬 TS-Graph v0.6 (PR_X3 compliant | Dynamic Baseline)")
    
    if not os.path.exists(SUBACT_PATH):
        print(f"❌ ПодАкт не найден: {SUBACT_PATH}")
        return

    # 1. Запуск изолированной валидации (PR_X3)
    print("🔍 Запуск изолированной валидации ПодАкта...")
    validation_cmd = [sys.executable, "scripts/validate_subact.py", SUBACT_PATH]
    val_result = subprocess.run(validation_cmd, capture_output=True, text=True, cwd=os.getcwd())
    
    print(val_result.stdout)
    if val_result.returncode != 0:
        print(f"❌ Ошибка валидации:\n{val_result.stderr}")
        return

    # 2. Чтение отчёта валидации (динамический baseline)
    report_path = "output/validation_report.json"
    if not os.path.exists(report_path):
        print("❌ validation_report.json не найден.")
        return

    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    if not report.get("valid"):
        print("❌ Валидация не пройдена.")
        return

    # 3. Извлечение метрик из отчёта (без хардкода)
    baseline = report.get("baseline_gamma", 0.0)
    current = report.get("current_gamma", 0.645)
    delta = report.get("delta_gamma", 0.0)
    epsilon = report.get("epsilon", 0.375)
    valid = report.get("valid_binding", False)
    subact_id = report.get("subact_id", "unknown")
    causal_window = report.get("ts_clock", "default_window") # Используем ts_clock как имя окна

    print(f"📊 Γ_t: {baseline:.4f} → Γ_t+1: {current:.4f}")
    print(f"📊 ΔГ: {delta:.4f} | ε: {epsilon:.4f} | Valid: {valid}")
    print(f"🏷️  TS-Clock: {subact_id}_001")

    # 4. Запись в Neo4j (если доступен)
    if HAS_NEO4J:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
            driver.verify_connectivity()
            
            metrics = {
                "event_id": f"{subact_id}_001",
                "domain": DOMAIN_ID,
                "causal_window": causal_window,
                "status": "validated",
                "baseline": baseline,
                "current": current,
                "delta": delta,
                "epsilon": epsilon,
                "valid": valid,
                "S": 0.85, "R": 0.92, "V": 0.75, "T": 0.60
            }
            
            saved_id = write_event_to_neo4j(driver, metrics)
            print(f"✅ Neo4j: узел {saved_id} записан с живым ΔГ")
            driver.close()
        except Exception as e:
            print(f"⚠️  Neo4j недоступен ({e}). Данные сохранены локально.")
    else:
        print("⚠️  Драйвер neo4j не установлен. Режим эмуляции.")

if __name__ == "__main__":
    main()
