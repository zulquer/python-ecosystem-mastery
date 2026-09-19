#!/usr/bin/env python3
"""
================================================================================
LAB 03: PYSPARK INTERNALS, SHUFFLE BOTTLENECK & CATALYST OPTIMIZER
================================================================================
Demuestra a nivel Senior:
1. Arquitectura Spark: Driver Node vs Cluster Executors.
2. Dependencias Estrechas (Narrow) vs Dependencias Anchas (Wide / Shuffle):
   - Narrow: map(), filter() -> Ejecución en memoria local de cada partición (0 red).
   - Wide: groupByKey(), join() -> Requiere Network Shuffle, serialización y disco.
3. El Optimizador Catalyst: Predicate Pushdown (empujar filtros antes de mover datos).
================================================================================
"""

from typing import List, Dict, Tuple
from collections import defaultdict

print("=" * 80)
print("⚡ [1/2] NARROW DEPENDENCIES VS WIDE DEPENDENCIES (NETWORK SHUFFLE)")
print("=" * 80)

# Simulación de un DataFrame distribuido particionado en 2 Executors
partition_0 = [
    {"user_id": "u1", "country": "ES", "amount": 120.0},
    {"user_id": "u2", "country": "US", "amount": 340.0},
    {"user_id": "u3", "country": "ES", "amount": 50.0},
]

partition_1 = [
    {"user_id": "u4", "country": "ES", "amount": 210.0},
    {"user_id": "u5", "country": "FR", "amount": 80.0},
    {"user_id": "u6", "country": "US", "amount": 95.0},
]

cluster_dataset = [partition_0, partition_1]

# 1. Narrow Transformation: filter() en cada partición sin transferir datos por la red
print("\n1. Transformación Estrecha (Narrow: filter amount >= 100):")
filtered_partitions = []
for i, part in enumerate(cluster_dataset):
    filtered = [row for row in part if row["amount"] >= 100]
    filtered_partitions.append(filtered)
    print(f"   [Executor-{i}] Procesó {len(part)} filas -> Mantiene {len(filtered)} filas (0 bytes de red transferidos)")

# 2. Wide Transformation: groupByKey(country) -> Requiere SHUFFLE entre nodos
print("\n2. Transformación Ancha (Wide: groupBy 'country' con cálculo de suma):")
print("   ⚠️ BARRERA DE SHUFFLE: Los datos deben redistribuirse por la red para que las mismas claves")
print("      caigan en el mismo Executor...")

shuffle_network_transfers = 0
buckets = defaultdict(list)

for part_idx, part in enumerate(filtered_partitions):
    for row in part:
        key = row["country"]
        target_executor = hash(key) % 2
        if target_executor != part_idx:
            shuffle_network_transfers += 1
            print(f"   🌐 [RED] Fila {row['user_id']} ({key}) viaja de Executor-{part_idx} -> Executor-{target_executor}")
        buckets[key].append(row["amount"])

# Agregación en memoria de destino
results = {country: sum(amounts) for country, amounts in buckets.items()}
print(f"\n   Totales agregados post-shuffle: {results}")
print(f"   Total de registros transferidos por red durante el Shuffle: {shuffle_network_transfers}")

print("\n" + "=" * 80)
print("🧠 [2/2] CATALYST OPTIMIZER: PREDICATE PUSHDOWN SIMULATION")
print("=" * 80)

query = "SELECT country, sum(amount) FROM dataset WHERE country = 'ES' GROUP BY country"
print(f"Consulta SQL lógica: {query}\n")

print("Sin optimización (Ingeniero Junior):")
print("1. Leer todo el dataset de disco.")
print("2. Hacer el Shuffle de todos los países.")
print("3. Filtrar country = 'ES' al final.")
print("-> Coste: Transferir el 100% de los datos por red.\n")

print("Con Catalyst Optimizer / Predicate Pushdown (Ingeniero Senior / Staff):")
print("1. El optimizador detecta el filtro `country = 'ES'`.")
print("2. Empuja el filtro directamente al lector de Parquet/Delta Lake en cada Executor.")
print("3. Solo se leen las particiones 'ES' y se elimina el 70%+ del tráfico de Shuffle.")

print("\n" + "=" * 80)
print("🎯 INTEGRACIÓN CON CURSO-PYSPARK DEL WORKSPACE:")
print("- Este track formaliza la arquitectura interna (Catalyst, Tungsten engine, RDD lineage, DAG scheduler).")
print("- Se complementa con las prácticas aplicadas en tu carpeta local `curso-pyspark`.")
print("=" * 80)
