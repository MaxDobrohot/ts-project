#!/usr/bin/env python3
# runtime/ts_physics_mvp.py — TS-Graph v0.4 (ΔΓ Pipeline + Neo4j 5.x ready)
# Домен: TS-Physics_2.0 (Сверхпроводимость)

import os, json, yaml
from datetime import datetime, timezone

try:
    from neo4j import GraphDatabase, basic_auth
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

DOMAIN_ID = "physics_2.0"
BASE_KVS = "1.1"

def load_act_config():
    path = f"contracts/domains/TS-Physics_2.0/subacts/superconductivity_2.1.yaml"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"status": "template", "note": "Subact not found"}

def compute_delta_gamma(baseline, current):
    """T_HP.1: ΔΓ = Γ_{t+1} − Γ_t. Блокируется, если статус ≠ validated"""
    return round(current - baseline, 4)

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
    print(f"🔬 TS-Graph v0.4 (ΔΓ Pipeline)")
    config = load_act_config()
    status = config.get("status", "template")
    print(f"📋 Акт: superconductivity_2.1 | Статус: {status}")

    # 🔒 Блокировка ΔΓ на невалидированных актах (T_HP + R1)
    if status != "validated":
        print("⚠️  Расчёт ΔΓ заблокирован. Требуется status: 'validated' и прогон R1→R2→R3.")
        print("📜 После валидации: baseline_gamma фиксируется, ΔΓ вычисляется на causal_window.")
        return

    # 📊 Метрики (в продакшене берутся из TS-Optimizer / Neo4j)
    baseline_gamma = 0.0
    current_gamma = 0.645
    delta = compute_delta_gamma(baseline_gamma, current_gamma)
    epsilon = 0.375
    valid = delta > epsilon
    ts_clock = f"τ_{DOMAIN_ID}_001"

    print(f"📊 Γ_t: {baseline_gamma:.3f} → Γ_t+1: {current_gamma:.3f}")
    print(f"📊 ΔΓ: {delta:.3f} | ε: {epsilon:.3f} | Valid: {valid}")
    print(f"🏷️  TS-Clock: {ts_clock} | S: 0.85 | R: 0.92")

    # 💾 Запись в Neo4j (если доступен)
    if HAS_NEO4J:
        try:
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "password"))
            driver.verify_connectivity()
            saved_id = write_to_neo4j(driver, "sc_coherence_001", {
                "event_id": "sc_coherence_001",
                "baseline": baseline_gamma,
                "current": current_gamma,
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

    # 📦 Сохранение отчёта
    report = {"domain": DOMAIN_ID, "delta_gamma": delta, "epsilon": epsilon, "valid": valid, "ts_clock": ts_clock}
    os.makedirs("output", exist_ok=True)
    with open("output/delta_gamma_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("💾 Отчёт: output/delta_gamma_report.json")

if __name__ == "__main__":
    main()
