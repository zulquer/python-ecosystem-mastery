#!/usr/bin/env python3
"""
================================================================================
LAB 01: CPYTHON RUNTIME, GIL, MEMORY & CONCURRENCY COMPARISON
================================================================================
Demuestra a nivel Senior:
1. Desensamblado de Bytecode de CPython (eval loop y opcode dispatch).
2. Modelo de Memoria: Conteo de Referencias (Reference Counting) vs Ciclos con GC.
3. El Impacto Real del GIL (Global Interpreter Lock):
   - CPU-bound con Threading (serializado por GIL) vs Multiprocessing (paralelo real).
   - I/O-bound cooperativo con Asyncio.
================================================================================
"""

import dis
import sys
import gc
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Funciones y clases a nivel de módulo (necesario para serialización/pickle en Multiprocessing)
def calculate_tax(amount: float) -> float:
    rate = 0.21
    total = amount * (1.0 + rate)
    return total

class Node:
    def __init__(self, name: str):
        self.name = name
        self.reference = None

def cpu_heavy_task(n: int) -> int:
    """Simula carga pura de CPU que requiere adquirir el GIL constantemente."""
    count = 0
    for i in range(n):
        count += i * i
    return count

async def async_io_task(task_id: int, delay_s: float):
    await asyncio.sleep(delay_s)
    return f"Task-{task_id} completed"

def main():
    print("=" * 80)
    print("🧪 [1/3] CPYTHON BYTECODE DISASSEMBLY: INSTRUCCIONES OP_CODE EN VIRTUAL MACHINE")
    print("=" * 80)

    print("\nDesensamblado de calculate_tax() via modulo `dis`:")
    dis.dis(calculate_tax)

    print("\n" + "=" * 80)
    print("🧠 [2/3] MODELO DE MEMORIA: REFERENCE COUNTING VS CYCLIC GARBAGE COLLECTION")
    print("=" * 80)

    # 1. Reference counting lineal
    obj = Node("Data-Block-Alpha")
    print(f"Objeto creado. Conteo de referencias inicial (sys.getrefcount): {sys.getrefcount(obj) - 1}")
    alias_1 = obj
    print(f"Tras alias_1 = obj -> Conteo de referencias: {sys.getrefcount(obj) - 1}")
    del alias_1
    print(f"Tras del alias_1  -> Conteo de referencias: {sys.getrefcount(obj) - 1}")

    # 2. Ciclo de referencia (no recolectable solo por refcount)
    node_a = Node("A")
    node_b = Node("B")
    node_a.reference = node_b
    node_b.reference = node_a

    print(f"\nCiclo creado entre Node(A) y Node(B).")
    print(f"Node A refcount: {sys.getrefcount(node_a) - 1}, Node B refcount: {sys.getrefcount(node_b) - 1}")

    # Forzar recolección cíclica
    del node_a
    del node_b
    unreachable_count = gc.collect()
    print(f"Objetos inalcanzables detectados y limpiados por el GC cíclico de CPython: {unreachable_count}")

    print("\n" + "=" * 80)
    print("⚡ [3/3] EL DILEMA DEL GIL: THREADS (SERIALIZADOS) VS PROCESSES (TRUE MULTI-CORE)")
    print("=" * 80)

    ITERATIONS = 4_000_000
    TASKS = 2

    # 1. Ejecución Secuencial
    t0 = time.perf_counter()
    cpu_heavy_task(ITERATIONS)
    cpu_heavy_task(ITERATIONS)
    t_seq = time.perf_counter() - t0
    print(f"⏱️ 1. Secuencial (1 Core):              {t_seq:.3f} s")

    # 2. Ejecución con Threads (Limitado por el GIL de CPython)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=TASKS) as executor:
        list(executor.map(cpu_heavy_task, [ITERATIONS] * TASKS))
    t_threads = time.perf_counter() - t0
    print(f"⏱️ 2. ThreadPoolExecutor ({TASKS} Threads):     {t_threads:.3f} s  ⚠️ (El GIL serializa la CPU)")

    # 3. Ejecución con Procesos (Cada proceso tiene su propio CPython y GIL independiente)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=TASKS) as executor:
        list(executor.map(cpu_heavy_task, [ITERATIONS] * TASKS))
    t_proc = time.perf_counter() - t0
    speedup = t_threads / max(t_proc, 0.001)
    print(f"⏱️ 3. ProcessPoolExecutor ({TASKS} Procesos):   {t_proc:.3f} s  ✅ (Multi-Core Real: ~{speedup:.1f}x más rápido)")

    # 4. Asincronía para I/O-bound (asyncio)
    async def run_async_demo():
        t0 = time.perf_counter()
        await asyncio.gather(
            async_io_task(1, 0.1),
            async_io_task(2, 0.1),
            async_io_task(3, 0.1)
        )
        t_async = time.perf_counter() - t0
        print(f"\n🌐 4. Asyncio Cooperativo (I/O-Bound):   {t_async:.3f} s (3 tareas concurrentes de 100ms resueltas a la vez)")

    asyncio.run(run_async_demo())

    print("\n" + "=" * 80)
    print("🎯 CONCLUSIÓN SENIOR CPYTHON:")
    print("- Para CPU-bound: Usar multiprocessing o extensiones C/Rust (PyO3).")
    print("- Para I/O-bound masivo: Usar asyncio (FastAPI, aiohttp).")
    print("- En Python 3.13+: Se introduce el modo experimental Free-Threaded (PEP 703) sin GIL.")
    print("=" * 80)

if __name__ == '__main__':
    main()
