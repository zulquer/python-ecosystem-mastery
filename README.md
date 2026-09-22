# 🐍 Python Ecosystem & Distributed Engineering Mastery

Repositorio maestro de referencia técnica profunda para consolidar habilidades de nivel **Senior / Staff / Python Architect / Data Platform Engineer** en **CPython Internals (Bytecode, Conteo de Referencias, Ciclos GC, GIL & Concurrencia), Frameworks Modernos (FastAPI ASGI, Django ORM Internals), Procesamiento Distribuido de Datos (PySpark, Catalyst Optimizer, Shuffle) y Calidad de Código (Mypy estricto, Pytest avanzado)**.

---

## 🎯 Preguntas de Entrevista Técnica

Para preparar entrevistas técnicas de alto nivel (**Senior Python Architect, FastAPI/Django Specialist y Data Platform Engineer**), este módulo incluye la guía:

👉 **[Las 100 Preguntas Más Comunes en Entrevistas Técnicas: Python Ecosystem](./INTERVIEW-QUESTIONS.md)** (CPython Internals, GIL & Free-threading PEP 703, FastAPI ASGI, Django ORM, PySpark Catalyst/Tungsten, Pytest, con criterios 🚩 *Red Flags* vs 🟢 *Green Flags*).

---

## 🌐 The Mastery Suite (Ecosistema Modular)

| Repositorio | Especialidad Técnica | Enlace |
|---|---|---|
| **`nodejs-ecosystem-mastery`** | 🟢 **Node.js Core, V8, Libuv, Express, NestJS, Testing & TypeScript** | [Ver Repositorio](../nodejs-ecosystem-mastery/) |
| **`python-ecosystem-mastery`** | 🐍 **CPython Internals, GIL, FastAPI, Django, PySpark & Pytest** | *Este repositorio* |
| **`php-ecosystem-mastery`** | 🐘 **Zend Engine, OPcache, JIT, Laravel, Symfony, FrankenPHP & Pest** | [Ver Repositorio](../php-ecosystem-mastery/) |
| **`backend-mastery`** | 🌐 **REST APIs RFC 9110, SQL, NoSQL, Sistemas Distribuidos & Caché** | [Ver Repositorio](../backend-mastery/) |
| **`frontend-mastery`** | ⚛️ **React 19, Angular v2-v19+, Next.js App Router & Web Performance** | [Ver Repositorio](../frontend-mastery/) |
| **`cloud-mastery`** | ☁️ **Cloud Architecture (AWS, Azure, DigitalOcean), K8s, Terraform & FinOps** | [Ver Repositorio](../cloud-mastery/) |
| **`cicd-mastery`** | 🚀 **CI/CD Universal (GitHub Actions, Azure, GitLab), GitOps & Canary** | [Ver Repositorio](../cicd-mastery/) |
| **`agile-mastery`** | 🏃 **Scrum, Kanban, Ley de Little, XP (TDD/Trunk-Based) & Cynefin** | [Ver Repositorio](../agile-mastery/) |

---

## 🏛️ Organización de los Tracks

```
python-ecosystem-mastery/
├── tracks/
│   ├── 01-python-runtime-and-internals/      # CPython, Bytecode (dis), Refcount, Ciclos GC, GIL, Threads vs Multiprocessing vs Asyncio
│   ├── 02-frameworks-fastapi-and-django/     # Especificación ASGI 3.0, FastAPI Depends & Grafo DAG, Django ORM y N+1
│   ├── 03-data-and-distributed-pyspark/      # Arquitectura Spark (Driver/Executors), Narrow vs Wide Dependencies, Shuffling, Catalyst
│   └── 04-tooling-typing-and-testing/        # Tipado con Mypy estricto, Gestores (uv, poetry), Pytest (fixtures, mocks, parametrize)
├── .gitignore
├── pyproject.toml
└── package.json
```

---

## 🧠 Matriz de Diferenciación por Seniority en Python

| Dimensión | Junior | Intermediate | Senior / Staff Python Engineer |
|---|---|---|---|
| **Runtime & Memoria** | "Python no necesita gestión de memoria porque tiene Garbage Collector". | Entender qué hace un script línea a línea y evitar variables globales. | **CPython Internals**: Conocer el modelo de **Reference Counting** con campos de cabecera `ob_refcnt`, el recolector de ciclos generacionales (Gen 0, 1, 2), desensamblado de **Bytecode** (`dis`), y optimizaciones con `__slots__` para reducir overhead de `__dict__`. |
| **Concurrencia & GIL** | Usar `threading.Thread` para tareas pesadas creyendo que usa todos los núcleos del CPU. | Usar `async/await` para consultas web básicas. | **Arquitectura de Paralelismo**: Dominar el impacto del **Global Interpreter Lock (GIL)**, saber cuándo usar `multiprocessing` o extensiones C/Rust (`PyO3`) para CPU, y cuándo usar `asyncio` cooperativo para I/O masivo, además de la evolución hacia **Free-Threaded Python (PEP 703)** en Python 3.13+. |
| **Frameworks (FastAPI / Django)** | Copiar rutas sin entender middlewares ni autenticación. | Usar Pydantic básico y crear modelos Django. | **Protocolo ASGI & DI**: Diseñar dependencias reutilizables con **`Depends`** de FastAPI con gestión de recursos garantizada vía generadores `yield` (teardown), entender el ciclo de eventos ASGI (`scope`, `receive`, `send`), y mitigar cuellos de botella en Django con `select_related` / `prefetch_related`. |
| **Procesamiento de Datos (PySpark)** | Usar `collect()` en datasets de terabytes tumbando el nodo Driver de Spark por OutOfMemory. | Escribir consultas SQL básicas en Spark DataFrames. | **Arquitectura Distribuida**: Diferenciar dependencias estrechas (*Narrow*) de transformaciones que provocan **Network Shuffle** masivo (*Wide Dependencies* como `groupByKey`), optimizar la partición de datos para evitar sesgo (*Data Skew*), y comprender el optimizador **Catalyst** y **Tungsten**. |
| **Tipado & Calidad** | Código sin type hints. | Usar `int`, `str`, `List` básicos. | **Typing Estricto**: Uso de `TypeVar`, `Generic`, `Protocol` (Duck typing estructural formal), `ParamSpec`, validación estática con `mypy --strict`, y tests deterministas con `pytest` y fixtures avanzadas. |

---

## 🔬 Laboratorios Ejecutables Senior

Puedes ejecutar los laboratorios con `python3` directamente o usando los scripts de `package.json`:

```bash
# 🐍 1. CPython Runtime, GIL, Memoria y Concurrencia:
npm run py:gil:01
# o directamente:
python3 tracks/01-python-runtime-and-internals/01-cpython-gil-concurrency-and-memory.py

# 🌐 2. FastAPI Dependency Injection & ASGI Internals:
npm run py:fastapi:01
# o directamente:
python3 tracks/02-frameworks-fastapi-and-django/01-fastapi-dependency-injection-and-asgi.py

# ⚡ 3. PySpark Internals, Shuffle & Catalyst Optimizer:
npm run py:spark:01
# o directamente:
python3 tracks/03-data-and-distributed-pyspark/01-pyspark-catalyst-and-shuffle-simulator.py
```
