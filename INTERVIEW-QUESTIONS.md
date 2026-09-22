# 🐍 Python Ecosystem & Data Systems Mastery: Las 100 Preguntas Más Comunes en Entrevistas Técnicas

Guía de referencia técnica profunda para preparación de entrevistas en roles de **Senior Python Engineer, Backend Architect, Data Engineer, Staff Software Engineer y Tech Lead (FastAPI, Django, PySpark, CPython Internals)**.

---

## 📑 Tabla de Contenidos

1. [CPython Internals, Gestión de Memoria y el GIL (Preguntas 1-15)](#1-cpython-internals-gestión-de-memoria-y-el-gil)
2. [FastAPI, Django y Arquitecturas Web ASGI/WSGI (Preguntas 16-28)](#2-fastapi-django-y-arquitecturas-web-asgiwsgi)
3. [Procesamiento Distribuido con Apache Spark / PySpark (Preguntas 29-38)](#3-procesamiento-distribuido-con-apache-spark--pyspark)
4. [Tipado Estático Moderno, Testing con Pytest y Tooling (Preguntas 39-100)](#4-tipado-estático-moderno-testing-con-pytest-y-tooling)

---

## 1. CPython Internals, Gestión de Memoria y el GIL

### 1. ¿Qué es el GIL (Global Interpreter Lock) en CPython, qué problemas de seguridad de memoria resuelve en C, y cómo cambia el panorama con PEP 703 (Free-Threading en Python 3.13)?
- **Nivel**: Senior / Staff / Architect
- **Respuesta Técnica**:
  El GIL es un cerrojo de exclusión mutua (*Mutex*) a nivel de proceso en CPython que restringe la ejecución de bytecode de Python a **un único hilo nativo a la vez**, incluso en procesadores con decenas de núcleos físicos.
  - **Por qué existe históricamente**: La gestión de memoria de CPython se basa en conteo de referencias (`ob_refcnt`). Sin el GIL, dos hilos nativos incrementando o decrementando el `refcount` del mismo objeto concurrentemente provocarían condiciones de carrera y fugas o liberaciones prematuras de memoria (*Use-After-Free*). El GIL simplificó masivamente la integración de librerías nativas escritas en C (NumPy, SciPy).
  - **El gran cambio en Python 3.13 (PEP 703 - Free-Threading)**:
    - Introduce una compilación experimental de CPython **sin GIL (`--disable-gil`)**.
    - Reemplaza el mutex global mediante tres técnicas avanzadas:
      1. **Mimalloc**: Asignador de memoria concurrente ultra rápido de Microsoft adaptado para aislamiento por hilo.
      2. **Biased Reference Counting**: Los objetos son propiedad de un hilo principal que actualiza el `refcount` sin operaciones atómicas de CPU costosas; solo los accesos cruzados de hilos secundarios pagan la penalización de operaciones atómicas.
      3. **Inmortalización de Objetos**: Objetos globales (`None`, `True`, números pequeños) se marcan como inmutables y nunca alteran su `refcount`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que el GIL impide que múltiples hilos se beneficien de I/O concurrente (en operaciones de red o disco, CPython libera el GIL permitiendo que otros hilos corran mientras uno espera I/O).
  - 🟢 **Green Flag**: Detallar el impacto de PEP 703 y las técnicas de Biased Reference Counting para permitir paralelismo multinúcleo real en CPU-bound tasks.

---

### 2. ¿Cómo funciona la gestión de memoria en CPython: Reference Counting vs Garbage Collector Generacional (Generational GC)?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  CPython combina dos mecanismos complementarios:
  1. **Reference Counting (Mecanismo Primario y Determinista)**:
     - Cada objeto (`PyObject`) contiene un campo `ob_refcnt`.
     - Cuando una variable se asigna o se pasa como argumento, `ob_refcnt` se incrementa; cuando sale de scope o se ejecuta `del`, se decrementa.
     - **En el milisegundo exacto en que `ob_refcnt == 0`**, el objeto es destruido y su memoria en el Heap es liberada inmediatamente.
  2. **Generational Garbage Collector (Mecanismo Secundario para Ciclos)**:
     - El conteo de referencias falla ante **referencias circulares** (Objeto A apunta a B y B apunta a A; su `refcount` nunca baja de 1 tras salir de scope).
     - El módulo `gc` organiza todos los objetos contenedores (listas, tuplas, diccionarios, instancias de clases) en **3 Generaciones**:
       - **Generación 0**: Objetos recién creados. Se inspecciona con mucha frecuencia.
       - **Generación 1**: Objetos que sobrevivieron a una recolección en Gen 0.
       - **Generación 2**: Objetos longevos que sobrevivieron a recolecciones previas. Se inspecciona con muy baja frecuencia.
     - Si la tasa de asignaciones supera el umbral configurado (`gc.get_threshold()`), el GC ejecuta una detección de ciclos basada en restas de referencias internas en esa generación.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que la instrucción `del var` borra físicamente el objeto de la memoria (solo decrementa el contador de referencias).
  - 🟢 **Green Flag**: Explicar por qué los tipos inmutables que solo contienen datos primitivos (como tuplas de enteros o strings) son excluidos del GC generacional (*Untracked Objects*).

---

### 3. ¿Cómo asigna memoria PyMalloc y qué son los Arenas, Pools y Blocks en CPython?
- **Nivel**: Staff / Principal Engineer
- **Respuesta Técnica**:
  Para evitar el sobrecoste de llamadas al sistema operativo (`malloc`) con objetos pequeños ($\le 512$ bytes, que constituyen el 90% de los objetos en Python):
  - CPython implementa su propio asignador de memoria en espacio de usuario llamado **PyMalloc**:
    1. **Block**: La unidad mínima de memoria asignable (de 8 a 512 bytes, en múltiplos de 8 bytes).
    2. **Pool**: Un bloque continuo de **4KB** de memoria que agrupa bloques del mismo tamaño (*Size Class*). Cada Pool tiene una lista enlazada de bloques libres.
    3. **Arena**: Un bloque continuo de **256KB** asignado directamente del sistema operativo mediante `mmap()` o `malloc()`. Agrupa 64 Pools de 4KB.
  - Para objetos grandes ($> 512$ bytes), CPython salta PyMalloc y delega la asignación directamente a la función estándar `malloc()` del sistema operativo.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer que Python tiene un gestor de memoria especializado para objetos pequeños y asumir que cada entero hace un `malloc` en Linux.
  - 🟢 **Green Flag**: Explicar la fragmentación de memoria y por qué un proceso de Python puede retener memoria en Linux (`RSS`) si una sola celda de un Arena de 256KB sigue en uso.

---

### 4. ¿Cuáles son las diferencias de rendimiento y arquitectura entre Threading, Multiprocessing y Asyncio en Python?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  | Paradigma | Concurrencia / Paralelismo | Espacio de Memoria | Caso de Uso Ideal | Limitación Principal |
  |---|---|---|---|---|
  | **`threading`** | Concurrencia preemptiva (un hilo a la vez por el GIL). | Memoria compartida en el mismo proceso. | Tareas **I/O-Bound bloqueantes legadas** (leer archivos, llamadas a APIs síncronas). | Inútil para acelerar tareas de CPU intensivo debido al GIL. |
  | **`multiprocessing`** | **Paralelismo real multi-core** (un proceso por core, cada uno con su propio GIL e intérprete independiente). | Espacios de memoria completamente aislados (~30-50MB RAM por proceso). | Tareas **CPU-Bound intensivas** (compresión, machine learning, procesamiento de datos). | Alto coste de comunicación entre procesos (IPC) y serialización con `pickle`. |
  | **`asyncio`** | **Concurrencia cooperativa monohilo** sobre un Event Loop (`async/await`). | Un único hilo y un solo espacio de memoria. | Tareas **I/O-Bound ultra concurrentes** (servidores web, websockets, miles de conexiones de red). | Una sola función síncrona bloqueante (`time.sleep()` o cálculo pesado) congela todo el servidor. |
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Proponer `threading` para procesar un cálculo matemático de 10 millones de números esperando que use 16 núcleos de CPU.
  - 🟢 **Green Flag**: Identificar que en `multiprocessing` los objetos deben ser serializables por `pickle` y advertir sobre el sobrecoste de memoria en sistemas Linux usando `fork` vs `spawn`.

---

### 5. ¿Cómo funciona internamente el módulo `dis` y cómo se evalúa el Bytecode en el Frame Evaluation Loop (`_PyEval_EvalFrameDefault`)?
- **Nivel**: Staff / Principal Architect
- **Respuesta Técnica**:
  Python compila el código fuente a bytecode binario inmutable almacenado en objetos de código (`code object`):
  - El módulo **`dis`** es el desensamblador nativo que permite visualizar las instrucciones de opcode generadas:
    ```python
    import dis
    dis.dis(lambda a, b: a + b)
    # Genera: LOAD_FAST 0 (a), LOAD_FAST 1 (b), BINARY_OP 0 (+), RETURN_VALUE
    ```
  - **Frame Evaluation Loop**:
    - La función en C **`_PyEval_EvalFrameDefault()`** en `ceval.c` es el corazón de CPython: un bucle infinito que lee los opcodes secuencialmente y los despacha mediante una instrucción gigante `switch(opcode)` o saltos calculados (*Computed Gotos*).
    - Mantiene una **pila de evaluación (Value Stack)**: los argumentos se cargan en la pila (`LOAD_FAST`) y las operaciones los desapilan, ejecutan la función de C subyacente y apilan el resultado.
    - **Python 3.11+ (Faster CPython / Proyecto Shannon)**: Introdujo un **Optimizador Adaptativo de Bytecode**: los opcodes genéricos lentos (ej. `BINARY_OP`) se mutan en tiempo de ejecución a opcodes especializados monomórficos (`BINARY_OP_ADD_INT`) tras observar tipos repetidos, acelerando la ejecución hasta un 25-60%.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que Python ejecuta directamente el árbol sintáctico (AST) línea por línea sin una fase de compilación a bytecode.
  - 🟢 **Green Flag**: Citar las optimizaciones de Python 3.11+ con Specializing Adaptive Interpreter y el impacto de `LOAD_FAST` vs `LOAD_GLOBAL`.

---

### 6. ¿Cuál es la diferencia estricta entre los métodos dunder `__new__` y `__init__` en la creación de objetos?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **`__new__(cls, *args, **kwargs)`**:
    - Es el **constructor real** del objeto.
    - Método estático implícito que toma la clase `cls` como primer argumento.
    - Su responsabilidad es **asignar físicamente la memoria y crear la nueva instancia** retornándola:
      ```python
      instance = super().__new__(cls)
      return instance
      ```
    - Esencial para implementar el patrón **Singleton**, crear subclases de tipos inmutables primitivos (`int`, `str`, `tuple`) y en Metaclases.
  - **`__init__(self, *args, **kwargs)`**:
    - Es el **inicializador** del objeto.
    - Recibe la instancia recién creada (`self`) por `__new__`.
    - Su responsabilidad es inicializar los atributos del objeto (`self.name = 'Juan'`). **No puede retornar nada distinto de `None`**.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que `__init__` es quien asigna la memoria y crea el objeto en Python.
  - 🟢 **Green Flag**: Implementar un Singleton thread-safe sobrescribiendo `__new__` o heredar de `tuple` inicializando valores antes de que el objeto quede congelado.

---

### 7. ¿Qué es el Protocolo Descriptor (`__get__`, `__set__`, `__delete__`) y cómo alimenta a `@property`, los métodos y los ORMs?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  Un Descriptor es un objeto de Python que define al menos uno de los métodos del protocolo descriptor:
  - `__get__(self, instance, owner)`
  - `__set__(self, instance, value)`
  - `__delete__(self, instance)`
  - **Diferencia Crítica**:
    - **Data Descriptor**: Define `__set__` o `__delete__`. Tiene precedencia absoluta sobre el diccionario de la instancia (`instance.__dict__`).
    - **Non-Data Descriptor**: Solo define `__get__`. Si el atributo existe en `instance.__dict__`, el diccionario de la instancia tiene precedencia.
  - **Dónde se usa en el corazón del lenguaje**:
    1. **`@property`**: Es un Data Descriptor de CPython.
    2. **Métodos de Instancia**: Toda función ordinaria en Python implementa `__get__` (es un Non-Data Descriptor). Al acceder a `obj.metodo`, la función devuelve un objeto enlazado (*Bound Method*) que inyecta automáticamente la instancia en el argumento `self`.
    3. **ORMs (Django/SQLAlchemy)**: Los campos de los modelos (`models.CharField()`) son descriptores que interceptan lecturas y escrituras para aplicar validaciones y queries diferidas.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer que las funciones estándar de Python son descriptores que implementan `__get__` para ligar el `self`.
  - 🟢 **Green Flag**: Explicar el orden de búsqueda de atributos en el diccionario: Data Descriptor $\to$ `instance.__dict__` $\to$ Non-Data Descriptor $\to$ `class.__dict__` $\to$ `__getattr__`.

---

### 8. ¿Qué es una Metaclase (`type`) y cuándo está justificado su uso en lugar de Decoradores de Clase o `__init_subclass__`?
- **Nivel**: Senior / Staff / Architect
- **Respuesta Técnica**:
  En Python, las clases son objetos de primera clase. Así como un objeto es una instancia de una clase, **una clase es una instancia de una Metaclase**.
  - La metaclase por defecto de todo objeto en Python es **`type`**.
  - Una metaclase personalizada hereda de `type` y permite interceptar la **creación y definición de las clases en tiempo de compilación/importación**:
    ```python
    class Meta(type):
      def __new__(mcs, name, bases, attrs):
        # Mutar o validar atributos de la clase antes de que exista
        return super().__new__(mcs, name, bases, attrs)
    ```
  - **Cuándo NO usar Metaclases**: En el 95% de los casos, las metaclases introducen una complejidad innecesaria. Desde Python 3.6, el método hook nativo **`__init_subclass__`** permite personalizar y validar la herencia de subclases de forma limpia sin tocar metaclases.
  - **Cuándo sí están justificadas**: En la construcción de frameworks profundos (Pydantic v1, Django Models) que requieren reescribir la tabla de símbolos de la clase o registrar namespaces dinámicamente antes de instanciar la clase.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar metaclases complejas para tareas triviales que se resuelven con un decorador de clase o `__init_subclass__`.
  - 🟢 **Green Flag**: Citar a Tim Peters: *"Las metaclases son magia más profunda de la que el 99% de los desarrolladores necesitará jamás"*, demostrando madurez arquitectónica.

---

### 9. ¿Qué es y cómo funciona el MRO (Method Resolution Order) con el algoritmo C3 Linearization?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  En Python, ante la herencia múltiple (ej. el problema del diamante: la clase D hereda de B y C, y ambas heredan de A), el MRO define la secuencia exacta en la que se buscan los métodos y atributos:
  - CPython utiliza el **Algoritmo de Linealización C3**:
    - Garantiza dos propiedades fundamentales:
      1. **Precedencia de Hijos sobre Padres**: Una subclase siempre se consulta antes que cualquiera de sus clases base.
      2. **Preservación del Orden de Declaración**: Si la clase declara `class D(B, C)`, los métodos de B siempre se buscan antes que los de C.
      3. **Monotonicidad**: Si una clase precede a otra en la jerarquía, esa relación de orden se preserva en todas las subclases derivadas.
  - Si una jerarquía de clases viola las reglas de C3, Python **rechaza la creación de la clase en tiempo de compilación con un error: `TypeError: Cannot create a consistent method resolution order (MRO)`**.
  - Se puede inspeccionar con `Clase.mro()` o `Clase.__mro__`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que Python busca métodos mediante un simple recorrido en profundidad (Depth-First Search) ingenuo.
  - 🟢 **Green Flag**: Explicar cómo la función `super()` no llama necesariamente al padre inmediato de la clase, sino al siguiente elemento en la lista del MRO de la instancia.

---

### 10. ¿Por qué `__slots__` reduce drásticamente el consumo de memoria RAM y cuándo debe utilizarse?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Por defecto en Python**: Cada instancia de una clase almacena sus atributos en un diccionario dinámico interno llamado **`__dict__`**. Un diccionario de Python consume un mínimo de 150-250 bytes de sobrecoste de memoria en el Heap para permitir agregar atributos dinámicamente en cualquier momento.
  - **Con `__slots__`**:
    ```python
    class Point:
      __slots__ = ('x', 'y')
      def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    ```
    - CPython **elimina por completo el diccionario `__dict__` de cada instancia**.
    - Los atributos se almacenan internamente en un array de punteros C de tamaño fijo preasignado en memoria contigua.
    - **Beneficios**: Reduce el consumo de memoria por objeto en hasta un **60% - 75%** y acelera el acceso a propiedades en CPU.
  - **Cuándo usarlo**: En aplicaciones de Big Data, ciencia de datos o sistemas donde instancies **millones de objetos pequeños en memoria RAM**.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer que las clases con `__slots__` no permiten asignar atributos dinámicos arbitrarios no declarados en tiempo de ejecución.
  - 🟢 **Green Flag**: Recordar que si heredas de una clase sin `__slots__`, la subclase heredará un `__dict__` a menos que ambas definan `__slots__`.

---

### 11. ¿Cuál es la diferencia entre `deepcopy` y `shallow copy` (`copy.copy`) y cuáles son sus trampas de rendimiento?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  - **Shallow Copy (`copy.copy(x)` o `list(x)`)**: Crea un nuevo objeto contenedor, pero **inserta referencias a los mismos objetos hijos exactos contenidos en el original**.
    ```python
    a = [[1, 2, 3]]
    b = a.copy()
    b[0].append(4) # ¡Mutación compartida!: a[0] ahora también tiene [1, 2, 3, 4]
    ```
  - **Deep Copy (`copy.deepcopy(x)`)**: Crea un nuevo objeto contenedor y **recorre recursivamente todo el grafo de objetos dependientes copiando cada valor**.
  - **Trampas de Rendimiento**:
    - `deepcopy()` es extremadamente lento: mantiene un diccionario interno de memorización (`memo`) para no entrar en bucles infinitos con referencias circulares, lo que añade un sobrecoste masivo de CPU en grafos densos.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `deepcopy()` de forma rutinaria sobre estructuras de miles de nodos sin evaluar alternativas inmutables.
  - 🟢 **Green Flag**: Citar la protección interna contra ciclos mediante el diccionario `memo` en la implementación de `copy.deepcopy()`.

---

### 12. ¿Cómo funciona el Context Manager Protocol (`__enter__`, `__exit__`) y qué significa retornar `True` en `__exit__`?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  Gobierna la sentencia **`with`** para garantizar la liberación determinista de recursos (archivos, sockets, cerrojos de base de datos):
  - **`__enter__(self)`**: Inicializa el recurso y retorna el valor que se asociará a la variable tras el `as` (`with Resource() as r:`).
  - **`__exit__(self, exc_type, exc_val, exc_tb)`**: Se ejecuta **SIEMPRE**, incluso si ocurrió una excepción no controlada dentro del bloque `with`.
  - **Retornar `True` en `__exit__`**:
    - Si el bloque arrojó una excepción y `__exit__` retorna un valor veraz (**`True`**), **la excepción es silenciada y suprimida por completo**: el programa continúa ejecutándose con normalidad tras el bloque `with`.
    - Si retorna `False` o `None`, la excepción se re-lanza hacia arriba por la pila de llamadas.
  - **Alternativa concisa**: El decorador `@contextmanager` del módulo `contextlib` permite escribir context managers con funciones generadoras (`yield`).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Silenciar excepciones retornando `True` ciegamente en `__exit__` ocultando errores fatales del sistema.
  - 🟢 **Green Flag**: Utilizar `contextlib.ExitStack` para gestionar un número dinámico variable de context managers abiertos en paralelo.

---

### 13. ¿Qué es el "GIL Release" en extensiones en C / Cython y por qué permite que librerías como NumPy o Polars escalen a múltiples núcleos?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  Cuando una operación pesada no necesita interactuar con objetos de Python ni mutar sus `ob_refcnt`:
  - En la extensión en C o Cython, se invoca la macro de CPython:
    ```c
    Py_BEGIN_ALLOW_THREADS
    // Código en C puro de cómputo intensivo (multiplicación de matrices en NumPy)
    // Se ejecuta en hilos POSIX nativos en múltiples núcleos de CPU en paralelo
    Py_END_ALLOW_THREADS
    ```
  - Esto **libera el GIL temporalmente**: el hilo de C ejecuta el cálculo numérico a toda velocidad en todos los cores mientras otros hilos de Python pueden continuar ejecutando código en el Event Loop.
  - Al terminar el cómputo, la macro re-adquiere el GIL antes de devolver el resultado a Python.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Asumir que NumPy o PyTorch están limitados a un solo núcleo por el GIL de Python.
  - 🟢 **Green Flag**: Explicar la barrera de seguridad: está prohibido tocar cualquier estructura `PyObject*` dentro del bloque `Py_BEGIN_ALLOW_THREADS`.

---

### 14. ¿Qué es la librería `weakref` y cómo previene ciclos de memoria en cachés de objetos?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  El módulo `weakref` permite crear **Referencias Débiles** a objetos de Python:
  - Una referencia débil **NO incrementa el `ob_refcnt` del objeto de destino**.
  - Si todas las referencias fuertes desaparecen, el objeto es destruido inmediatamente por el recolector de basura, y la referencia débil devuelve `None` o activa un callback de limpieza.
  - **Caso de uso primordial (`weakref.WeakValueDictionary`)**:
    - Ideal para construir **Cachés de Instancias en memoria**:
      ```python
      import weakref

      _cache = weakref.WeakValueDictionary()

      def get_user(user_id: int):
        if user_id in _cache:
          return _cache[user_id]
        user = load_from_db(user_id)
        _cache[user_id] = user
        return user
      ```
    - Mientras alguna parte del código esté utilizando el objeto `user`, la caché lo recordará. En cuanto nadie lo use, el objeto es liberado de RAM automáticamente sin que la caché mantenga una fuga de memoria.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar un `dict` ordinario para almacenar cachés en memoria sin considerar políticas de expiración o WeakReferences.
  - 🟢 **Green Flag**: Conocer las limitaciones: tipos primitivos inmutables como `int` o `tuple` no soportan referencias débiles directas.

---

### 15. ¿Qué diferencia hay entre funciones síncronas bloqueantes y llamadas en `asyncio.to_thread()` en servidores ASGI?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  En un servidor asíncrono (FastAPI / Uvicorn con `asyncio`):
  - Si dentro de una función de ruta `async def` ejecutas una llamada síncrona bloqueante (ej. `time.sleep(5)`, `requests.get()`, o una consulta con un ORM síncrono):
    - **El Event Loop monohilo se congela por completo durante 5 segundos**.
    - Ninguna otra petición de ningún otro usuario puede ser atendida durante ese tiempo.
  - **Solución con `asyncio.to_thread()` (Python 3.9+)**:
    - Delega la función síncrona bloqueante a un **hilo secundario separado del ThreadPoolExecutor**:
      ```python
      # No congela el Event Loop principal:
      data = await asyncio.to_thread(requests.get, "https://api.lenta.com")
      ```
    - El Event Loop principal cede el control inmediatamente y sigue atendiendo a miles de usuarios concurrentes mientras el hilo secundario espera la respuesta.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Bloquear el Event Loop de FastAPI usando librerías síncronas como `requests` en endpoints `async def`.
  - 🟢 **Green Flag**: Saber que en FastAPI declarar un endpoint como `def` normal (sin `async`) hace que FastAPI lo despache automáticamente a un worker thread pool para proteger el Event Loop.

---

## 2. FastAPI, Django y Arquitecturas Web ASGI/WSGI

### 16. ¿Cuál es la diferencia fundamental de arquitectura entre la especificación WSGI (PEP 3333) y ASGI?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **WSGI (Web Server Gateway Interface - PEP 3333)**:
    - Diseñado en 2003 para un modelo de petición/respuesta puramente **síncrono**:
      ```python
      def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b"Hola Mundo"]
      ```
    - Cada petición HTTP bloquea un hilo o proceso worker completo de Gunicorn/uWSGI hasta que la respuesta termina.
    - Incapaz de manejar WebSockets, Server-Sent Events (SSE) o miles de conexiones HTTP de larga duración (*Long-Polling*). (Base de Django clásico y Flask).
  - **ASGI (Asynchronous Server Gateway Interface)**:
    - El estándar moderno superset de WSGI basado en **`asyncio`**:
      ```python
      async def application(scope, receive, send):
        # scope: diccionario de conexión
        # receive: función awaitable para escuchar eventos entrantes (mensajes websocket, chunks HTTP)
        # send: función awaitable para emitir datos hacia el cliente
      ```
    - Maneja de forma nativa protocolos bidireccionales, streaming de datos HTTP y WebSockets sobre un único Event Loop no bloqueante. (Base de FastAPI, Starlette y Django Channels).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar correr WebSockets en producción sobre un servidor WSGI puro como Gunicorn con workers síncronos.
  - 🟢 **Green Flag**: Analizar los 3 argumentos de la interfaz ASGI (`scope`, `receive`, `send`) y cómo gestionan los ciclos de vida `lifespan`.

---

### 17. ¿Por qué Pydantic v2 es hasta 20 veces más rápido que Pydantic v1 y qué implicaciones tiene en FastAPI?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  En Pydantic v1, toda la lógica de validación, recursión de esquemas y serialización estaba escrita en código Python puro, pagando el sobrecoste de interpretación del Zend/CPython.
  - **Pydantic v2 (Reescritura en Rust Core)**:
    - Todo el motor nuclear de validación y serialización fue reescrito en **Rust (`pydantic-core`)**.
    - El árbol de validación se compila en un validador nativo de Rust que opera directamente sobre memoria en C.
    - **Validación y Serialización Ultra Rápida**: Hasta **5x a 50x más rápido** validando payloads JSON y convirtiendo modelos a diccionarios (`model_dump()`).
  - **Implicaciones en FastAPI**: Como FastAPI utiliza Pydantic para validar cada body entrante y serializar cada respuesta saliente, la adopción de Pydantic v2 redujo la latencia de CPU por petición a la mitad en APIs enterprise.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Seguir utilizando métodos depreciados de Pydantic v1 como `.dict()` y `.parse_obj()` en lugar de `.model_dump()` y `.model_validate()`.
  - 🟢 **Green Flag**: Detallar la interoperabilidad de tipos con `Annotated` y los validadores de Rust (`@field_validator`, `@model_validator`).

---

### 18. ¿Cómo funciona el sistema de Inyección de Dependencias con `Depends()` en FastAPI?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  El sistema de dependencias de FastAPI construye internamente un **Grafo Acíclico Dirigido (DAG)** de dependencias para cada endpoint:
  ```python
  async def get_db():
    db = SessionLocal()
    try:
      yield db
    finally:
      db.close() # Se ejecuta garantizadamente al terminar la petición

  async def get_current_user(token: str = Header(...), db: Session = Depends(get_db)):
    return authenticate(db, token)

  @app.get("/items")
  async def read_items(user: User = Depends(get_current_user)):
    return user.items
  ```
  - **Mecánica**:
    1. Resuelve dependencias jerárquicas en cascada (`read_items` $\to$ `get_current_user` $\to$ `get_db`).
    2. **Dependency Caching (`use_cache=True` por defecto)**: Si múltiples dependencias en el mismo árbol solicitan `get_db()`, FastAPI invoca la función una sola vez y comparte el mismo valor en toda la petición.
    3. Soporta generadores (`yield`) para manejo limpio de recursos y transacciones con cierre garantizado.
    4. **Testing sin Mocks frágiles**: Permite sobrescribir dependencias globalmente en tests con `app.dependency_overrides[get_db] = get_test_db`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer `app.dependency_overrides` y usar complejos patches de `unittest.mock` para simular la base de datos en tests.
  - 🟢 **Green Flag**: Explicar la interacción de `yield` en generadores de dependencias con el contexto de salida del middleware.

---

### 19. ¿Cuál es la diferencia estricta entre `select_related` y `prefetch_related` en el ORM de Django?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  Ambos son los métodos de Django para mitigar el problema de las Consultas N+1:
  - **`select_related(*fields)`**:
    - Funciona a nivel de **SQL JOIN (`INNER JOIN` o `LEFT OUTER JOIN`)**.
    - Solo funciona para relaciones de un solo valor: **ForeignKey (1 a N)** y **OneToOneField (1 a 1)**.
    - Ejecuta una **única consulta SQL** consolidada trayendo todas las columnas de la tabla padre y relacionada en un solo viaje de red.
  - **`prefetch_related(*lookups)`**:
    - Funciona ejecutando **consultas SQL separadas y haciendo el JOIN en memoria en Python**:
    - Obligatorio para relaciones multi-valor: **ManyToManyField (N a M)** y la inversa de ForeignKeys (**Reverse ForeignKey** / `1 a N`).
    - Ejecuta exactamente **2 consultas SQL**:
      1. `SELECT * FROM pizzas;`
      2. `SELECT * FROM toppings WHERE pizza_id IN (1, 2, ...);`
    - En memoria, el ORM de Django conecta los ingredientes con sus respectivas pizzas.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar usar `select_related` sobre un campo `ManyToManyField` (Django arrojará un error de consulta).
  - 🟢 **Green Flag**: Utilizar el objeto `Prefetch()` para filtrar y optimizar la subconsulta secundaria de `prefetch_related`.

---

### 20. ¿Cómo funciona la evaluación perezosa (Lazy Evaluation) de los QuerySets en Django y cuándo golpean realmente la base de datos?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  Crear o encadenar filtros en un QuerySet de Django **NO ejecuta ninguna consulta SQL en la base de datos**:
  ```python
  # Cero consultas SQL ejecutadas aquí (solo se construye el objeto en memoria):
  qs = User.objects.filter(is_active=True).exclude(role='guest').order_by('-date')
  ```
  El QuerySet solo "golpea" físicamente la base de datos en el milisegundo exacto en que sus datos son evaluados:
  1. **Iteración**: `for user in qs:`
  2. **Slicing con Step**: `qs[0:10:2]` (un slice simple sin step `qs[0:10]` solo añade `LIMIT/OFFSET` sin evaluar).
  3. **Evaluación Booleana**: `if qs:` o `bool(qs)` (para verificar existencia, usar siempre `qs.exists()` que ejecuta un `SELECT 1` mucho más rápido).
  4. **Funciones de Agregación o Conversión**: `len(qs)` (evalúa y trae todo a memoria; para contar registros usar siempre `qs.count()`), `list(qs)`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `if len(User.objects.filter(...)) > 0:` en lugar de `if User.objects.filter(...).exists():`.
  - 🟢 **Green Flag**: Explicar cómo el QuerySet cachea internamente los resultados en `qs._result_cache` tras la primera evaluación.

---

### 21. ¿Cómo se diseñan Transacciones Atómicas y Bloqueos de Concurrencia en Django (`transaction.atomic` y `select_for_update`)?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  - **`transaction.atomic()`**:
    - Context manager que envuelve un bloque en una transacción SQL (`BEGIN ... COMMIT`).
    - Soporta transacciones anidadas mediante **Savepoints** de base de datos (`SAVEPOINT`).
    - Si se produce una excepción, hace rollback automático al savepoint o al inicio de la transacción.
  - **`select_for_update()` (Row-Level Locking)**:
    - Bloquea las filas consultadas para evitar condiciones de carrera en operaciones de inventario o dinero:
      ```python
      with transaction.atomic():
        account = Account.objects.select_for_update().get(id=account_id)
        account.balance -= amount
        account.save()
      ```
    - Agrega la instrucción SQL `SELECT ... FOR UPDATE`, garantizando que ninguna otra transacción concurrente pueda mutar ese saldo hasta que la transacción actual haga commit.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Modificar saldos financieros concurrentes con un simple `filter().update()` sin bloqueos ni transacciones atómicas.
  - 🟢 **Green Flag**: Usar expresiones `F()` (`account.balance = F('balance') - amount`) para delegar el cálculo atómico directamente al motor SQL.

---

### 22. ¿Cómo funciona la arquitectura de Middlewares en Django y cuál es la diferencia con los Middlewares de FastAPI?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Middlewares de Django (Síncronos o Asíncronos)**:
    - Clases con el método `__call__(request)`:
      ```python
      class SimpleMiddleware:
        def __init__(self, get_response):
          self.get_response = get_response

        def __call__(self, request):
          # Lógica antes de la vista
          response = self.get_response(request)
          # Lógica después de la vista
          return response
      ```
    - Si el middleware implementa métodos especiales como `process_view()` o `process_exception()`, Django los invoca en momentos precisos del ciclo.
  - **Middlewares en FastAPI (ASGI puro)**:
    - Operan a nivel de protocolo ASGI crudo sobre la tupla `(scope, receive, send)` o mediante la abstracción `BaseHTTPMiddleware` de Starlette.
    - Permiten interceptar streaming asíncrono de chunks de datos binarios y WebSockets sin bloquear hilos.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `BaseHTTPMiddleware` en FastAPI para streaming masivo de archivos sin saber que rompe el streaming acumulando todo en memoria.
  - 🟢 **Green Flag**: Diseñar middlewares asíncronos nativos en Django 4.2+ adaptados con `asgiref.sync.sync_to_async`.

---

### 23. ¿Cómo se ejecutan tareas en segundo plano en FastAPI con `BackgroundTasks` vs Celery?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **`BackgroundTasks` de FastAPI**:
    - Tareas que se ejecutan **dentro del mismo proceso del servidor web** inmediatamente después de haber emitido la respuesta HTTP al cliente.
    - *Pros*: Cero infraestructura adicional (no requiere Redis ni workers externos).
    - *Contras*: Si el contenedor o pod de Kubernetes se reinicia o muere en ese segundo, la tarea se pierde para siempre; si la tarea es pesada, consumirá la CPU del propio servidor web. Solo apto para tareas triviales (enviar un email simple o registrar una métrica en log).
  - **Celery / Dramatiq (Colas Distribuidas Reales)**:
    - Las tareas se serializan y se depositan en un Message Broker independiente (RabbitMQ / Redis).
    - Procesadas por workers desacoplados en máquinas independientes.
    - Soporta reintentos exponenciales, persistencia garantizada, balanceo de carga y prioridades. Obligatorio para tareas de negocio críticas (procesamiento de pagos, generación de reportes PDF pesados, machine learning).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `BackgroundTasks` de FastAPI para procesar una exportación de vídeo que tarda 20 minutos.
  - 🟢 **Green Flag**: Argumentar con tolerancia a fallos, durabilidad de tareas y desacoplamiento de recursos entre la API y los workers.

---

### 24. ¿Qué es y cómo funciona el mecanismo de Migraciones de Base de Datos en Django ORM?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  El sistema de migraciones de Django es declarativo y bidireccional:
  - Cada cambio en un archivo `models.py` se traduce en un archivo de migración mediante `python manage.py makemigrations`.
  - El archivo de migración contiene operaciones puras de Python (`operations = [migrations.AddField(...)]`).
  - Al ejecutar `python manage.py migrate`:
    - Django consulta la tabla interna **`django_migrations`** en la base de datos para ver qué archivos ya fueron aplicados.
    - Resuelve el grafo de dependencias de migraciones entre diferentes aplicaciones (`dependencies = [...]`).
    - Ejecuta las sentencias DDL correspondientes dentro de una **transacción atómica** (en bases de datos que soportan DDL transaccional como PostgreSQL).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Modificar a mano archivos de migraciones históricas ya aplicadas en producción en lugar de crear una nueva migración.
  - 🟢 **Green Flag**: Explicar migraciones de datos (`migrations.RunPython`) con soporte de rollback reverso (`reverse_code`).

---

### 25. ¿Cómo se previene el ataque de CSRF (Cross-Site Request Forgery) en Django y por qué las APIs REST tokenizadas no lo necesitan?
- **Nivel**: Mid-Level / Senior / Security
- **Respuesta Técnica**:
  - **El Ataque CSRF**: Ocurre en aplicaciones basadas en **Cookies de Sesión**: el navegador adjunta automáticamente la cookie de sesión del usuario en cualquier petición hacia el dominio víctima, incluso si el clic se originó en un sitio web malicioso externo.
  - **Defensa en Django**: Implementa el patrón **Synchronizer Token Pattern**:
    - Inserta un token secreto criptográfico en un campo oculto del formulario (`{% csrf_token %}`) y en una cookie.
    - Al enviar el formulario por `POST`, el middleware `CsrfViewMiddleware` valida que el token del body coincida con el de la cookie.
  - **Por qué las APIs REST basadas en cabeceras `Authorization: Bearer <JWT>` son inmunes a CSRF**:
    - El navegador **NUNCA adjunta automáticamente cabeceras `Authorization` personalizadas** en peticiones cruzadas.
    - Para enviar la cabecera, la página de origen debe ejecutar JavaScript explícito (`fetch()`), el cual está estrictamente bloqueado por la política de mismo origen del navegador (**CORS**).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Almacenar tokens JWT en `localStorage` creyendo que es seguro sin advertir sobre la vulnerabilidad extrema ante ataques XSS.
  - 🟢 **Green Flag**: Explicar el uso de cookies con directivas modernas `SameSite=Strict` y `HttpOnly` para mitigar tanto XSS como CSRF.

---

### 26. ¿Cómo se optimiza la serialización masiva de datos en Django REST Framework (DRF)?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  El serializador estándar `ModelSerializer` de DRF es notoriamente lento para listas de miles de elementos debido al sobrecoste de instanciar validadores de campo por cada atributo de cada fila.
  **Estrategias de Optimización**:
  1. **`values()` / `values_list()`**: Si solo se necesita emitir un JSON de lectura, consultar directamente los campos en SQL (`User.objects.values('id', 'name')`), saltándose por completo la instanciación de objetos del modelo.
  2. **`Serpy` / `msgspec`**: Reemplazar los serializadores de DRF por serializadores ultrarrápidos basados en C o compilados.
  3. **Paginación estricta obligatoria**: No permitir descargas masivas de 50,000 registros sin paginación por cursor.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Dejar que un endpoint de DRF serialice 10,000 modelos complejos en memoria tardando 12 segundos por petición.
  - 🟢 **Green Flag**: Combinar `values()` con la librería ultra rápida `orjson` para generar respuestas JSON en milisegundos.

---

### 27. ¿Cómo funciona la arquitectura de señales (`django.db.models.signals`) y cuáles son sus peligros ocultos?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  Las señales de Django (`post_save`, `pre_save`, `post_delete`) permiten desacoplar componentes emitiendo notificaciones cuando ocurren eventos en los modelos:
  **Peligros Ocultos**:
  1. **Ejecución Síncrona Oculta**: Las señales de Django **NO son asíncronas**. Se ejecutan de forma estrictamente síncrona dentro del mismo hilo y dentro de la misma transacción de base de datos que el `.save()`. Un listener lento bloqueará toda la petición web.
  2. **No se disparan en operaciones masivas**: Métodos como `bulk_create()`, `bulk_update()` y `QuerySet.update()` **NUNCA disparan las señales `post_save` ni `pre_save`**.
  3. **Flujo de Control Invisible**: Dificultan la depuración porque el código salta a listeners remotos sin trazabilidad explícita.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Depender de una señal `post_save` para lógica crítica de negocio asumiendo que siempre se ejecuta ante cualquier actualización.
  - 🟢 **Green Flag**: Recomendar encapsular la lógica en Servicios de Dominio explícitos (*Service Layer Pattern*) en lugar de abusar de señales mágicas.

---

### 28. ¿Cómo gestionar la conexión con múltiples Bases de Datos en Django (Database Routers)?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  Django soporta arquitecturas multi-base de datos (ej. separar lecturas de escrituras o sharding por cliente) implementando una clase **Database Router**:
  ```python
  class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
      return 'replica' # Todas las lecturas van a la réplica de lectura

    def db_for_write(self, model, **hints):
      return 'default' # Todas las escrituras van al nodo maestro primario

    def allow_relation(self, obj1, obj2, **hints):
      return True

    def allow_migrate(self, db, app_label, **hints):
      return True
  ```
  - Registrado en `settings.py` mediante `DATABASE_ROUTERS = ['path.to.PrimaryReplicaRouter']`.
  - Permite dirigir dinámicamente queries específicas usando `.using('analytics_db')`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Realizar escrituras en una réplica de base de datos de solo lectura por no configurar un router que separe tráfico.
  - 🟢 **Green Flag**: Explicar la trampa del retraso de replicación (*Replication Lag*): tras escribir una orden en el maestro, leerla inmediatamente de la réplica puede arrojar un 404; el router debe forzar lecturas desde el maestro tras una escritura reciente.

---

## 3. Procesamiento Distribuido con Apache Spark / PySpark

### 29. ¿Cuál es la arquitectura fundamental de Apache Spark (Driver, Cluster Manager, Executors y Workers)?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  Spark sigue una arquitectura maestro-esclavo distribuida:
  1. **Driver Program**:
     - El cerebro del trabajo (*SparkSession*). Ejecuta la función `main()` del código de usuario.
     - Analiza el código, construye el Grafo Acíclico Dirigido (**DAG**) de transformaciones lógicas y lo divide en **Stages** y **Tasks**.
     - Programa las tareas y las despacha a los Executors a través del Cluster Manager.
  2. **Cluster Manager (YARN, Kubernetes, Standalone)**:
     - Asigna recursos físicos (CPU cores y memoria RAM) en las máquinas físicas del clúster.
  3. **Worker Nodes**:
     - Nodos físicos o VMs en el clúster que ejecutan los procesos ejecutores.
  4. **Executors**:
     - Procesos de la JVM que corren en los Worker Nodes.
     - Ejecutan las tareas individuales (**Tasks**) en paralelo mediante múltiples hilos.
     - Almacenan en memoria RAM y disco los datos de los DataFrames y cachés persistidas.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Ejecutar operaciones como `.collect()` en un DataFrame de 10 Terabytes en el Driver (hace colapsar el Driver por Out of Memory).
  - 🟢 **Green Flag**: Describir la interacción entre el proceso Driver y los procesos Executors y la contención de red durante la etapa de Shuffle.

---

### 30. ¿Cuál es la diferencia entre RDDs, DataFrames y Datasets en Spark?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **RDD (Resilient Distributed Dataset)**:
    - La abstracción fundacional de bajo nivel de Spark: colección inmutable y distribuida de objetos JVM.
    - Cero optimización de esquema: Spark trata a los objetos como cajas negras opacas.
    - En PySpark es lento debido al coste constante de serializar y deserializar objetos de Python a la JVM (*Py4J overhead*).
  - **DataFrame**:
    - Colección distribuida de datos organizada en columnas con nombre y tipos de datos fuertemente tipados (equivalente a una tabla SQL o Pandas).
    - **Acelerado por el Optimizador Catalyst y el motor Tungsten**: el código se optimiza a nivel lógico y físico; se ejecuta en memoria binaria fuera del Heap de la JVM a la misma velocidad en Python, Scala, Java o R.
  - **Dataset**:
    - Disponible exclusivamente en Scala y Java (no en Python por ser de tipado dinámico). Combina la seguridad de tipos en tiempo de compilación de las clases tipadas con el rendimiento de Catalyst.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar RDDs con bucles manuales de `map()` y `filter()` en PySpark en lugar de DataFrames nativos.
  - 🟢 **Green Flag**: Explicar que los DataFrames de PySpark operan con paridad de rendimiento con Scala porque Catalyst genera código máquina de bajo nivel.

---

### 31. ¿Cómo funciona el Optimizador Catalyst y el motor de ejecución Tungsten en Spark SQL?
- **Nivel**: Senior / Staff / Data Architect
- **Respuesta Técnica**:
  - **Catalyst Optimizer**:
    - Motor de optimización extensible de consultas de 4 fases:
      1. *Analysis*: Resuelve nombres de columnas y tipos contra el Catálogo.
      2. *Logical Optimization*: Aplica reglas de optimización basadas en álgebra relacional: **Predicate Pushdown** (empujar los filtros `WHERE` directamente al archivo Parquet en disco para no leer columnas innecesarias) y **Projection Pruning** (leer solo las columnas seleccionadas).
      3. *Physical Planning*: Genera múltiples planes físicos de ejecución y selecciona el más económico basado en costes (*Cost-Based Optimizer - CBO*).
      4. *Code Generation*: Genera bytecode de Java en tiempo de ejecución.
  - **Tungsten Engine**:
    - Optimización a nivel de hardware:
      1. **Gestión de Memoria Off-Heap**: Almacena los datos en memoria binaria cruda sin envoltorios de objetos de la JVM, eliminando la sobrecarga y pausas de Garbage Collection.
      2. **Whole-Stage Code Generation**: Fusiona múltiples operadores consecutivos en un único bucle de código de bajo nivel, maximizando la utilización de registros de la CPU y la localidad de caché L1/L2.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que Spark es rápido simplemente "porque corre en memoria RAM" sin entender Catalyst y Tungsten.
  - 🟢 **Green Flag**: Citar Predicate Pushdown sobre archivos Parquet y la eliminación de sobrecoste de GC con Tungsten Off-Heap memory.

---

### 32. ¿Cuál es la diferencia entre Transformaciones "Narrow" y "Wide" en PySpark y qué es un Shuffle?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Narrow Transformations (Transformaciones Estrechas)**:
    - Cada partición del DataFrame hijo depende de **exactamente una única partición del DataFrame padre**.
    - No requiere mover datos a través de la red entre diferentes nodos. Cada executor procesa sus datos de forma 100% local y en paralelo.
    - Ejemplos: `filter()`, `map()`, `select()`, `drop()`.
  - **Wide Transformations (Transformaciones Anchas)**:
    - Múltiples particiones del DataFrame hijo dependen de datos distribuidos a lo largo de **todas las particiones del DataFrame padre**.
    - Requiere redistribuir los datos físicamente a través de la red entre todos los nodos del clúster basándose en una clave de hash: este proceso masivo se llama **SHUFFLE**.
    - Ejemplos: `groupBy()`, `distinct()`, `join()`, `orderBy()`.
    - **Impacto**: El Shuffle es la operación más lenta y costosa de Spark: satura el I/O de disco y el ancho de banda de red del clúster.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer qué es un Shuffle y escribir múltiples `groupBy()` consecutivos sin considerar el coste de red.
  - 🟢 **Green Flag**: Explicar cómo el DAG Scheduler corta los *Stages* exactamente en los límites donde se produce una transformación Wide (Shuffle boundary).

---

### 33. ¿Cómo funciona un Broadcast Hash Join en PySpark y cuándo evita el temido Shuffle?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  Cuando unes un DataFrame gigante de transacciones (100 millones de filas) con un DataFrame pequeño de catálogo de países o categorías (1,000 filas):
  - **Sort-Merge Join ordinario (Lento con Shuffle)**: Spark reparte ambos DataFrames a través de la red por hash de la clave, ordena los datos en disco en todos los nodos y ejecuta el join.
  - **Broadcast Hash Join (`broadcast()`)**:
    ```python
    from pyspark.sql.functions import broadcast

    # El DataFrame pequeño se difunde a todos los nodos:
    df_resultado = df_transacciones.join(broadcast(df_paises), "pais_id")
    ```
    - El Driver copia la tabla pequeña completa y la envía por red **una sola vez a cada uno de los Executors**.
    - Cada executor carga la tabla pequeña en una tabla Hash en memoria local.
    - El join se ejecuta de forma totalmente local en cada nodo: **CERO SHUFFLE del DataFrame gigante de 100 millones de filas**.
    - Configurado por defecto para tablas menores a 10MB (`spark.sql.autoBroadcastJoinThreshold`).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar hacer broadcast de un DataFrame de 50GB, provocando un error OOM en el Driver de Spark.
  - 🟢 **Green Flag**: Ajustar `spark.sql.autoBroadcastJoinThreshold` y monitorear el plan físico con `df.explain()` para verificar `BroadcastHashJoin`.

---

### 34. ¿Qué es el "Data Skew" en Spark y cuáles son las técnicas para mitigar particiones desbalanceadas?
- **Nivel**: Senior / Staff / Data Architect
- **Respuesta Técnica**:
  El Data Skew (Sesgo de Datos) ocurre cuando los datos no están distribuidos uniformemente entre las particiones:
  - **El Síntoma en la UI de Spark**: 199 tareas terminan en 10 segundos, pero **1 sola tarea se queda colgada al 99% durante 45 minutos** (o falla con `OutOfMemoryError`). Esto sucede porque el 90% de los registros comparten la misma clave de agrupamiento (ej. `NULL` o el cliente "Amazon" en una columna `client_id`), saturando un solo executor mientras los otros 199 permanecen ociosos.
  - **Estrategias de Mitigación**:
    1. **Salting (Salado de Claves)**: Agregar un número pseudoaleatorio a la clave para dispersar las filas skeweadas entre múltiples subparticiones:
       `df = df.withColumn("salted_key", concat(col("key"), lit("_"), rand() * 10))`
    2. **Adaptive Query Execution (AQE)**: Habilitar `spark.sql.adaptive.enabled = true` y `spark.sql.adaptive.skewJoin.enabled = true` (activo por defecto en Spark 3+): Spark detecta las particiones con skew en tiempo de ejecución y las divide automáticamente en subtareas paralelas.
    3. **Filtrado previo de nulos**: Aislar los registros con `NULL` antes del join y unirlos al final con `unionByName()`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Responder que para solucionar el skew simplemente hay que aumentar la memoria RAM de todas las máquinas del clúster.
  - 🟢 **Green Flag**: Demostrar la técnica matemática de Key Salting y el uso de AQE Skew Join Optimization en Spark 3.

---

### 35. ¿Cuál es la diferencia entre `cache()` y `persist()` en Spark y cuándo debe liberarse con `unpersist()`?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **`cache()`**: Almacena el DataFrame en memoria RAM con el nivel de almacenamiento predeterminado: **`StorageLevel.MEMORY_AND_DISK`** (en DataFrames) o `MEMORY_ONLY` (en RDDs).
  - **`persist(storage_level)`**: Permite seleccionar explícitamente el nivel de almacenamiento deseado:
    - `MEMORY_ONLY`: En memoria sin serializar.
    - `MEMORY_ONLY_SER`: En memoria serializado como bytes (ocupa mucho menos espacio, pero consume más CPU al deserializar).
    - `MEMORY_AND_DISK`: En memoria; si no cabe, desborda los bloques excedentes al disco local de los workers.
    - `DISK_ONLY`, o réplicas `_2` (replica los datos en 2 nodos para tolerancia a fallos).
  - **Cuándo usarlos**: Cuando un mismo DataFrame transformado va a ser consumido por **múltiples acciones posteriores diferentes**.
  - **`unpersist()`**: Es imperativo liberar los datos persistidos cuando ya no se necesitan para no agotar la memoria de ejecución de los executors.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Poner `.cache()` en cada línea de código de un pipeline lineal que solo se ejecuta una sola vez.
  - 🟢 **Green Flag**: Explicar la diferencia entre el Storage Memory Pool y el Execution Memory Pool en el modelo de memoria unificada de Spark.

---

### 36. ¿Por qué Parquet es el formato de archivo estándar de facto en Data Lakes frente a CSV o JSON?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  - **CSV / JSON (Formatos Basados en Filas - Row-Based y Texto Plano)**:
    - Para calcular la suma de una columna (`SELECT SUM(amount) FROM table`), el motor de procesamiento debe **leer secuencialmente el 100% de los datos de todas las columnas de todo el archivo del disco**, desperdiciando ancho de banda de I/O masivo. No contienen tipos de datos formales (todo es texto).
  - **Apache Parquet (Formato Columnar Binario)**:
    - **Almacenamiento Columnar**: Cada columna se almacena en bloques contiguos en disco. Spark solo lee los bytes de la columna `amount`, ignorando las otras 50 columnas (**Column Pruning**).
    - **Metadatos y Estadísticas Integradas**: Cada bloque (*Row Group*) almacena estadísticas mínimas y máximas (`min`, `max`, `count`) de cada columna. Si filtras `WHERE date = 2025`, Spark salta bloques enteros sin leerlos (**Predicate Pushdown / Block Skipping**).
    - **Compresión Extrema**: Al agrupar datos del mismo tipo en una columna, algoritmos como Snappy o Zstandard logran ratios de compresión del 75% al 90% comparado con texto plano.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Recomendar almacenar terabytes de datos históricos en CSVs sin comprimir para analítica en la nube.
  - 🟢 **Green Flag**: Analizar el ahorro directo en costes de AWS Athena / S3 gracias a la reducción de bytes escaneados con Parquet.

---

### 37. ¿Cuál es la diferencia entre Broadcast Variables y Acumuladores (Accumulators) en Spark?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  Variables compartidas entre el Driver y los Executors distribuidos:
  - **Broadcast Variables (Solo Lectura - Read-Only)**:
    - Permiten enviar una variable grande de solo lectura (ej. un diccionario de búsqueda o modelo ML de 100MB) a cada nodo **una sola vez**, en lugar de enviarla copiada dentro de cada tarea individual en la red.
    - Los executors solo pueden leer su valor (`broadcast_var.value`), nunca modificarlo.
  - **Accumulators (Solo Escritura - Write-Only para los Workers)**:
    - Variables que los executors pueden incrementar o agregar mediante operaciones asociativas y conmutativas (ej. un contador global de registros corruptos o eventos específicos):
      ```python
      error_counter = spark.sparkContext.accumulator(0)
      # Dentro de la función distribuida:
      error_counter.add(1)
      ```
    - **Los executors no pueden leer el valor del acumulador**: únicamente el programa **Driver** tiene permisos para leer el total acumulado (`error_counter.value`).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar leer el valor de un acumulador dentro de una transformación en un executor.
  - 🟢 **Green Flag**: Advertir que si una tarea se reintenta por un fallo de nodo, los acumuladores dentro de transformaciones pueden re-ejecutarse incrementando el contador dos veces.

---

### 38. ¿Qué es y cómo funciona el Repartitioning (`repartition()`) vs `coalesce()` en PySpark?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  Ambos modifican el número de particiones del DataFrame, pero con mecánicas radicalmente distintas:
  - **`repartition(numPartitions)`**:
    - **Ejecuta un SHUFFLE completo a través de la red**.
    - Permite tanto aumentar como disminuir el número de particiones.
    - Redistribuye los datos de forma completamente homogénea y balanceada mediante Round-Robin o hashing de columnas.
  - **`coalesce(numPartitions)`**:
    - **EVITA el Shuffle de red**.
    - **Solo sirve para DISMINUIR el número de particiones** (ej. de 1,000 a 10).
    - Simplemente fusiona particiones existentes que residen en los mismos nodos físicos.
    - **Riesgo**: Si reduces demasiado agresivamente (ej. de 1,000 a 1), toda la computación se forzará en un único executor, perdiendo el paralelismo.
  - **Regla de Oro**: Usar `coalesce()` antes de guardar datos en disco para evitar generar miles de archivos diminutos (*Small Files Problem*); usar `repartition()` cuando se necesite balancear datos tras un filtro masivo o incrementar el paralelismo.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `repartition()` para reducir el número de particiones pagando el coste de un shuffle innecesario.
  - 🟢 **Green Flag**: Conectar `coalesce()` al final del pipeline con la mitigación del problema de los "Small Files" en almacenamiento S3 / HDFS.

---

## 4. Tipado Estático Moderno, Testing con Pytest y Tooling

### 39. ¿Qué es el Subtipado Estructural mediante `Protocol` (PEP 544) y cómo difiere de las Clases Abstractas (`abc.ABC`)?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  - **Subtipado Nominal (`abc.ABC`)**:
    - Una clase solo es considerada compatible si **hereda explícitamente** de la clase base abstracta (`class MiClase(AbstractRepository):`).
    - Muy rígido; acopla clases de librerías de terceros que no pueden modificar su declaración de herencia.
  - **Subtipado Estructural (`typing.Protocol` - Duck Typing Estático)**:
    - Una clase es compatible con un `Protocol` **si implementa los mismos métodos y atributos con las mismas firmas de tipo, SIN necesidad de heredar de él**:
      ```python
      from typing import Protocol

      class Renderable(Protocol):
        def render(self) -> str: ...

      class Boton: # ¡No hereda de Renderable!
        def render(self) -> str:
          return "<button>Click</button>"

      def dibujar(componente: Renderable): # Válido para Mypy!
        print(componente.render())

      dibujar(Boton()) # Mypy valida con éxito por compatibilidad estructural
      ```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Forzar jerarquías de herencia múltiple complejas con `abc.ABC` para contratos simples.
  - 🟢 **Green Flag**: Utilizar `@runtime_checkable` con `Protocol` si se requiere validar compatibilidad con `isinstance()` en tiempo de ejecución.

---

### 40. ¿Cómo funcionan `TypeVar`, `Generic`, `ParamSpec` y la Varianza (Covarianza vs Contravarianza) en Python?
- **Nivel**: Senior / Staff (Type Gymnastics)
- **Respuesta Técnica**:
  - **`TypeVar`**: Permite definir tipos genéricos: `T = TypeVar('T')`.
  - **Varianza**:
    - **Invariante (Por defecto)**: `List[Gato]` no es compatible con `List[Animal]`, porque podrías agregar un `Perro` a la lista de animales y corromper la lista original de gatos.
    - **Covariante (`covariant=True`)**: Si `Gato` es un `Animal`, entonces `Contenedor[Gato]` es compatible con `Contenedor[Animal]`. Se aplica a contenedores de **solo lectura**.
    - **Contravariante (`contravariant=True`)**: Invierte la relación de herencia. Se aplica a consumidores de datos o argumentos de funciones.
  - **`ParamSpec` (PEP 612)**:
    - Permite tipar decoradores de funciones preservando la firma exacta de argumentos (`*args`, `**kwargs`) de la función decorada para que el autocompletado del IDE no se pierda.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `Any` como firma en decoradores perdiendo el tipado estricto de las funciones envueltas.
  - 🟢 **Green Flag**: Escribir un decorador tipado utilizando `ParamSpec` y `TypeVar` con la nueva sintaxis simplificada de Python 3.12 (`def decorador[**P, R](fn: Callable[P, R]) -> Callable[P, R]:`).

---

### 41. ¿Cuál es la jerarquía de Scopes en Fixtures de Pytest y cómo se gestiona la limpieza con `yield`?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  Una fixture de Pytest provee datos, mocks o dependencias preparadas para las pruebas:
  - **Los 5 Scopes (Ámbitos de Vida)**:
    1. **`function` (Por defecto)**: Se crea y se destruye para cada función de test individual (aislamiento total).
    2. **`class`**: Se instancia una vez por cada clase de tests.
    3. **`module`**: Se instancia una vez por cada archivo `.py` de tests.
    4. **`package`**: Se instancia una vez por cada paquete de tests.
    5. **`session`**: Se instancia **una sola vez para toda la ejecución de la suite de pruebas** (ideal para levantar un contenedor Docker con Testcontainers o inicializar un motor de base de datos).
  - **Limpieza con `yield` (Teardown)**:
    ```python
    @pytest.fixture(scope="session")
    def db_connection():
      conn = create_connection() # 1. Código de configuración (Setup)
      yield conn                 # 2. Se entrega el recurso al test
      conn.close()               # 3. Código de limpieza (Teardown automático al final)
    ```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Levantar una base de datos pesada en cada test individual con scope `function` haciendo que la suite tarde 40 minutos en correr.
  - 🟢 **Green Flag**: Utilizar fixtures parametrizadas y fixtures autoejecutables (`autouse=True`).

---

### 42. ¿Cómo se utiliza `@pytest.mark.parametrize` para eliminar la duplicación de código en pruebas unitarias?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  Permite ejecutar la misma prueba con múltiples combinaciones de entradas y salidas esperadas:
  ```python
  @pytest.mark.parametrize("entrada,esperado", [
    ("alex@corp.com", True),
    ("invalido@", False),
    ("", False),
    ("sin-arroba.com", False),
  ], ids=["valido", "falta_dominio", "vacio", "sin_arroba"])
  def test_validacion_email(entrada, esperado):
    assert es_email_valido(entrada) == esperado
  ```
  - Cada tupla se ejecuta como un **test independiente y aislado**: si una falla, las demás continúan reportando su estado.
  - El argumento `ids` genera nombres descriptivos limpios en la consola del test runner para depuración instantánea.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Escribir bucles `for` manuales con aserciones dentro de una sola prueba unitaria (si el primer caso falla, aborta el test sin probar los demás).
  - 🟢 **Green Flag**: Utilizar parametrización apilada para generar productos cartesianos de casos borde automáticamente.

---

### 43. ¿Cuál es el peligro de usar `unittest.mock.patch` con rutas de importación incorrectas (The "Where to Patch" rule)?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **La Regla de Oro de Mocking (Ned Batchelder)**: *"Parchea el objeto en el lugar donde se USA, no en el lugar donde se DEFINE"*.
  - **El Fallo Común**:
    - Tienes un módulo `servicios/pagos.py` que hace: `from libreria.api import StripeClient`.
    - En tu test escribes:
      ```python
      # ERROR: Parchea la definición original en el paquete externo, pero pagos.py ya importó su propia referencia local:
      @patch('libreria.api.StripeClient')
      def test_pago(mock_stripe):
        ...
      ```
    - El test fallará porque `pagos.py` seguirá usando la clase real sin mockear.
  - **La Forma Correcta**:
    ```python
    # CORRECTO: Parchea el namespace local del módulo que está consumiendo la clase:
    @patch('servicios.pagos.StripeClient')
    def test_pago(mock_stripe):
      ...
    ```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Luchar durante horas con mocks que "no funcionan" y no saber explicar la regla de importación de namespaces de Python.
  - 🟢 **Green Flag**: Utilizar `autospec=True` en `patch()` para garantizar que el mock falle si intentas llamar a métodos inexistentes en la clase real.

---

### 44. ¿Por qué Ruff ha reemplazado a Flake8, Black, Isort y Pylint en el ecosistema moderno de Python?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **El Problema Histórico**: Un pipeline de CI de Python típico ejecutaba múltiples herramientas escritas en Python: Black (formateo), Flake8 (linting de estilo), Isort (orden de importaciones), Pydocstyle (docstrings) y Bandit (seguridad). Ejecutar todas tardaba decenas de segundos o minutos en bases de código grandes.
  - **Ruff**:
    - Desarrollado en **Rust por Astral**.
    - Reemplaza a más de 40 plugins y herramientas diferentes de Python en un único binario universal.
    - **Entre 10x y 100x más rápido**: Parsea y formatea un monorrepositorio con 500,000 líneas de código en **menos de 0.2 segundos**, eliminando por completo la fricción en pre-commit hooks y acelerando el Lead Time de CI.
    - Configuración centralizada unificada en el archivo estándar `pyproject.toml`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Mantener 5 herramientas obsoletas independientes configuradas con archivos `.flake8`, `.isort.cfg` dispersos.
  - 🟢 **Green Flag**: Demostrar la configuración unificada de Ruff con reglas de autofix automático en `pyproject.toml`.

---

### 45. ¿Cómo funciona Mypy en modo estricto (`--strict`) y cómo gestionar librerías de terceros sin tipos (Type Stubs / Typeshed)?
- **Nivel**: Senior / Staff
- **Respuesta Técnica**:
  Mypy es el verificador de tipos estático oficial de Python:
  - **`mypy --strict`**: Activa todas las comprobaciones rigurosas:
    - Prohíbe tipos dinámicos (`disallow_any_generics = True`).
    - Exige que el 100% de las funciones tengan anotaciones de tipo completas en argumentos y retornos.
    - Prohíbe el uso de funciones sin tipar dentro de código tipado.
  - **Librerías de Terceros sin Tipos**:
    - Muchas librerías legadas en `pip` no incluyen metadatos de tipos (`py.typed`). Mypy arrojará errores: `Cannot find implementation or library stub for module`.
    - **Soluciones**:
      1. Instalar paquetes de stubs de la comunidad Typeshed: `pip install types-requests types-PyYAML`.
      2. Si la librería no tiene stubs públicos, crear archivos `.pyi` propios (*Stub Files*) en una carpeta local tipando únicamente las funciones consumidas.
      3. Como último recurso, configurar exclusiones explícitas quirúrgicas en `pyproject.toml` (`[[tool.mypy.overrides]] ignore_missing_imports = true`).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Configurar `ignore_missing_imports = True` de forma global para todo el proyecto, desactivando la comprobación de tipos de todas las dependencias.
  - 🟢 **Green Flag**: Explicar el archivo marcador estándar PEP 561 **`py.typed`** para indicar que un paquete propio exporta tipos.

---

### 46. ¿Qué es y cómo funciona el operador Walrus (`:=`) introducido en Python 3.8?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  El operador de expresión de asignación (**Walrus Operator `:=`**) permite **asignar un valor a una variable y retornar ese mismo valor dentro de una única expresión**:
  ```python
  # Tradicional (verboso y repetitivo):
  line = file.readline()
  while line:
    process(line)
    line = file.readline()

  # Con Walrus Operator (conciso y limpio):
  while (line := file.readline()):
    process(line)
  ```
  - Muy potente en filtrado de listas y comprensión de datos evitando cálculos duplicados costosos:
    ```python
    # Calcula expensive_calc(x) una sola vez por elemento:
    resultados = [val for x in datos if (val := expensive_calc(x)) > 10]
    ```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Confundir el operador de asignación ordinario `=` (que es una sentencia y no retorna valor) con el operador Walrus `:=` (que es una expresión).
  - 🟢 **Green Flag**: Utilizar el operador Walrus para evitar llamadas redundantes a expresiones regulares (`if match := pattern.search(text):`).

---

### 47. ¿Qué es el Structural Pattern Matching (`match / case`) introducido en Python 3.10 y por qué supera a los bloques `if/elif`?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  A diferencia de un simple `switch` de C o Java, el Pattern Matching de Python (PEP 634) es un **motor completo de deconstrucción y verificación de formas de datos**:
  ```python
  def procesar_comando(evento):
    match evento:
      case {"tipo": "click", "coordenadas": (x, y)}:
        # Deconstruye un diccionario y desempaqueta la tupla en variables locales x e y
        return f"Click en {x}, {y}"
      case {"tipo": "tecla", "codigo": int(c)} if c > 0: # Con Guard de condición
        return f"Tecla {c}"
      case [primero, *resto]: # Deconstrucción de secuencias
        return f"Lista con cabeza {primero}"
      case _:
        return "Comando desconocido"
  ```
  - Permite verificar la estructura, extraer y desempaquetar variables internas de objetos, validar tipos y aplicar condiciones lógicas (*Guards*) de forma declarativa en una sola construcción.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que `match/case` es solo una sintaxis alternativa para escribir `if x == 1: elif x == 2:`.
  - 🟢 **Green Flag**: Demostrar cómo desempaqueta dataclasses o clases de dominio mediante `case Clase(attr1=val1, attr2=val2):`.

---

### 48. ¿Qué son los Generadores Asíncronos (`async for`) y los Context Managers Asíncronos (`async with`)?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Generador Asíncrono (`async def` con `yield`)**:
    - Implementa el protocolo `__anext__()`:
      ```python
      async def fetch_pages(url: str):
        while url:
          data = await client.get(url)
          yield data["items"]
          url = data.get("next_page")
      ```
    - Consumido con la sintaxis **`async for items in fetch_pages(url):`**.
    - Permite transmitir flujos continuos de datos a través de la red (Server-Sent Events, WebSockets, colas de Kafka) procesando cada trozo de forma no bloqueante a medida que llega.
  - **Context Manager Asíncrono**:
    - Implementa los métodos `__aenter__(self)` y `__aexit__(self, exc_type, exc_val, exc_tb)` que retornan corrutinas.
    - Se consume con **`async with aiohttp.ClientSession() as session:`**.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar usar un `for` ordinario sobre un generador asíncrono arrojando un error de tipo.
  - 🟢 **Green Flag**: Utilizar generadores asíncronos para streaming de respuestas de modelos de IA / LLMs en FastAPI sin acumular la respuesta completa en RAM.

---

### 49. ¿Por qué usar un argumento mutable por defecto (`def append_to(val, lista=[])`) es uno de los bugs más famosos de Python?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  En Python, las funciones son objetos de primera clase. **Los valores predeterminados de los argumentos de una función se evalúan UNA SOLA VEZ en el momento en que la función se DEFINE (tiempo de carga del módulo)**, y no en cada llamada en tiempo de ejecución:
  - Si defines `def agregar(item, lista=[]):`, la lista vacía `[]` se almacena físicamente dentro del objeto de la función en su atributo `__defaults__`.
  - Si invocas `agregar(1)` y luego `agregar(2)`, ambas llamadas mutarán la **misma instancia física de la lista en memoria**:
    ```python
    print(agregar(1)) # [1]
    print(agregar(2)) # [1, 2] -- ¡Bug!
    ```
  - **La Solución Estándar (Sentinel Pattern con `None`)**:
    ```python
    def agregar(item, lista=None):
      if lista is None:
        lista = [] # Asigna una lista nueva e independiente en cada ejecución
      lista.append(item)
      return lista
    ```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: No saber explicar por qué ocurre el bug o proponer soluciones que no usan `None`.
  - 🟢 **Green Flag**: Inspeccionar el atributo `funcion.__defaults__` en consola para demostrar dónde reside el objeto mutable en el Heap.

---

### 50. ¿Cómo funciona la Inmutabilidad y la validación en Dataclasses con `frozen=True` y `kw_only=True`?
- **Nivel**: Junior / Mid-Level
- **Respuesta Técnica**:
  El módulo estándar `dataclasses` (PEP 557) genera automáticamente métodos boilerplate (`__init__`, `__repr__`, `__eq__`, `__hash__`) a partir de anotaciones de tipo:
  - **`@dataclass(frozen=True)`**:
    - Hace que la instancia sea **inmutable**: cualquier intento de mutar un atributo (`obj.x = 10`) arroja un error fatal `FrozenInstanceError`.
    - Al ser inmutable, genera automáticamente un método `__hash__()`, permitiendo que las instancias de la dataclass puedan ser utilizadas como **claves en diccionarios o elementos en conjuntos (`set`)**.
  - **`kw_only=True` (Python 3.10+)**:
    - Fuerza a que todos los atributos deban ser pasados obligatoriamente como **argumentos nombrados** al instanciar la clase (`Point(x=1, y=2)`), prohibiendo argumentos posicionales ambiguos.
  - **Validación con `__post_init__`**: Permite ejecutar comprobaciones de invariantes de dominio inmediatamente después de que el constructor inicializa los campos.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Escribir clases normales con 50 líneas de código para representar entidades de datos puras sin usar `dataclass`.
  - 🟢 **Green Flag**: Conectar `@dataclass(frozen=True, slots=True)` para obtener máxima inmutabilidad y mínimo consumo de memoria RAM.


---

### 51. ¿Cómo funcionan las Metaclases en Python (`type`) y cómo reemplaza `__init_subclass__` la mayoría de sus casos de uso tradicionales?
- **Nivel**: Senior / Staff Python Engineer
- **Respuesta Técnica**:
  - **Metaclases (`type` como metaclase por defecto)**:
    - En Python, las clases son objetos, y la "clase de una clase" es una metaclase. Por defecto, todas las clases son instancias de `type`.
    - Al definir una clase `class Foo: pass`, Python ejecuta internamente: `Foo = type('Foo', (bases,), {attributes})`.
    - Una metaclase personalizada hereda de `type` y sobreescribe `__new__(mcs, name, bases, namespace)` para interceptar, modificar o validar la estructura de la clase antes de que sea instanciada en memoria.
  - **Modernización con `__init_subclass__` (PEP 487 en Python 3.6+)**:
    - Las metaclases introducen fuerte complejidad y problemas de herencia múltiple ("metaclass conflict").
    - `__init_subclass__` permite a una clase base interceptar la creación de cualquier subclase de forma mucho más limpia y directa:
```python
class PluginBase:
    registry: dict[str, type['PluginBase']] = {}

    def __init_subclass__(cls, plugin_name: str, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'execute'):
            raise TypeError(f"La subclase {cls.__name__} debe implementar execute()")
        cls.registry[plugin_name] = cls

class AudioPlugin(PluginBase, plugin_name="audio_processor"):
    def execute(self):
        return "Processing audio"
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar metaclases complejas para registros simples de subclases o validaciones de atributos donde `__init_subclass__` es el estándar idiomático moderno.
  - 🟢 **Green Flag**: Saber cuándo una metaclase sigue siendo estrictamente necesaria (ej. modificar dinámicamente el orden del namespace mediante `__prepare__` antes de evaluar el cuerpo de la clase, como hace Enum).

---

### 52. ¿Cómo opera el Protocolo de Descriptores (`__get__`, `__set__`, `__delete__`) y cómo sustenta `@property`, `classmethod` y métodos en CPython?
- **Nivel**: Senior / Core Python Developer
- **Respuesta Técnica**:
  - **Definición**: Un descriptor es cualquier objeto que define al menos uno de los métodos `__get__`, `__set__` o `__delete__` del protocolo.
  - **Data Descriptor vs Non-Data Descriptor**:
    - **Data Descriptor**: Define `__set__` o `__delete__` (además de `__get__`). **Tiene precedencia absoluta sobre el `__dict__` de la instancia**: si buscas un atributo que coincide con un data descriptor, Python invoca el descriptor sin consultar el diccionario de la instancia.
    - **Non-Data Descriptor**: Solo define `__get__` (ej. funciones estándar y `@classmethod`). Si la instancia define un atributo con el mismo nombre en su `__dict__`, el valor de la instancia tiene prioridad sobre el descriptor.
  - **Cómo funcionan los métodos en Python**:
    - Una función normal es un non-data descriptor. Cuando accedes a `instancia.metodo`, Python invoca `funcion.__get__(instancia, TipoInstancia)`, el cual retorna un objeto **MethodType** enlazado (*Bound Method*) que inyecta automáticamente la instancia como primer argumento (`self`).
  - **Implementación de un Validador de Tipo con Descriptor**:
```python
class TypedField:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError(f"{self.name} debe ser un entero")
        instance.__dict__[self.name] = value
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer que el decorador `@property` es simplemente una clase que implementa los métodos `__get__` y `__set__` del protocolo de descriptores.
  - 🟢 **Green Flag**: Explicar la prioridad de búsqueda en la resolución de atributos (`__getattribute__` -> Data Descriptors -> Instance `__dict__` -> Non-Data Descriptors -> Class `__dict__` -> `__getattr__`).

---

### 53. ¿Cómo funciona internamente el Asignador de Memoria de CPython (PyMalloc) y su jerarquía de Arenas, Pools y Blocks?
- **Nivel**: Staff Python / Systems Engineer
- **Respuesta Técnica**:
  - **Jerarquía de PyMalloc (Optimizado para objetos pequeños <= 512 bytes)**:
    - En Python, la mayoría de los objetos son pequeños (enteros, tuplas, strings cortos). Llamar directamente a `malloc()` del sistema operativo causaría fragmentación severa y baja eficiencia de CPU.
    1. **Block (Bloque)**: La unidad básica de memoria. Varían en múltiplos de 8 bytes (desde 8 hasta 512 bytes: 8, 16, 24, ..., 512). Un bloque solo almacena un objeto de un tamaño de clase específico.
    2. **Pool (Piscina)**: Bloque de memoria contiguo de exactamente **4 KB** (equivalente al tamaño de una página de memoria virtual del SO). Un Pool está compuesto por bloques de un tamaño homogéneo. Mantiene una lista enlazada de bloques libres (`freeblock`).
    3. **Arena**: Fragmento contiguo de memoria virtual de **256 KB** asignado directamente mediante `malloc()` / `mmap()`. Contiene 64 Pools de 4 KB.
  - **Comportamiento de Liberación de Memoria hacia el Sistema Operativo**:
    - CPython **solo devuelve memoria física al sistema operativo cuando una Arena completa de 256 KB queda 100% vacía**.
    - Si una Arena tiene 63 Pools vacíos pero un único Pool conserva un solo objeto activo de 16 bytes, la Arena entera permanece en el espacio de memoria virtual del proceso, lo que explica por qué el RSS de memoria de un proceso Python rara vez decrece tras procesar grandes volúmenes de datos.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Asumir que invocar `del variable` o `gc.collect()` devuelve inmediatamente la memoria física al sistema operativo.
  - 🟢 **Green Flag**: Explicar el uso de `tracemalloc` y `gc.get_objects()` para depurar picos de retención de memoria y pools fragmentados.

---

### 54. ¿Qué cambia con el No-GIL (Free-Threaded CPython - PEP 703) en Python 3.13 y cómo se gestiona la concurrencia a nivel de C?
- **Nivel**: Principal / Staff Python Architect
- **Respuesta Técnica**:
  - **El Hito Histórico del PEP 703**:
    - Python 3.13 introduce soporte experimental para compilar CPython con la bandera `--disable-gil`.
    - Elimina el Global Interpreter Lock (GIL), permitiendo que múltiples hilos de Python se ejecuten simultáneamente en núcleos de CPU físicos independientes para código intensivo en cómputo.
  - **Nuevos Mecanismos Internos de Sincronización**:
    1. **Mimalloc**: CPython reemplaza PyMalloc con el asignador de memoria seguro para hilos de alto rendimiento de Microsoft (**mimalloc**), diseñado para concurrencia multi-hilo escalable.
    2. **Biased Reference Counting**: El conteo de referencias tradicional no es seguro entre hilos sin bloqueos atómicos. PEP 703 introduce un esquema donde el hilo que creó el objeto utiliza un conteo rápido no atómico, mientras que los hilos foráneos utilizan instrucciones atómicas solo cuando es estrictamente necesario.
    3. **Immortal Objects (PEP 683)**: Objetos inmutables del core (`None`, `True`, `False`, cadenas pequeñas) se marcan con un flag inmutable y su conteo de referencias nunca se modifica, evitando contención de memoria entre hilos.
    4. **Locks granulares a nivel de contenedor**: Diccionarios y listas internas implementan bloqueos finos independientes para operaciones de mutación concurrente.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que el No-GIL hace que el código de aplicación sea mágicamente seguro para concurrencia sin necesidad de locks o primitivas de sincronización (`threading.Lock`) a nivel de lógica de negocio.
  - 🟢 **Green Flag**: Discutir el impacto en extensiones C existentes (Cython, NumPy, PyO3) y el tradeoff temporal del 10-15% de degradación en rendimiento de un solo hilo.

---

### 55. ¿Cómo construir extensiones nativas de alto rendimiento para Python usando Rust con PyO3 y Maturin frente a Cython?
- **Nivel**: Senior / Staff Python Engineer
- **Respuesta Técnica**:
  - **Cython vs Rust con PyO3**:
    - **Cython**: Es un dialecto híbrido de Python y C. Potente pero propenso a errores de punteros en C (segfaults, buffer overflows, gestión manual de memoria en bloques `nogil`).
    - **PyO3 + Maturin**: Permite escribir módulos nativos de Python en Rust puro, garantizando seguridad de memoria en tiempo de compilación (*Memory Safety* sin Garbage Collector), tipado estricto y concurrencia sin carreras de datos (*Data-race Freedom*).
  - **Implementación de un Módulo PyO3**:
```rust
// lib.rs
use pyo3::prelude::*;

#[pyfunction]
fn compute_heavy_hash(data: &[u8]) -> PyResult<u64> {
    // Código en Rust nativo a máxima velocidad de CPU
    let sum: u64 = data.iter().map(|&b| b as u64).sum();
    Ok(sum)
}

#[pymodule]
fn my_fast_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_heavy_hash, m)?)?;
    Ok(())
}
```
  - **Compilación y Empaquetado**:
    - `maturin develop`: Compila y enlaza el archivo binario `.so` / `.pyd` directamente en el virtualenv de Python activo.
    - Proyectos líderes del ecosistema moderno de Python (como **Pydantic v2**, **Ruff**, **Polars**) han migrado su núcleo de C/Python a Rust con PyO3, logrando incrementos de velocidad de $20\times$ a $50\times$.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Proponer reescribir toda una aplicación en Go o C cuando solo un algoritmo numérico o parser del 5% del código genera el cuello de botella.
  - 🟢 **Green Flag**: Explicar la liberación del GIL en Rust con `py.allow_threads()` para cálculos intensivos multi-core.

---

### 56. ¿Cómo opera internamente el Event Loop de Asyncio y en qué se diferencia uvloop de la implementación por defecto?
- **Nivel**: Senior Python Backend / SRE
- **Respuesta Técnica**:
  - **Asyncio Event Loop por defecto (SelectorEventLoop)**:
    - Escrito en Python puro sobre el módulo estándar `selectors`.
    - Utiliza las llamadas del sistema del kernel del SO (`epoll` en Linux, `kqueue` en macOS/BSD) para multiplexar sockets I/O no bloqueantes.
    - Cuando una corutina hace un `await socket.recv()`, Asyncio registra el descriptor de archivo en el selector con un callback y cede el control al bucle de eventos.
    - *Limitación*: La sobrecarga de interpretar callbacks y envoltorios de clases en Python puro en cada tick del bucle limita el throughput máximo a unas 15,000 - 25,000 peticiones por segundo por worker.
  - **uvloop (Reemplazo ultra-rápido en C)**:
    - Desarrollado por MagicStack (creadores de EdgeDB).
    - Escrito en **Cython y C** directamente sobre la librería de eventos de alto rendimiento de Node.js (**libuv**).
    - Reemplaza el bucle de eventos estándar con una sola línea:
```python
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```
    - **Rendimiento**: Multiplica por $2\times$ a $4\times$ la velocidad de procesamiento de I/O y corutinas, permitiendo que frameworks como FastAPI / Sanic alcancen más de 100,000 rps en benchmarks HTTP.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Confundir concurrencia cooperativa (Asyncio cede el control voluntariamente en `await`) con concurrencia preventiva (hilos o procesos con expulsión forzada por el kernel).
  - 🟢 **Green Flag**: Conocer las limitaciones de uvloop en Windows (donde se utiliza `ProactorEventLoop` basado en IOCP) y la incompatibilidad con ciertas APIs heredadas.

---

### 57. ¿Cómo resuelve Pydantic v2 el rendimiento y la validación utilizando `pydantic-core` en Rust?
- **Nivel**: Senior Backend / API Architect
- **Respuesta Técnica**:
  - **El cuello de botella de Pydantic v1**:
    - Validaba y transformaba tipos de datos recorriendo dinámicamente árboles de objetos y ejecutando validadores escritos en Python puro.
    - En APIs de alto volumen serializando miles de objetos JSON complejos, Pydantic v1 consumía hasta el 60-70% del tiempo total de la petición en CPU.
  - **Arquitectura de Pydantic v2 (`pydantic-core`)**:
    1. **Rust Engine**: Toda la lógica de serialización, deserialización y validación de tipos se reescribió en un crate nativo de Rust (`pydantic-core`).
    2. **Parse directamente desde JSON sin objeto intermedio**:
       - En v1: `JSON String -> json.loads() (dict de Python) -> Pydantic Model`.
       - En v2: `pydantic-core` parsea los bytes de JSON directamente en memoria de Rust mapeándolos a los campos del modelo con validación simultánea, eliminando la creación masiva de diccionarios efímeros en el Heap de Python.
    3. **Schema Generation**: Al definir una clase `BaseModel`, Python solo genera un esquema JSON/estructural estático una sola vez y lo envía a Rust para compilar un validador altamente optimizado.
    - **Ganancia**: De $5\times$ a $50\times$ mayor velocidad y consumo de memoria drásticamente inferior.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar validaciones manuales complejas con bucles `for` o diccionarios sin tipar por desconocer el rendimiento de Pydantic v2.
  - 🟢 **Green Flag**: Utilizar `model_validate_json()` para saltarse la conversión intermedia de `json.loads()` y aprovechar validadores de campo nativos con `@field_validator(mode='before'|'after')`.

---

### 58. ¿Cómo funcionan `select_related` y `prefetch_related` en el ORM de Django para eliminar el problema de las consultas $N+1$?
- **Nivel**: Senior Django / Database Architect
- **Respuesta Técnica**:
  - **Problema de la consulta $N+1$**:
    - Al iterar sobre 1,000 pedidos e imprimir el nombre de su cliente (`order.customer.name`), Django ejecuta 1 consulta para obtener los 1,000 pedidos, y luego **1,000 consultas SQL individuales adicionales** (una por cada cliente), colapsando la base de datos.
  - **`select_related` (Join SQL en una sola query)**:
    - **Tipo de relaciones**: Claves foráneas individuales (`ForeignKey`) y relaciones uno a uno (`OneToOneField`).
    - **Mecanismo**: Genera una única consulta SQL combinando las tablas mediante un `INNER JOIN` o `LEFT OUTER JOIN`.
    - Toda la información de la entidad relacionada viene en el mismo result set de la base de datos; cero consultas adicionales al acceder al atributo.
  - **`prefetch_related` (Consultas independientes en memoria)**:
    - **Tipo de relaciones**: Relaciones de muchos a muchos (`ManyToManyField`), claves foráneas inversas (`1 a N`) o Generic Foreign Keys.
    - **Mecanismo**: Django ejecuta **exactamente 2 consultas SQL**:
      1. `SELECT * FROM orders WHERE ...;`
      2. `SELECT * FROM customers WHERE id IN (1, 2, 3, ...);`.
    - Luego, Django realiza el cruce y mapeo de las entidades en la memoria RAM del proceso Python utilizando diccionarios indexados por clave primaria.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `select_related` sobre un `ManyToManyField` (genera un producto cartesiano masivo de filas duplicadas en SQL).
  - 🟢 **Green Flag**: Usar la clase `Prefetch` avanzada para filtrar, ordenar o limitar las relaciones precargadas en el segundo query (`Prefetch('orders', queryset=Order.objects.filter(is_active=True))`).

---

### 59. ¿Cómo opera el patrón "Unit of Work" e "Identity Map" en SQLAlchemy 2.0 y cómo difiere del patrón Active Record?
- **Nivel**: Senior Backend / Data Engineer
- **Respuesta Técnica**:
  - **Active Record (Django ORM / Ruby on Rails)**:
    - Cada objeto del modelo representa directamente una fila de la tabla de la base de datos y contiene los métodos para persistirse a sí mismo (`user.save()`, `user.delete()`).
    - Alto acoplamiento entre la lógica de negocio y el esquema de la base de datos; ejecuta sentencias SQL de forma inmediata en cada llamada a método.
  - **Data Mapper + Unit of Work (SQLAlchemy)**:
    - Las entidades de dominio están completamente desacopladas de la persistencia (modelos limpios).
    - **Unit of Work (`Session`)**:
      - Mantiene una lista de objetos modificados, creados y borrados durante una transacción de negocio.
      - **Diferimiento atómico**: Las modificaciones en los objetos no envían SQL a la base de datos de inmediato. Cuando se invoca `session.commit()`, la Unit of Work calcula el grafo de dependencias de claves foráneas y ejecuta las sentencias SQL en el orden matemáticamente correcto y en un único lote agrupado (*Batch Execution*).
    - **Identity Map (Mapa de Identidades)**:
      - Dentro de la misma sesión, SQLAlchemy mantiene un diccionario interno de objetos cargados por clave primaria (`(User, 42) -> instancia`).
      - Si ejecutas dos queries que solicitan el usuario con ID 42, SQLAlchemy devuelve exactamente **la misma referencia de objeto en memoria física**, garantizando coherencia de estado y evitando consultas SQL redundantes.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Crear una nueva instancia de `Session()` en cada función individual en lugar de gestionar el ciclo de vida de la sesión por petición HTTP (Session per Request).
  - 🟢 **Green Flag**: Explicar la sintaxis moderna 2.0 basada en `select(User).where(...)` y la integración asíncrona nativa con `AsyncSession` y `asyncpg`.

---

### 60. ¿Cómo configurar la concurrencia en Celery (`prefork` vs `gevent` vs `eventlet`) y cómo resolver la pérdida de tareas ante reinicios de workers?
- **Nivel**: Senior Backend / Distributed Systems
- **Respuesta Técnica**:
  - **Modelos de Ejecución de Celery Pools**:
    - **`prefork` (Por defecto - Procesos múltiples)**:
      - Basado en `multiprocessing` de Python. Aislamiento de memoria total; esquiva el GIL.
      - Ideal para: **Tareas intensivas en CPU** (procesamiento de imágenes, criptografía, cómputo numérico).
      - Ineficiente si hay miles de tareas de I/O bloqueante (cada proceso consume 50-100 MB de RAM).
    - **`gevent` / `eventlet` (Greenlets cooperativos)**:
      - Ejecuta miles de tareas concurrentes en un único proceso mediante corutinas y monkey-patching del stack de red.
      - Ideal para: **Tareas de I/O masivo** (enviar miles de emails, web scraping, webhooks). Inútil para tareas pesadas de CPU (se bloquean mutuamente).
  - **Garantías de Entrega y Tolerancia a Fallos**:
    - **Problema de ACK prematuro**: Por defecto, Celery confirma (*ACK*) la tarea al broker (RabbitMQ/Redis) en el momento en que el worker **recibe** el mensaje, no cuando termina de procesarlo. Si el contenedor del worker muere a mitad del proceso, la tarea se pierde para siempre.
    - **Solución con Late ACK y Reintentos Seguros**:
```python
@app.task(
    bind=True,
    acks_late=True, # Confirma el mensaje SOLO tras ejecutar con éxito la función
    reject_on_worker_lost=True, # Si el worker muere por OOM, re-encola la tarea
    max_retries=3
)
def process_payment(self, payment_id):
    # La lógica debe ser IDEMPOTENTE porque acks_late puede re-ejecutar la tarea
    ...
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Configurar `acks_late=True` en tareas que no son idempotentes (puede provocar dobles cobros a clientes ante reinicios de red).
  - 🟢 **Green Flag**: Configurar `worker_prefetch_multiplier=1` para evitar que un worker acapare tareas largas en su buffer local mientras otros workers permanecen ociosos.

---

### 61. ¿Cómo funciona el Optimizador Catalyst y el Motor Tungsten en Apache PySpark para procesamiento distribuido a gran escala?
- **Nivel**: Senior Data Engineer / Spark Architect
- **Respuesta Técnica**:
  - **Catalyst Optimizer (Árboles de Expresión y Transformación)**:
    - PySpark compila las transformaciones del DataFrame API en un plan de ejecución lógico.
    - Fases del pipeline de Catalyst:
      1. *Analysis*: Resuelve nombres de columnas y tipos contra el catálogo de metadatos.
      2. *Logical Optimization*: Aplica optimizaciones basadas en reglas:
         - **Predicate Pushdown**: Mueve los filtros (`.filter(col("age") > 30)`) directamente a la fuente de datos (ficheros Parquet o tablas JDBC) para leer únicamente las filas necesarias de disco.
         - **Projection Pruning**: Lee únicamente las columnas requeridas, descartando el resto antes de transferir datos por la red.
      3. *Physical Planning*: Genera múltiples planes físicos y selecciona el más eficiente según un modelo de coste.
  - **Project Tungsten (Optimización de Hardware)**:
    - **Off-Heap Memory Management**: Gestiona la memoria directamente en formato binario compacto fuera del Heap de la JVM (usando `sun.misc.Unsafe`), eliminando por completo la sobrecarga de objetos Java y las pausas del Garbage Collector.
    - **Whole-Stage Code Generation**: Sintetiza consultas complejas en una sola función compacta de bytecode de Java que cabe completamente en el caché L1/L2 del procesador físico.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar RDDs con lambdas de Python en PySpark (obliga a serializar/deserializar objetos entre la JVM y el intérprete de Python mediante Py4J en cada fila, perdiendo toda optimización de Catalyst).
  - 🟢 **Green Flag**: Demostrar cómo un `explain(mode="formatted")` revela si se aplicaron Predicate Pushdown y Broadcast Hash Joins.

---

### 62. ¿Cuándo y por qué utilizar un Broadcast Hash Join en PySpark en lugar de un Shuffle Hash Join tradicional?
- **Nivel**: Senior Big Data / PySpark Engineer
- **Respuesta Técnica**:
  - **Shuffle Hash Join tradicional**:
    - Al cruzar dos DataFrames grandes (Tabla A de 1 TB y Tabla B de 500 GB), Spark debe redistribuir los registros de ambas tablas a través de la red física del clúster basándose en el hash de la clave de unión (**Shuffle**).
    - El Shuffle es la operación más costosa y lenta en computación distribuida: satura la red, escribe datos intermedios a disco y genera cuellos de botella por sesgo de particiones (*Data Skew*).
  - **Broadcast Hash Join (BHJ)**:
    - Se utiliza cuando una de las dos tablas es **pequeña** (por defecto < 10 MB, configurable con `spark.sql.autoBroadcastJoinThreshold`).
    - **Mecanismo**: El nodo Driver descarga la tabla pequeña completa y la transmite por la red (*broadcast*) a **todos los nodos ejecutores del clúster una sola vez**.
    - Cada ejecutor construye una tabla hash en memoria local con la tabla pequeña y cruza su partición local de la tabla grande **sin transferir un solo byte de la tabla grande por la red (Zero Shuffle)**.
```python
from pyspark.sql.functions import broadcast

# Forzar explícitamente el Broadcast Join
resultado = transacciones_grandes.join(
    broadcast(catalogo_paises_pequeno),
    on="codigo_pais",
    how="inner"
)
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Aplicar `broadcast()` a un DataFrame de 15 GB, provocando un `OutOfMemoryError` inmediato en el nodo Driver de Spark.
  - 🟢 **Green Flag**: Analizar los trade-offs de tamaño de memoria en el Driver frente a la eliminación completa de las fases de Shuffle en el DAG de ejecución.

---

### 63. ¿Cómo opera la nueva sintaxis de Tipado Avanzado en Python 3.10-3.12 (`TypeVar`, `ParamSpec`, `Concatenate` y `Self`)?
- **Nivel**: Senior Python Developer / Library Author
- **Respuesta Técnica**:
  - **`ParamSpec` y `Concatenate` (PEP 612 - Decoradores con Tipado Estricto)**:
    - Históricamente, al escribir un decorador que preservaba la firma de argumentos de la función decorada, `Callable[..., Any]` perdía por completo los tipos de los argumentos.
    - `ParamSpec` captura las variables de parámetros (posicionales y de clave) de una función, permitiendo que herramientas de análisis estático (Mypy, Pyright) mantengan la verificación de tipos exacta a través del decorador:
```python
from typing import Callable, ParamSpec, TypeVar, Concatenate

P = ParamSpec('P')
R = TypeVar('R')

def con_reintentos(fn: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn(*args, **kwargs)
    return wrapper
```
  - **`Self` Type (PEP 673 en Python 3.11+)**:
    - Permite anotar métodos de instancia que retornan la propia instancia (patrón Fluent API / Builder) sin necesidad de declarar un `TypeVar` complejo acoplado a la clase:
```python
from typing import Self

class QueryBuilder:
    def where(self, condition: str) -> Self:
        self.condition = condition
        return self
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `Any` en firmas de decoradores o bibliotecas públicas por no dominar las capacidades modernas del sistema de tipos de Python.
  - 🟢 **Green Flag**: Explicar la diferencia entre covariancia, contravariancia e invariancia en `TypeVar(..., covariant=True)`.

---

### 64. ¿Cómo mitigar fugas de memoria en aplicaciones asíncronas de Python provocadas por tareas huérfanas (`asyncio.create_task`)?
- **Nivel**: Senior Backend / Core Engineer
- **Respuesta Técnica**:
  - **Causa raíz de la fuga**:
    - `asyncio.create_task(coro())` planifica la corutina en el Event Loop en segundo plano.
    - El bucle de eventos **solo mantiene una referencia débil (Weak Reference)** hacia la tarea creada.
    - Si no se almacena una referencia fuerte en una variable o colección:
      1. El Garbage Collector puede destruir la tarea a mitad de su ejecución sin previo aviso, arrojando advertencias silenciosas.
      2. O peor: si la tarea captura variables de contexto en bucles infinitos no cancelados, retiene objetos grandes en el Heap indefinidamente.
  - **Soluciones en Producción**:
    1. **Conjunto de Referencias Fuertes**:
```python
background_tasks: set[asyncio.Task] = set()

def launch_task(coro):
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard) # Limpieza automática al terminar
```
    2. **TaskGroups (PEP 654 en Python 3.11+)**:
       - Reemplaza el uso inseguro de `asyncio.gather()` y `create_task` sueltos mediante concurrencia estructurada (*Structured Concurrency*):
```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(fetch_data_a())
    tg.create_task(fetch_data_b())
# Si alguna falla, cancela automáticamente todas las demás tareas del grupo de forma limpia
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Lanzar `asyncio.create_task()` dentro de controladores de peticiones web sin rastrear su ciclo de vida ni manejar excepciones no capturadas.
  - 🟢 **Green Flag**: Adoptar Concurrencia Estructurada con `asyncio.TaskGroup` para garantizar que ninguna tarea secundaria sobreviva al ámbito del contexto.

---

### 65. ¿Cómo funciona la resolución del grafo de dependencias en el sistema de Dependency Injection de FastAPI?
- **Nivel**: Senior Backend / Framework Specialist
- **Respuesta Técnica**:
  - **El motor `Depends` de FastAPI**:
    - Al definir una ruta con parámetros decorados con `Depends(get_db)`, FastAPI construye un **Grafo Acíclico Dirigido (DAG)** de dependencias en tiempo de inicio de la aplicación.
  - **Mecanismo de Ejecución y Caché en cada Petición**:
    1. **Resolución Topológica**: FastAPI resuelve las dependencias en orden bottom-up: primero las hojas del grafo (ej. configuración, cliente Redis) y luego las dependencias compuestas (ej. servicio de autenticación que depende de la base de datos).
    2. **Mapeo de Caché por Petición (`use_cache=True` por defecto)**:
       - Si 3 sub-dependencias diferentes requieren `Depends(get_current_user)`, FastAPI **ejecuta la función una sola vez** por ciclo de petición HTTP. El resultado se almacena en el diccionario de contexto de la petición y se inyecta en los demás consumidores instantáneamente.
    3. **Manejo de Context Managers con Generadores**:
       - Si una dependencia usa `yield` (ej. `def get_db(): try: yield db finally: db.close()`), FastAPI la envuelve en un generador asíncrono.
       - La fase previa al `yield` corre antes de que el endpoint procese la petición, y el bloque `finally` corre **garantizadamente después** de que la respuesta HTTP se haya transmitido al cliente (incluso si se arrojó una excepción HTTP 500 no controlada).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Abrir conexiones de base de datos directamente en el cuerpo del endpoint sin usar el patrón de dependencias con `yield`, provocando fugas de conexiones en el pool.
  - 🟢 **Green Flag**: Usar `app.dependency_overrides` en suites de pruebas unitarias para reemplazar clientes de infraestructura reales por mocks en memoria de forma limpia.

---

### 66. ¿Cómo optimizar el uso de memoria con `__slots__` y cuándo está contraindicado su uso?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **El coste estándar de `__dict__`**:
    - Por defecto, cada instancia de una clase en Python almacena sus atributos en un diccionario dinámico privado (`__dict__`). Un diccionario vacío en CPython ocupa un mínimo de 104 a 144 bytes de memoria física en el Heap.
    - Si se instancian 5 millones de objetos (ej. registros procesados en memoria), el coste de los diccionarios satura gigabytes de RAM.
  - **`__slots__`**:
    - Le dice a CPython que reserve un array de punteros de tamaño fijo estático para los atributos especificados, **suprimiendo la creación del diccionario `__dict__`**:
```python
class SensorData:
    __slots__ = ('timestamp', 'sensor_id', 'temperature', 'humidity')
    def __init__(self, t, s, temp, hum):
        self.timestamp = t
        self.sensor_id = s
        self.temperature = temp
        self.humidity = hum
```
    - **Ahorro**: Reduce el consumo de memoria de cada instancia en más de un **60%**, acelerando además el tiempo de lectura/escritura de atributos en un 20%.
  - **Cuándo NO usarlo / Contraindicaciones**:
    - No permite asignar atributos dinámicos arbitrarios en tiempo de ejecución (a menos que se incluya `'__dict__'` explícitamente en el iterable de slots).
    - Herencia múltiple compleja: no se pueden heredar múltiples clases base que definan `__slots__` no vacíos distintos.
    - Si se usa `@dataclass`, se debe activar `@dataclass(slots=True)` en Python 3.10+ para que lo genere de forma automática e idiomática.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Recomendar `__slots__` para todas las clases de una aplicación web (agrega restricciones innecesarias a modelos ORM o clases de configuración donde solo existen 2 instancias).
  - 🟢 **Green Flag**: Identificar su aplicación en pipelines de ingesta de datos de alta frecuencia o nodos de árboles y grafos en memoria.

---

### 67. ¿Cómo funciona la arquitectura de extensiones con CFFI vs ctypes para interoperabilidad con librerías C nativas?
- **Nivel**: Senior Systems / Python Engineer
- **Respuesta Técnica**:
  - **`ctypes` (Módulo estándar en CPython)**:
    - Utiliza `libffi` internamente. Carga bibliotecas dinámicas (`.so`, `.dll`) en tiempo de ejecución de forma dinámica.
    - *Desventaja*: Todo se define en tiempo de ejecución mediante introspección; sin validación del compilador C. Errores tipográficos en firmas de funciones provocan caídas catastróficas inmediatas del proceso (`Segmentation Fault`). Lento al empaquetar y desempaquetar tipos de datos en llamadas recurrentes.
  - **`CFFI` (C Foreign Function Interface - Creado por el equipo de PyPy)**:
    - Permite escribir declaraciones C directas utilizando la sintaxis estándar de cabeceras C (`.h`):
```python
from cffi import FFI
ffi = FFI()
ffi.cdef("""
    int add_numbers(int a, int b);
""")
C = ffi.dlopen("./libmath.so")
result = C.add_numbers(10, 20)
```
    - **Modo ABI vs Modo API**:
      - *Modo ABI*: Igual que ctypes (acceso dinámico a símbolos de la librería compartida).
      - *Modo API (Recomendado)*: CFFI invoca al compilador C del sistema (`gcc`/`clang`) para generar un módulo C compilado intermedio. El compilador C valida los tipos de structs, constantes y alineaciones de memoria **antes** de que el código corra, garantizando seguridad absoluta y rendimiento idéntico a una extensión C nativa.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer que un fallo de memoria en ctypes/CFFI crashea todo el intérprete de Python sin generar una excepción Python capturable.
  - 🟢 **Green Flag**: Explicar la compatibilidad de CFFI con PyPy (JIT compilation) frente a la sobrecarga de la C-API estándar de CPython.

---

### 68. ¿Cómo implementar un Decorador con y sin argumentos preservando la firma de metadatos e introspección con `functools.wraps`?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **El problema de la pérdida de identidad**:
    - Un decorador ingenuo reemplaza la función original por una función interna (`wrapper`).
    - Si se inspecciona `funcion.__name__` o `funcion.__doc__`, mostrarán el nombre y docstring del wrapper. Además, herramientas de documentación automática (Sphinx) y depuradores pierden la firma real de los argumentos.
  - **Solución Universal con `functools.wraps`**:
```python
from functools import wraps
from typing import Callable, Any

def log_execution(prefix: str = "EXEC"):
    """Decorador flexible que soporta argumentos."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn) # Copia __name__, __doc__, __annotations__ y expone __wrapped__
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"[{prefix}] Ejecutando {fn.__name__}")
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@log_execution(prefix="DATABASE")
def query_users(limit: int) -> list[str]:
    """Obtiene lista de usuarios."""
    return ["user1", "user2"][:limit]
```
  - **Acceso a la función original**: `functools.wraps` expone el atributo `query_users.__wrapped__`, permitiendo invocar la función original sin el comportamiento del decorador en pruebas unitarias aisladas.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Escribir decoradores sin utilizar `@wraps`, rompiendo la introspección y el tipado estático en la base de código.
  - 🟢 **Green Flag**: Implementar un decorador híbrido que funcione tanto como `@log` (sin paréntesis) como `@log(prefix="WARN")` mediante inspección de argumentos.

---

### 69. ¿Cómo funciona el algoritmo de Recolección de Basura Generacional en CPython para resolver referencias circulares?
- **Nivel**: Senior / Core Python Engineer
- **Respuesta Técnica**:
  - **Primer mecanismo: Reference Counting (Inmediato y Determinista)**:
    - Cada objeto tiene un campo `ob_refcnt`. Cuando llega a 0, la memoria se libera de inmediato.
    - *Limitación*: Es incapaz de detectar **referencias circulares** (un objeto A referencia a B y B referencia a A; sus contadores nunca bajan a 0 al salir de ámbito).
  - **Segundo mecanismo: Garbage Collector Generacional (Ciclos)**:
    - Solo supervisa objetos contenedores capaces de contener referencias a otros objetos (`dict`, `list`, `set`, instancias de clases; ignora strings y enteros).
    - Divide los objetos en **3 Generaciones (G0, G1, G2)** según su longevidad en base a la hipótesis generacional: "la mayoría de los objetos mueren jóvenes".
      - **Generación 0**: Objetos recién creados. Se escanea con altísima frecuencia (cuando las asignaciones netas superan `threshold0`, típicamente 700).
      - **Generación 1**: Objetos que sobrevivieron a una recolección en G0. Se escanea con menor frecuencia.
      - **Generación 2**: Objetos de larga duración (módulos globales, caches). Se escanea raramente.
  - **Algoritmo de Detección de Ciclos**:
    - El GC construye una lista de contenedores y copia sus `refcnt` a un campo temporal (`gc_refs`).
    - Para cada objeto, resta 1 a los objetos que referencia.
    - Si al final del proceso el `gc_refs` de un grupo de objetos cae a 0, significa que esos objetos solo se referencian entre sí y no hay ningún puntero alcanzable desde el exterior (raíces del programa), por lo que el ciclo completo es destruido de forma segura.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que Python solo tiene Reference Counting o que el GC corre continuamente en tiempo real deteniendo todos los hilos del proceso.
  - 🟢 **Green Flag**: Conocer las optimizaciones de Python 3.12+ para deshabilitar el GC en procesos hijos tras un `fork()` (`gc.freeze()`) para evitar invalidación de memoria Copy-on-Write.

---

### 70. ¿Cómo opera la biblioteca de concurrencia estructurada AnyIO y cómo unifica Asyncio y Trio?
- **Nivel**: Senior Backend / Async Architect
- **Respuesta Técnica**:
  - **El problema de la fragmentación asíncrona**:
    - Las bibliotecas asíncronas escritas exclusivamente para `asyncio` no pueden utilizarse en proyectos basados en `trio` (pionero en concurrencia estructurada sin corutinas huérfanas).
  - **AnyIO**:
    - Capa de abstracción y compatibilidad que traduce primitivas asíncronas a un API unificado y moderno sobre cualquiera de los dos motores (`asyncio` o `trio`).
    - Es la columna vertebral subyacente utilizada por **Starlette**, **FastAPI**, **HTTPX** y **LiteLLM**.
  - **Capacidades Clave**:
    1. **Task Groups Estructurados**: Proporciona grupos de tareas con cancelación en cascada transparente, independiente de la versión de Python.
    2. **Manejo de I/O en Hilos Bloqueantes**:
```python
import anyio

async def endpoint():
    # Ejecuta una función síncrona bloqueante en un worker pool sin congelar el event loop
    resultado = await anyio.to_thread.run_sync(heavy_sync_database_query)
    return resultado
```
    3. **Streams de Memoria y Sockets**: Abstracciones bidireccionales (`MemoryObjectReceiveStream` / `SendStream`) que reemplazan a las colas tradicionales (`asyncio.Queue`) con soporte formal de cierre de canal (*EndOfStream*).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Bloquear el event loop de FastAPI ejecutando código síncrono pesado (como `time.sleep()` o `requests.get()`) directamente dentro de un endpoint `async def`.
  - 🟢 **Green Flag**: Utilizar `anyio.to_thread.run_sync()` o definir el endpoint como `def` síncrono normal para que FastAPI lo despache automáticamente a un pool de subprocesos.

---

### 71. ¿Cómo gestionar transacciones anidadas y Savepoints en bases de datos con Django y SQLAlchemy?
- **Nivel**: Senior Backend / Database Specialist
- **Respuesta Técnica**:
  - **El problema del Commit Anidado**:
    - El estándar SQL relacional no permite transacciones verdaderas anidadas de forma nativa (`BEGIN TRANSACTION` dentro de otro `BEGIN TRANSACTION` arremete error o confirma la transacción exterior).
  - **Implementación mediante Savepoints**:
    - Los ORMs simulan la anidación utilizando puntos de guardado SQL (`SAVEPOINT savepoint_name` y `ROLLBACK TO SAVEPOINT`).
  - **En Django ORM (`transaction.atomic` como Context Manager)**:
```python
from django.db import transaction

with transaction.atomic(): # Inicia la transacción principal externa (BEGIN)
    crear_factura()
    try:
        with transaction.atomic(): # Crea un SAVEPOINT en la base de datos
            procesar_pago_externo()
    except PaymentError:
        # Hace ROLLBACK TO SAVEPOINT únicamente para el pago;
        # la factura creada anteriormente no se cancela
        registrar_intento_fallido()
# Realiza el COMMIT de la transacción externa completa si no hay errores no capturados
```
  - **Cuidado crítico en Postgres**: Si una sentencia SQL arroja un error dentro de un bloque `atomic` y no se usa un Savepoint, PostgreSQL marca la transacción completa como abortada (`Current transaction is aborted, commands ignored until end of transaction block`), obligando a cancelar la transacción entera.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar capturar excepciones de base de datos dentro de un bloque de transacción sin entender que Postgres invalida toda la transacción si no hubo un Savepoint previo.
  - 🟢 **Green Flag**: Utilizar `transaction.on_commit(callback)` en Django para despachar emails o tareas asíncronas únicamente cuando la transacción principal se confirme físicamente en el disco de la base de datos.

---

### 72. ¿Cómo funciona la optimización de código en Python mediante el JIT Compiler experimental en Python 3.13?
- **Nivel**: Staff Python / Systems Specialist
- **Respuesta Técnica**:
  - **Evolución del proyecto Faster CPython (PEP 659 - Specialized Adaptive Interpreter)**:
    - Introducido en Python 3.11: el intérprete detecta "bytecode caliente" en tiempo de ejecución y sustituye opcodes genéricos (`BINARY_OP`) por opcodes especializados monomórficos (`BINARY_OP_ADD_INT`), acelerando la ejecución de tipos homogéneos.
  - **El JIT de Python 3.13 (Copy-and-Patch Architecture)**:
    - En lugar de implementar un compilador JIT complejo y pesado como LLVM (que tarda segundos en compilar y consume gigabytes de RAM), Python 3.13 adopta una arquitectura de **Copy-and-Patch**:
      1. En tiempo de compilación de CPython, Clang compila fragmentos pequeños de código máquina de plantilla (*stencils*) para cada instrucción de bytecode especializada.
      2. En tiempo de ejecución, cuando una función se ejecuta miles de veces (código caliente), el motor JIT simplemente copia los fragmentos de código máquina precompilados en memoria ejecutable y "parchea" los valores inmediatos de punteros y constantes.
      3. El procesador pasa a ejecutar código máquina nativo x86_64 o ARM64 directamente sin pasar por el bucle central de interpretación de bytecode (`_PyEval_EvalFrameDefault`).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Creer que el nuevo JIT de Python 3.13 compilará código dinámico sucio con variables de tipo mutante a velocidad de C++ sin requerir estabilidad de tipos.
  - 🟢 **Green Flag**: Analizar el tradeoff del JIT Copy-and-Patch: tiempo de compilación casi nulo (< 100 microsegundos) frente a menor agresividad en optimizaciones globales que un JIT maduro como PyPy.

---

### 73. ¿Cómo estructurar un proyecto de Python empresarial con `pyproject.toml`, Hatchling/Poetry y aislamiento estricto (PEP 517/518/621)?
- **Nivel**: Senior Python / DevOps Engineer
- **Respuesta Técnica**:
  - **La obsolescencia de `setup.py` y `requirements.txt`**:
    - `setup.py` ejecuta código arbitrario de Python durante la instalación del paquete (vector de ataque de seguridad grave).
    - Múltiples archivos dispersos (`setup.cfg`, `Pipfile`, `requirements.txt`, `tox.ini`) creaban fragmentación y dependencias circulares.
  - **Estándar Unificado Moderno (`pyproject.toml`)**:
    - **PEP 518**: Especifica el sistema de construcción (*Build System*) de forma declarativa e inmutable:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "empresa-core"
version = "2.4.0"
description = "Servicio empresarial de pagos"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.7.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "mypy>=1.9.0",
    "ruff>=0.3.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"
```
    - Permite empaquetar binarios de forma reproducible mediante entornos efímeros de compilación aislados (`pip` o `uv` compilan sin acceso al entorno global).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Mantener nuevos proyectos creados con `setup.py` y fijar dependencias sin lockfile criptográfico en entornos productivos.
  - 🟢 **Green Flag**: Adoptar herramientas ultra-rápidas como **uv** (de Astral) para resolución e instalación de dependencias en fracciones de segundo con compatibilidad total con PEP 621.

---

### 74. ¿Cómo implementar un Cache LRU en memoria respetando el TTL (Time-to-Live) utilizando estructuras de datos nativas?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Limitación de `functools.lru_cache`**:
    - El decorador estándar de Python solo implementa desalojo por tamaño máximo (`maxsize`), pero **no soporta expiración temporal (TTL)**. Un dato obsoleto permanece en memoria indefinidamente si la capacidad no se desborda.
  - **Implementación con `collections.OrderedDict`**:
```python
import time
from collections import OrderedDict
from typing import Any

class TTLCache:
    def __init__(self, maxsize: int = 1000, ttl_seconds: float = 300):
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self.cache:
            return None
        value, expiry = self.cache[key]
        if time.monotonic() > expiry:
            del self.cache[key] # Expira de forma reactiva
            return None
        self.cache.move_to_end(key) # Marca como recientemente usado
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False) # Desaloja el elemento más antiguo (FIFO/LRU)
        self.cache[key] = (value, time.monotonic() + self.ttl)
```
  - **Uso de `time.monotonic()`**: Se debe usar siempre el reloj monotónico en lugar de `time.time()` para evitar anomalías provocadas por saltos de reloj del sistema operativo o ajustes NTP.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `time.time()` para calcular diferencias de tiempo en servidores con sincronización horaria dinámica.
  - 🟢 **Green Flag**: Utilizar una cola de prioridad (Heapq) para desalojo activo de llaves expiradas en segundo plano sin esperar al acceso reactivo.

---

### 75. ¿Cómo funciona la arquitectura de ContextVar para aislar estado en corutinas de Asyncio y tareas concurrentes?
- **Nivel**: Senior Backend / Core Engineer
- **Respuesta Técnica**:
  - **El fallo de `threading.local()` en Asyncio**:
    - `threading.local()` aísla datos a nivel de hilo del sistema operativo.
    - En Asyncio, miles de corutinas concurrentes se ejecutan en el **mismo hilo físico**. Si se guarda el ID de usuario autenticado en `threading.local()`, todas las corutinas que se ejecuten en ese hilo verán y sobreescribirán los datos de los demás clientes, produciendo fugas de seguridad catastróficas.
  - **`contextvars` (PEP 567)**:
    - Variable de contexto diseñada específicamente para el bucle de eventos y concurrencia cooperativa:
```python
from contextvars import ContextVar

# Declaración global de la variable de contexto
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="unknown")

async def middleware(request, call_next):
    # Asigna un valor exclusivo para el árbol de ejecución de esta corutina
    token = request_id_ctx.set(request.headers.get("X-Request-ID", "gen-123"))
    try:
        return await call_next(request)
    finally:
        request_id_ctx.reset(token) # Restaura el estado al salir

async def service_call():
    # Accede al ID de la petición sin pasarlo explícitamente en los argumentos de la función
    current_id = request_id_ctx.get()
    print(f"Log: petición actual {current_id}")
```
    - Cada corutina secundaria creada con `asyncio.create_task()` hereda una **copia superficial inmutable** del contexto de la corutina padre; las modificaciones dentro del hijo no mutan el contexto del padre.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar variables globales o `threading.local()` para gestionar el contexto de peticiones en FastAPI o Starlette.
  - 🟢 **Green Flag**: Demostrar el uso de `contextvars` para inyectar automáticamente IDs de correlación de trazas en todos los logs de la aplicación.

---

### 76. ¿Cómo optimizar el procesamiento de archivos masivos en paralelo con `multiprocessing` y memoria compartida (`SharedMemory`)?
- **Nivel**: Senior Data / Performance Engineer
- **Respuesta Técnica**:
  - **Sobrecarga del `multiprocessing` estándar**:
    - Cuando los procesos hijos se comunican mediante `Queue` o `Pipe`, Python debe serializar cada objeto con **Pickle**, enviarlo por un socket Unix local y deserializarlo en el hijo, saturando la CPU y duplicando el uso de RAM.
  - **Memoria Compartida sin Copias (`multiprocessing.shared_memory` en Python 3.8+)**:
    - Permite a múltiples procesos mapear el mismo bloque de memoria física compartida del sistema operativo (POSIX shared memory) directamente en sus espacios de direcciones virtuales:
```python
from multiprocessing import shared_memory, Process
import numpy as np

def worker(shm_name, shape, dtype):
    # Conecta al bloque existente sin copiar datos físicos
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    array = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
    # Modifica los datos directamente en el bloque compartido
    array += 10
    existing_shm.close()

if __name__ == '__main__':
    data = np.zeros((10000, 10000), dtype=np.float64) # ~800 MB
    shm = shared_memory.SharedMemory(create=True, size=data.nbytes)
    shared_array = np.ndarray(data.shape, dtype=data.dtype, buffer=shm.buf)
    shared_array[:] = data[:]

    p = Process(target=worker, args=(shm.name, data.shape, data.dtype))
    p.start()
    p.join()
    print(shared_array[0, 0]) # 10.0 (Modificado instantáneamente sin copias)
    shm.close()
    shm.unlink() # Destruye el segmento de memoria en el SO
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Pasar DataFrames de Pandas de varios gigabytes a través de una `multiprocessing.Queue` sufriendo congelaciones por serialización Pickle.
  - 🟢 **Green Flag**: Gestionar la sincronización con primitivas atómicas de bloqueo (`multiprocessing.Lock`) para prevenir condiciones de carrera de escritura en el bloque compartido.

---

### 77. ¿Cómo opera la función `__missing__` en subclases de `dict` y cómo se implementan estructuras como `defaultdict` a bajo nivel?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **El Hook de Clave No Encontrada**:
    - En el protocolo de mapeo de Python, cuando se accede a `d[key]` y la clave no existe en el diccionario, la clase interna invoca el método especial `__missing__(self, key)`.
    - Si la clase define `__missing__`, su valor de retorno se convierte en la respuesta de la expresión de indexación `d[key]`.
    - Si no está definido, arroja la excepción estándar `KeyError`.
  - **Implementación de un Árbol Autovivificante (Multi-Level Nested Dict)**:
```python
class AutoVivificationDict(dict):
    """Crea automáticamente niveles anidados infinitos al acceder a claves inexistentes."""
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

tree = AutoVivificationDict()
tree['users']['admins']['marcogil']['role'] = 'Staff'
print(tree) # {'users': {'admins': {'marcogil': {'role': 'Staff'}}}}
```
  - **Nota crítica**: `__missing__` **solo se invoca al usar la sintaxis de corchetes `d[key]`**; el método `d.get(key)` **no** invoca `__missing__` por diseño en CPython.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Llenar el código con comprobaciones defensivas repetitivas (`if k not in d: d[k] = {}`) en algoritmos de agrupación complejos.
  - 🟢 **Green Flag**: Distinguir entre `collections.defaultdict` (escrito en C) y la implementación personalizada mediante `__missing__` para comportamientos dinámicos basados en la propia clave solicitada.

---

### 78. ¿Cómo depurar cuellos de botella de CPU y memoria en aplicaciones de producción con `py-spy` sin detener el servicio?
- **Nivel**: Senior SRE / Performance Specialist
- **Respuesta Técnica**:
  - **Limitaciones de Profilers Tradicionales (`cProfile`, `profile`)**:
    - Profilers deterministas instrumentados: ralentizan la aplicación entre un 20% y un 300%, alterando el comportamiento de latencia en producción.
    - Requieren reiniciar el proceso con banderas especiales o modificar el código fuente.
  - **Sampling Profiler No Invasivo (`py-spy`)**:
    - Escrito en Rust. Lee el espacio de memoria virtual del proceso Python en ejecución desde el exterior mediante llamadas al sistema del kernel (`process_vm_readv` en Linux, `vm_read` en macOS).
    - **Cero impacto en producción**: No inyecta código en el proceso, no altera el GIL y consume menos del 1% de CPU.
    - **Capacidades Operativas**:
      1. **Top en vivo**: `py-spy top --pid 14205` (Muestra en tiempo real qué funciones de Python consumen más tiempo de CPU, similar al comando `top` del SO).
      2. **Flame Graphs**:
```bash
# Graba la pila de llamadas durante 60 segundos y genera un Flame Graph SVG interactivo
py-spy record -o profile.svg --pid 14205 --duration 60 --rate 100
```
      3. **Depuración de bloqueos (Deadlocks)**: `py-spy dump --pid 14205` imprime el stack trace de cada hilo activo del proceso, revelando al instante en qué lock o socket de red está congelado el servicio.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Afirmar que es imposible depurar una aplicación Python en producción sin añadir prints o reiniciar el proceso.
  - 🟢 **Green Flag**: Utilizar Flame Graphs de `py-spy` para detectar funciones síncronas bloqueando el event loop de procesos ASGI.

---

### 79. ¿Cómo funciona la arquitectura de Testing con `pytest` Fixtures (`scope`, `autouse` y `yield`) y parametrización avanzada?
- **Nivel**: Mid-Level / Senior QA Automation
- **Respuesta Técnica**:
  - **Inyección de Dependencias en Pytest**:
    - A diferencia de `unittest` (heredado de JUnit con clases rígidas), `pytest` utiliza funciones como fixtures inyectadas automáticamente por nombre en los argumentos de las funciones de prueba.
  - **Dimensiones de un Fixture**:
    1. **Alcance (`scope`)**:
       - `function` (por defecto): Se ejecuta una vez por cada función de test individual.
       - `class`: Se ejecuta una vez por cada clase de pruebas.
       - `module`: Se ejecuta una vez por cada archivo de pruebas.
       - `package` / `session`: Se inicializa una única vez para toda la suite de pruebas completa (ej. levantar un contenedor Docker de Postgres con Testcontainers).
    2. **Teardown Elegante con `yield`**:
```python
import pytest

@pytest.fixture(scope="session")
def database_connection():
    db = create_test_database()
    yield db # Pasa la conexión a los tests
    db.drop_tables()
    db.close() # Se ejecuta garantizadamente al terminar la sesión de pruebas
```
    3. **Parametrización Declarativa**: Permite correr la misma prueba con docenas de combinaciones de entradas y salidas esperadas:
```python
@pytest.mark.parametrize("entrada,esperado", [
    ("user@corp.com", True),
    ("invalid-email", False),
    ("", False),
])
def test_email_validator(entrada, esperado):
    assert validate_email(entrada) is esperado
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar `setUp` y `tearDown` de `unittest` con variables globales o fixtures con scope incorrecto que recrean bases de datos pesadas en cada test individual.
  - 🟢 **Green Flag**: Combinar fixtures de scope `session` con Savepoints o transacciones con rollback automático por cada test para máxima velocidad y total aislamiento.

---

### 80. ¿Cómo operar el protocolo ASGI (Asynchronous Server Gateway Interface) frente a WSGI y cómo se modelan los mensajes HTTP y WebSockets?
- **Nivel**: Senior Backend / Core Engineer
- **Respuesta Técnica**:
  - **WSGI (PEP 3333 - Síncrono y Limitado a HTTP)**:
    - Firma: `application(environ, start_response)`.
    - Procesa una única petición y respuesta de forma estrictamente síncrona. Incapaz de manejar conexiones abiertas persistentes como WebSockets, Server-Sent Events (SSE) o streaming bidireccional HTTP/2 sin bloquear el hilo completo del servidor.
  - **ASGI (Estándar Asíncrono Moderno)**:
    - Firma de la aplicación: `async def application(scope, receive, send)`.
    - **Tres Parámetros**:
      1. **`scope` (Diccionario de Conexión)**: Metadatos inmutables de la conexión (tipo: `'http'` o `'websocket'`, versión HTTP, headers, path, query string, client IP).
      2. **`receive` (Callable asíncrono)**: Canal para recibir eventos entrantes del cliente (`await receive()`). En HTTP devuelve fragmentos del cuerpo (`http.request`); en WebSockets devuelve mensajes de texto o binarios (`websocket.receive`).
      3. **`send` (Callable asíncrono)**: Canal para enviar eventos hacia el cliente (`await send({'type': 'http.response.start', 'status': 200, ...})`).
    - **Soporte Nativo de Protocolos**: Un único servidor ASGI (Uvicorn / Hypercorn / Granian) puede balancear y multiplexar tráfico HTTP/1.1, HTTP/2, gRPC y WebSockets bidireccionales en el mismo proceso.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar implementar WebSockets en producción sobre servidores WSGI puros como Gunicorn con workers síncronos estándar.
  - 🟢 **Green Flag**: Diseñar un middleware ASGI puro interceptando los canales `receive` y `send` para streaming y métricas de latencia de red en tiempo real.

---

### 81. ¿Cómo mitigar problemas de recursión infinita y optimizar llamadas profundas sin soporte de Tail Call Optimization (TCO)?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Python NO tiene Tail Call Optimization (TCO)**:
    - Por decisión deliberada de diseño de Guido van Rossum, CPython nunca optimiza llamadas a la cola (Tail Calls) para preservar la fidelidad absoluta de los stack traces y la depuración con tracebacks.
    - CPython impone un límite estricto de profundidad de recursión (por defecto 1,000 llamadas, consultable con `sys.getrecursionlimit()`). Si se supera, arroja `RecursionError: maximum recursion depth exceeded`.
  - **Estrategias de Resolución**:
    1. **Transformación a Bucle Iterativo con Pila Explícita en el Heap**:
       - Mover el estado de la recursión desde el stack de CPython a una estructura `list` o `deque` en la memoria RAM normal, esquivando el límite de 1,000 llamadas y evitando sobrecargar el stack de llamadas del sistema operativo.
    2. **Técnica de Trampolín (Trampoline Pattern con Generadores)**:
```python
def factorial_trampoline(n, acc=1):
    while n > 1:
        acc *= n
        n -= 1
    return acc
```
    3. **Aumentar el límite de recursión con moderación**: `sys.setrecursionlimit(5000)` (riesgoso: si se excede el tamaño físico del stack de C del sistema operativo, el proceso sufrirá un `Segmentation Fault` irreversible).
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Solucionar errores de recursión simplemente incrementando `sys.setrecursionlimit(100000)` hasta que el proceso muera por desbordamiento de pila del kernel.
  - 🟢 **Green Flag**: Reescribir algoritmos recursivos complejos utilizando pilas de estado explícitas o programación dinámica con memorización.

---

### 82. ¿Cómo funciona la arquitectura de compilación y ejecución de Regex en CPython (Motor SRE) y cómo evitar el ReDoS?
- **Nivel**: Senior Security / Python Engineer
- **Respuesta Técnica**:
  - **El motor interno de Regex de Python (SRE - Secret Labs Regular Expression)**:
    - Es un motor basado en **NFA (Nondeterministic Finite Automaton)** con retroceso (*Backtracking*).
    - Al compilar un patrón (`re.compile()`), SRE genera un bytecode interno que se ejecuta en un intérprete de máquina virtual especializado en C.
  - **El Peligro de ReDoS (Regular Expression Denial of Service)**:
    - Ocurre cuando un patrón contiene cuantificadores anidados o solapados (ej. `^(a+)+$` o `(a|a)+`).
    - Ante una entrada no coincidente como `"aaaaaaaaaaaaaaaaaaaaax"`:
      - El motor intenta todas las combinaciones combinatorias posibles antes de declarar el fallo.
      - La complejidad temporal pasa de lineal a **exponencial $\mathcal{O}(2^N)$**: una cadena de apenas 30 caracteres puede congelar el 100% de la CPU durante horas, bloqueando el proceso de Python por completo.
  - **Mitigación y Prevención**:
    1. **Evitar cuantificadores anidados**: Utilizar expresiones regulares lineales y deterministas.
    2. **Uso de la librería `google-re2`**:
       - CPython permite sustituir o complementar `re` con **re2**, un motor de expresiones regulares basado en DFA (Deterministic Finite Automaton) que garantiza un tiempo de ejecución estrictamente lineal $\mathcal{O}(N)$ respecto al tamaño de la entrada, siendo matemáticamente inmune a ataques ReDoS.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Evaluar expresiones regulares no auditadas suministradas por usuarios sobre el hilo principal de una API web.
  - 🟢 **Green Flag**: Identificar patrones con Catastrophic Backtracking en revisiones de código y aplicar motores DFA o timeouts estrictos de validación.

---

### 83. ¿Cómo opera la serialización segura de datos con `msgpack` o `protobuf` frente a la vulnerabilidad de ejecución remota de código en `pickle`?
- **Nivel**: Senior Security / Backend Engineer
- **Respuesta Técnica**:
  - **La Vulnerabilidad Crítica de `pickle`**:
    - `pickle` no es un formato de datos puro; es un **lenguaje de máquina virtual completo**.
    - Al deserializar un payload con `pickle.loads(untrusted_data)`, la máquina virtual de Pickle ejecuta instrucciones que pueden invocar cualquier función de Python del sistema mediante el método especial `__reduce__`:
```python
import pickle, os

class MaliciousPayload:
    def __reduce__(self):
        # Provoca Ejecución Remota de Código (RCE) inmediata al deserializar
        return (os.system, ('rm -rf /tmp/*',))

payload = pickle.dumps(MaliciousPayload())
# pickle.loads(payload) -> Ejecuta el comando en el servidor
```
    - **Regla de oro**: NUNCA deserializar datos de fuentes no confiables (cookies, peticiones HTTP, Redis público) con `pickle`.
  - **Alternativas Seguras y de Alto Rendimiento**:
    1. **MessagePack (`msgpack`)**: Formato binario eficiente (más compacto y rápido que JSON) que solo transporta tipos de datos primitivos (números, strings, listas, mapas). Cero riesgo de ejecución de código.
    2. **Protocol Buffers (`protobuf`)**: Esquema estrictamente tipado y versionado hacia adelante/atrás. Serialización ultrarrápida compilada en C/Rust, ideal para comunicación inter-microservicios gRPC.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Almacenar sesiones de usuario serializadas con `pickle` en cookies de navegador o en instancias de Redis compartidas.
  - 🟢 **Green Flag**: Sustituir serializadores inseguros por MessagePack o Protobuf midiendo la reducción de ancho de banda y latencia de CPU.

---

### 84. ¿Cómo implementar un Rate Limiter distribuido en Python utilizando el algoritmo Token Bucket y scripts Lua atómicos en Redis?
- **Nivel**: Senior Backend / Distributed Systems
- **Respuesta Técnica**:
  - **El problema de la race condition en Redis**:
    - Si se implementa un Rate Limiter ejecutando comandos de Redis individuales desde Python (`GET tokens`, `IF tokens > 0`, `DECRBY tokens 1`), dos peticiones concurrentes en milisegundos idénticos leerán el mismo valor, permitiendo un exceso de tráfico (*Race Condition*).
  - **Ejecución Atómica con Script Lua**:
    - Los scripts Lua en Redis se ejecutan de forma atómica en el hilo principal del motor de Redis: ninguna otra operación puede intercalarse entre sus instrucciones.
```python
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local fill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(data[1]) or capacity
local last_updated = tonumber(data[2]) or now

-- Calcula tokens regenerados según el tiempo transcurrido
local delta = math.max(0, now - last_updated)
tokens = math.min(capacity, tokens + delta * fill_rate)

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', now)
    redis.call('EXPIRE', key, math.ceil(capacity / fill_rate))
    return 1 -- Permitido
else
    return 0 -- Denegado (429 Too Many Requests)
end
"""

rate_limit_script = r.register_script(TOKEN_BUCKET_LUA)

def is_allowed(user_id: str, capacity: int = 10, fill_rate: float = 2.0) -> bool:
    import time
    now = time.time()
    return bool(rate_limit_script(keys=[f"rate:{user_id}"], args=[capacity, fill_rate, now, 1]))
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Proponer bloqueos distribuidos pesados (`Redlock`) para un simple control de tasa cuando un script Lua atómico lo resuelve en microsegundos.
  - 🟢 **Green Flag**: Dominar la ventaja de registrar el script con `SCRIPT LOAD` y ejecutarlo mediante su hash SHA-1 para optimizar el ancho de banda de red.

---

### 85. ¿Cómo opera el Garbage Collector en entornos multi-proceso con `fork()` y cómo resuelve `gc.freeze()` la degradación de Copy-on-Write (CoW)?
- **Nivel**: Staff Python / Systems Infrastructure
- **Respuesta Técnica**:
  - **Arquitectura Fork y Copy-on-Write (CoW)**:
    - Servidores web como Gunicorn arrancan un proceso maestro que carga la aplicación en memoria y luego invoca `os.fork()` para crear múltiples workers.
    - Gracias a la memoria virtual del kernel de Linux, los procesos hijos comparten las mismas páginas de memoria física del padre sin duplicarlas (*Copy-on-Write*), ahorrando gigabytes de RAM.
  - **La Destrucción de CoW por culpa del Reference Counting y el GC**:
    - Cada vez que un worker procesa una petición y lee un objeto cargado por el padre, CPython incrementa su contador de referencias (`ob_refcnt`).
    - Al mutar el contador de referencias de 4 bytes, el kernel detecta una escritura y se ve forzado a **copiar la página física de memoria completa (4 KB)** hacia el espacio del worker hijo.
    - Además, cuando el recolector de basura (`gc`) recorre las listas enlazadas de objetos (`gc_refs`), muta los metadatos de las cabeceras de los objetos. En pocos minutos, **el 100% de la memoria compartida se duplica**, disparando el consumo de RAM del servidor.
  - **La Solución con `gc.freeze()` (Python 3.7+ / Instagram Engineering)**:
    - En el proceso maestro, justo antes de ejecutar `fork()`:
```python
import gc

# Congela todos los objetos cargados hasta el momento moviéndolos a una lista inmutable
# que el recolector de basura de los workers nunca intentará escanear ni mutar
gc.freeze()
```
    - **Resultado**: Los objetos pre-cargados permanecen 100% compartidos en modo de solo lectura, reduciendo el consumo total de memoria RAM del clúster de servidores web hasta en un **40%**.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Desconocer que las lecturas en Python provocan escrituras a nivel de memoria por el conteo de referencias rompiendo Copy-on-Write.
  - 🟢 **Green Flag**: Citar la investigación seminal de Instagram Engineering sobre `gc.freeze()` y deshabilitación del GC en arquitecturas prefork.

---

### 86. ¿Cómo funciona la resolución de nombres en tiempo de importación (`sys.modules`, `importlib` y módulos circulares)?
- **Nivel**: Senior Python Engineer
- **Respuesta Técnica**:
  - **El algoritmo del import en CPython**:
    1. Consulta el diccionario global `sys.modules` para verificar si el módulo ya fue cargado previamente. Si existe, devuelve la referencia en caché de inmediato.
    2. Si no existe, los **Finder Hooks** (`sys.meta_path`) localizan el código fuente en el sistema de archivos siguiendo las rutas de `sys.path`.
    3. Un **Loader** crea un objeto módulo vacío, lo registra en `sys.modules` y compila el código fuente a bytecode (`.pyc`).
    4. El intérprete ejecuta el cuerpo del archivo secuencialmente de arriba hacia abajo para poblar el diccionario `__dict__` del módulo.
  - **Causa Raíz de los Errores de Importación Circular (`ImportError: cannot import name ...`):**:
    - Ocurre cuando el Módulo A importa al Módulo B mientras A todavía está en proceso de ejecución.
    - El Módulo B intenta importar un atributo de A que **aún no ha sido definido** porque el archivo A no ha terminado de ejecutarse.
  - **Estrategias de Remediación Limpia**:
    1. **Refactorización de Dependencias**: Extraer los tipos o funciones compartidas a un tercer módulo común (`types.py` o `models_core.py`).
    2. **Imports Condicionales para Verificación de Tipos (PEP 484)**:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.payment import PaymentService # Solo se evalúa en Mypy, nunca en runtime
```
    3. **Imports diferidos (Lazy Imports)** dentro del cuerpo de funciones específicas que los necesitan.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Proponer imports circulares sucios al final de los archivos como "patrón normal de diseño".
  - 🟢 **Green Flag**: Explicar cómo `importlib` permite carga dinámica de plugins en caliente y cómo `TYPE_CHECKING` previene ciclos en herramientas de tipado estático.

---

### 87. ¿Cómo opera la introspección profunda del AST (Abstract Syntax Tree) en Python con el módulo `ast` para análisis estático de código?
- **Nivel**: Staff Python / Compiler Tools Engineer
- **Respuesta Técnica**:
  - **Fases del pipeline del compilador de CPython**:
    $$\text{Código Fuente} \xrightarrow{\text{Tokenize}} \text{CST} \xrightarrow{\text{Parse}} \text{AST} \xrightarrow{\text{Control Flow}} \text{Bytecode}$$
  - **Manipulación del AST con el módulo estándar `ast`**:
    - El módulo `ast` permite parsear una cadena de código en una estructura de árbol de objetos Python (`ast.Module`, `ast.FunctionDef`, `ast.Call`).
  - **Implementación de un Linter de Seguridad que detecta llamadas prohibidas (`eval` / `exec`)**:
```python
import ast

class SecurityLinter(ast.NodeVisitor):
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in {'eval', 'exec'}:
            print(f"ALERTA DE SEGURIDAD: Uso prohibido de '{node.func.id}' en línea {node.lineno}")
        self.generic_visit(node) # Continúa recorriendo los nodos hijos

codigo_fuente = """
def procesar(datos):
    eval(datos)
"""

arbol = ast.parse(codigo_fuente)
SecurityLinter().visit(arbol)
```
  - Herramientas modernas de vanguardia como **Ruff** replican este análisis estático utilizando parsers de AST implementados en Rust para auditar millones de líneas de código en milisegundos.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar analizar código fuente buscando patrones inseguros mediante expresiones regulares basadas en texto plano (frágiles ante saltos de línea y comentarios).
  - 🟢 **Green Flag**: Utilizar `ast.NodeTransformer` para reescribir o instrumentar dinámicamente árboles de código antes de su compilación con `compile()`.

---

### 88. ¿Cómo estructurar pruebas de integración asíncronas con bases de datos reales utilizando Testcontainers-Python?
- **Nivel**: Senior Backend / QA Architect
- **Respuesta Técnica**:
  - **La debilidad de los Mocks**:
    - Mockear la base de datos (`unittest.mock`) no prueba la validez de los queries SQL reales, dialectos específicos de Postgres (JSONB, Trigrams), transacciones ni restricciones de integridad foránea.
  - **Arquitectura de Testcontainers**:
    - Levanta contenedores Docker reales y efímeros directamente desde el código de las pruebas de Python mediante la API de Docker del sistema.
  - **Integración con Pytest Fixtures**:
```python
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
def postgres_container():
    # Descarga y arranca una imagen real de PostgreSQL en un puerto efímero aleatorio
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture
async def db_session(postgres_container):
    # Obtiene la cadena de conexión generada dinámicamente
    url = postgres_container.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(url)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback() # Limpieza automática por cada test
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Ejecutar pruebas de integración contra bases de datos SQLite en memoria cuando la aplicación de producción utiliza Postgres con funciones avanzadas no soportadas por SQLite.
  - 🟢 **Green Flag**: Configurar puertos efímeros dinámicos en Testcontainers para permitir la ejecución concurrente de múltiples suites de CI en paralelo sin conflictos de puertos.

---

### 89. ¿Cómo funciona la concurrencia con `concurrent.futures.ProcessPoolExecutor` y cómo evitar bloqueos por Deadlock en procesos hijos?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Arquitectura de `ProcessPoolExecutor`**:
    - Proporciona una interfaz de alto nivel basada en futuros (`Future`) sobre `multiprocessing`.
    - Mantiene un pool de $N$ procesos de trabajo y gestiona colas internas de IPC para despachar llamadas y recolectar resultados de forma transparente:
```python
from concurrent.futures import ProcessPoolExecutor

def computo_intensivo(x: int) -> int:
    return sum(i * i for i in range(x))

with ProcessPoolExecutor(max_workers=4) as executor:
    resultados = list(executor.map(computo_intensivo, [1000000, 2000000, 3000000]))
```
  - **Peligro Crítico: Deadlocks en funciones no serializables o excepciones silenciadas**:
    1. Si una función o uno de sus argumentos no es serializable con **Pickle** (ej. una conexión abierta a un socket o una función lambda), el worker hijo fallará abruptamente.
    2. Si se invoca un `ProcessPoolExecutor` dentro de un proceso que ya tiene hilos corriendo y se usa el método de arranque `fork` por defecto en Linux, los hilos no se heredan pero los bloqueos (`Locks`) en memoria sí se copian en estado bloqueado, produciendo **Deadlocks permanentes e irrecuperables**.
    3. **Mitigación obligatoria**: Configurar siempre el método de arranque en **`spawn`** (`multiprocessing.set_start_method("spawn")`) para inicializar intérpretes limpios e independientes.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Usar el método `fork` en Linux cuando la aplicación ya ha inicializado hilos secundarios o pools de clientes de red.
  - 🟢 **Green Flag**: Controlar el ciclo de vida de los futuros con timeouts explícitos (`future.result(timeout=10)`) para evitar cuelgues indefinidos.

---

### 90. ¿Cómo opera la optimización de código numérico y vectorial con NumPy y vectorización SIMD frente a bucles puros de Python?
- **Nivel**: Senior Data / Machine Learning Engineer
- **Respuesta Técnica**:
  - **La lentitud del bucle `for` de Python**:
    - En Python, los números son objetos (`PyObject`) que contienen metadatos (tamaño, tipo, punteros, contador de referencias).
    - Un bucle `for` que itera 10 millones de enteros ejecuta en cada paso: verificación de límites de la lista, desempaquetado del puntero de memoria, comprobación dinámica del tipo de datos e invocación del método de suma.
  - **La Magia de la Vectorización en NumPy**:
    1. **Bloques Contiguos en C**: Un `ndarray` de NumPy es un puntero directo a un array contiguo de memoria física en C sin envolturas de objetos de Python.
    2. **Instrucciones SIMD (Single Instruction, Multiple Data)**:
       - El código compilado en C y ensamblador de NumPy aprovecha las extensiones del procesador (AVX-512, AVX2, ARM NEON).
       - En lugar de sumar número a número, una única instrucción de CPU suma **8 números de coma flotante de 64 bits de forma simultánea en un solo ciclo de reloj**.
    3. **Eliminación del Overhead del Intérprete**: Toda la iteración se ejecuta íntegramente dentro del hardware del procesador en microsegundos, siendo de **$50\times$ a $200\times$ más rápido** que el código equivalente en Python puro.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Escribir bucles `for` manuales para recorrer arrays de NumPy perdiendo toda la aceleración vectorial.
  - 🟢 **Green Flag**: Utilizar broadcasting y operaciones `ufunc` (universal functions) nativas para operar tensores multidimensionales sin duplicar memoria.

---

### 91. ¿Cómo mitigar el problema de "GIL thrashing" en aplicaciones que mezclan hilos de I/O e hilos de CPU intensivo?
- **Nivel**: Senior Systems / Core Python Developer
- **Respuesta Técnica**:
  - **El fenómeno del GIL Thrashing (Convicción del GIL)**:
    - En CPython tradicional, cuando un hilo ejecuta CPU pesada y otro hilo ejecuta tareas ligeras de I/O (ej. atender un socket de red), el sistema de conmutación de hilos del sistema operativo entra en conflicto con el mecanismo de liberación forzada del GIL (`sys.setswitchinterval(0.005)` - cada 5 milisegundos).
    - El hilo de I/O se despierta al recibir datos, intenta adquirir el GIL, falla porque el hilo de CPU lo tiene bloqueado, y es puesto a dormir por el kernel. Esto genera miles de cambios de contexto inútiles por segundo (*Context Switching Overhead*), disparando el uso de CPU al 100% y degradando la latencia de red del hilo de I/O de forma dramática.
  - **Soluciones de Arquitectura**:
    1. **Aislamiento Estricto de Responsabilidades**:
       - Nunca mezclar tareas de cálculo intensivo con tareas de atención de red en los mismos hilos del proceso de Python.
    2. **Externalización del Cómputo**:
       - Enviar el trabajo pesado de CPU a un proceso secundario independiente (`ProcessPoolExecutor`) o a una cola asíncrona distribuida (Celery / Redis Queue).
    3. **Liberación Manual del GIL en Código C/Rust**:
       - Si el cómputo se realiza en extensiones nativas (NumPy, Cython, PyO3), envolver el cálculo en un bloque `Py_BEGIN_ALLOW_THREADS` / `py.allow_threads()`, permitiendo que el hilo de I/O de Python continúe procesando peticiones sin interrupción.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar resolver cuellos de botella de CPU añadiendo más hilos con el módulo `threading` en un único proceso con GIL activo.
  - 🟢 **Green Flag**: Explicar la mecánica del `sys.getswitchinterval()` y cómo las extensiones en C/Rust liberan el GIL durante cálculos numéricos.

---

### 92. ¿Cómo funciona la arquitectura de Logging de Python y cómo evitar el bloqueo de peticiones web por escritura en disco síncrona?
- **Nivel**: Senior SRE / DevOps
- **Respuesta Técnica**:
  - **El problema del Logging síncrono estándar**:
    - Por defecto, los handlers del módulo estándar `logging` (`FileHandler`, `StreamHandler`) ejecutan llamadas de I/O al sistema de archivos de forma síncrona (`write()` / `flush()`) sobre el hilo que genera el log.
    - Si el disco del servidor sufre latencia o el log es capturado por un pipe bloqueante de Docker/Kubernetes, **cada petición web se congela esperando a que el log se escriba en el disco físico**.
  - **Solución No Bloqueante con `QueueHandler` y `QueueListener`**:
```python
import logging
import queue
from logging.handlers import QueueHandler, QueueListener

log_queue = queue.Queue(-1) # Cola en memoria sin límite de tamaño

# Handler rápido no bloqueante para los hilos de la aplicación
queue_handler = QueueHandler(log_queue)
logger = logging.getLogger()
logger.addHandler(queue_handler)

# Listener que corre en un hilo secundario independiente consumiendo la cola
file_handler = logging.FileHandler("/var/log/app.log")
listener = QueueListener(log_queue, file_handler)
listener.start() # Escribe al disco en segundo plano sin ralentizar las APIs
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Realizar llamadas de red o escrituras a disco síncronas pesadas dentro de formateadores de logging en rutas críticas de alto tráfico.
  - 🟢 **Green Flag**: Utilizar logging estructurado en formato JSON (`structlog` o `python-json-logger`) canalizado a través de un `QueueHandler` asíncrono.

---

### 93. ¿Cómo opera la técnica de Monkey Patching de forma controlada y cuáles son sus peligros catastróficos en producción?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Definición**: Modificación dinámica de clases, módulos o funciones en tiempo de ejecución sin alterar el código fuente original en disco.
  - **Caso de uso legítimo (Librerías de pruebas y corutinas)**:
    - Bibliotecas como `gevent` ejecutan `monkey.patch_all()` para sustituir sockets estándar y librerías de red del sistema por versiones cooperativas no bloqueantes.
    - En pruebas unitarias, bibliotecas de mocking (`unittest.mock.patch`) sobreescriben temporalmente métodos durante el contexto de la prueba y restauran el original al salir.
  - **Peligros Catastróficos en Producción**:
    1. **Efectos Secundarios Ocultos Globales**: Si el Módulo A sobreescribe un método de una clase compartida, todos los demás módulos de la aplicación que interactúan con esa clase sufren el cambio sin saberlo.
    2. **Imposibilidad de Depuración**: Las excepciones arrojadas muestran stack traces donde el código ejecutado no coincide con el código visible en los archivos del repositorio de Git.
    3. **Conflictos en Orden de Carga**: Si el archivo que aplica el monkey patch se importa después de que otros módulos ya hayan almacenado una referencia al método original, la aplicación se vuelve inconsistente.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Utilizar monkey patching en código de producción de aplicaciones de negocio para "arreglar un bug temporalmente" en lugar de utilizar herencia, composición o enviar una Pull Request a la librería upstream.
  - 🟢 **Green Flag**: Limitar el uso de monkey patching estrictamente al ámbito de pruebas unitarias utilizando siempre gestores de contexto (`with patch(...):`).

---

### 94. ¿Cómo estructurar un sistema de Plugins desacoplado utilizando Entry Points de Python (PEP 621 / `importlib.metadata`)?
- **Nivel**: Senior Architecture / Open Source Developer
- **Respuesta Técnica**:
  - **Entry Points como Mecanismo de Descubrimiento Dinámico**:
    - Permiten a paquetes externos de terceros registrarse como extensiones o plugins de una aplicación principal simplemente al instalarse con `pip`, sin necesidad de modificar el código de la aplicación anfitriona.
  - **Declaración en el paquete del Plugin (`pyproject.toml`)**:
```toml
[project.entry-points."mi_app.procesadores"]
pdf_plugin = "mi_plugin_pdf:ProcesadorPDF"
excel_plugin = "mi_plugin_excel:ProcesadorExcel"
```
  - **Descubrimiento y Carga Dinámica en la Aplicación Principal**:
```python
from importlib.metadata import entry_points

def cargar_plugins_disponibles():
    # Descubre automáticamente todos los paquetes instalados en el entorno activo
    # que se hayan registrado bajo el grupo 'mi_app.procesadores'
    plugins = entry_points(group="mi_app.procesadores")
    procesadores = {}
    for ep in plugins:
        # Carga la clase o función en memoria dinámicamente
        plugin_class = ep.load()
        procesadores[ep.name] = plugin_class()
        print(f"Plugin registrado con éxito: {ep.name}")
    return procesadores
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Diseñar sistemas de plugins que obligan a hardcodear listas de nombres de clases en un archivo de configuración centralizado.
  - 🟢 **Green Flag**: Utilizar el estándar formal de Entry Points de `importlib.metadata` para ecosistemas extensibles (como hacen Pytest, Sphinx y Flake8).

---

### 95. ¿Cómo opera la función `__init_subclass__` frente al decorador de clases para metaprogramación declarativa?
- **Nivel**: Mid-Level / Senior
- **Respuesta Técnica**:
  - **Decorador de Clase (`@decorador`)**:
    - Se aplica explícitamente sobre una clase individual (`@mi_decorador class Foo: ...`).
    - *Limitación*: No se hereda automáticamente. Si la clase `Bar` hereda de `Foo`, el decorador no se ejecuta para `Bar` a menos que el desarrollador recuerde escribir manualmente `@mi_decorador` sobre `Bar`.
  - **`__init_subclass__` (Herencia Automática Garantizada)**:
    - Se define en la clase base una sola vez.
    - Se ejecuta automáticamente **para cada subclase presente o futura que herede de la clase base**, sin que el desarrollador de la subclase tenga que añadir ningún decorador:
```python
class EntidadValidada:
    def __init_subclass__(cls, es_abstracta: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        if es_abstracta:
            return
        if not hasattr(cls, 'tabla_bd'):
            raise TypeError(f"La subclase {cls.__name__} debe declarar el atributo 'tabla_bd'")

class Usuario(EntidadValidada):
    tabla_bd = "usuarios" # Pasa la validación

# class Invalido(EntidadValidada): pass -> Arroja TypeError inmediato en tiempo de carga
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Escribir metaclases complejas de 50 líneas cuando `__init_subclass__` resuelve la validación en 5 líneas limpias.
  - 🟢 **Green Flag**: Argumentar cuándo conviene el decorador de clases (modificación de una clase sin relación jerárquica) vs `__init_subclass__` (reglas de dominio para toda una familia de clases).

---

### 96. ¿Cómo implementar validación estricta en tiempo de compilación/CI con Mypy en modo `strict` sin falsos positivos inmanejables?
- **Nivel**: Senior Python Engineer
- **Respuesta Técnica**:
  - **El Modo Strict de Mypy (`--strict`)**:
    - Activa todas las comprobaciones de tipado más rigurosas: prohíbe funciones sin anotaciones explícitas, prohíbe tipos `Any` dinámicos, exige verificación de valores opcionales (`None`) y valida variables genéricas.
  - **Configuración Estratégica en `pyproject.toml`**:
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
check_untyped_defs = true

# Silenciar selectivamente dependencias externas de terceros sin tipado
[[tool.mypy.overrides]]
module = ["legacy_library.*", "third_party_tool.*"]
ignore_missing_imports = true
```
  - **Técnicas para Evitar Falsos Positivos**:
    - **Uso de `TypeGuard` o `TypeIs` (PEP 742 en Python 3.13)**: Para funciones de validación que estrechan tipos (*Type Narrowing*).
    - **`cast(Tipo, valor)`**: Usar `typing.cast` únicamente en fronteras con librerías dinámicas como última opción en lugar de llenar el código de comentarios `# type: ignore`.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Llenar la base de código con directivas indiscriminadas `# type: ignore` para acallar al analizador estático en lugar de tipar correctamente.
  - 🟢 **Green Flag**: Adoptar Type Narrowing mediante comprobaciones de `isinstance()` y `assert` para ayudar al analizador estático a inferir tipos sin casts forzados.

---

### 97. ¿Cómo funciona la arquitectura de compilación de código fuente con `Cython` utilizando directivas de optimización de C?
- **Nivel**: Senior Systems / Python Performance
- **Respuesta Técnica**:
  - **De Python a Código C Nativo**:
    - Cython toma un archivo `.pyx`, analiza la sintaxis y genera un archivo de código fuente en C (`.c`) que interactúa directamente con la C-API de CPython, compiliéndose después en un módulo binario (`.so` / `.pyd`).
  - **Directivas Clave de Optimización**:
```cython
# cython: boundscheck=False, wraparound=False, nonecheck=False, cdivision=True
cimport cython

cpdef double compute_mandelbrot(int max_iter, double c_re, double c_im) nogil:
    # Tipado estricto en variables de C nativas (sin objetos de Python)
    cdef double z_re = 0.0
    cdef double z_im = 0.0
    cdef int n = 0
    cdef double z_re2 = 0.0
    cdef double z_im2 = 0.0

    while n < max_iter and (z_re2 + z_im2) < 4.0:
        z_im = 2.0 * z_re * z_im + c_im
        z_re = z_re2 - z_im2 + c_re
        z_re2 = z_re * z_re
        z_im2 = z_im * z_im
        n += 1

    return float(n)
```
  - **Explicación de las directivas**:
    - `boundscheck=False`: Elimina la comprobación de desbordamiento de índices en arrays, permitiendo lecturas a velocidad pura de puntero de C.
    - `nogil`: Libera el GIL por completo durante el cálculo, permitiendo que múltiples hilos de CPU aceleren la función en paralelo.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Compilar código en Cython sin declarar tipos de variables (`cdef int`), lo que solo produce una traducción 1 a 1 de llamadas lentas de la C-API sin ganancia real de velocidad.
  - 🟢 **Green Flag**: Utilizar el reporte HTML de anotaciones (`cython -a archivo.pyx`) para identificar qué líneas permanecen amarillas (interacción con el intérprete de Python) y optimizarlas a blanco puro (código C directo).

---

### 98. ¿Cómo opera la técnica de Zero-Copy Data Sharing en Python mediante el protocolo `memoryview` y `buffer protocol`?
- **Nivel**: Staff Python / Systems Infrastructure
- **Respuesta Técnica**:
  - **El coste de rebanar datos (`slice`) en Python estándar**:
    - Cuando se tiene un objeto `bytes` de 500 MB (un archivo o stream de vídeo) y se ejecuta `trozo = buffer[100:200]`, Python asigna un **nuevo bloque de memoria física** en el Heap y copia físicamente los 100 bytes. En streams masivos de red, esto genera gigabytes de copias redundantes y presión sobre el GC.
  - **El Protocolo de Buffer y `memoryview` (Cero Copias)**:
    - `memoryview` expone la memoria física subyacente de un objeto que implemente el C-Buffer Protocol (`bytearray`, `array.array`, estructuras de NumPy) **sin copiar memoria**:
```python
datos_pesados = bytearray(b"X" * 100_000_000) # 100 MB de memoria

# Crea una vista de memoria virtual sin duplicar un solo byte físico
vista = memoryview(datos_pesados)

# Rebanar la vista crea otra vista sobre la misma memoria física original
sub_vista = vista[1000:2000]

# Mutar la sub-vista altera directamente el buffer original en el Heap
sub_vista[0] = ord('A')
print(chr(datos_pesados[1000])) # Imprime 'A' (Zero-Copy)
```
  - **Uso en Sockets de Red**: La llamada `socket.send_into(vista)` permite escribir datos recibidos de la red directamente en el buffer de la aplicación sin copias intermedias en memoria de usuario.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Concatenar objetos inmutables de tipo `bytes` en bucles (`buffer += nuevo_trozo`), provocando complejidad cuadrática $\mathcal{O}(N^2)$ por reasignaciones continuas de memoria.
  - 🟢 **Green Flag**: Dominar el uso de `memoryview` para streaming masivo de archivos y sockets de alta velocidad.

---

### 99. ¿Cómo implementar un mecanismo de Graceful Shutdown en servicios asíncronos de Python ante señales de terminación del sistema (`SIGTERM` / `SIGINT`)?
- **Nivel**: Senior SRE / Backend Engineer
- **Respuesta Técnica**:
  - **El problema de la terminación abrupta**:
    - Cuando Kubernetes o Docker envían un `SIGTERM` para detener un contenedor, si la aplicación no intercepta la señal, el proceso es abortado de inmediato, dejando transacciones a medias en la base de datos, mensajes sin confirmar en RabbitMQ y conexiones HTTP colgadas para los clientes.
  - **Implementación de Parada Limpia con Asyncio**:
```python
import asyncio
import signal

async def main():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        print("Señal de parada recibida. Iniciando Graceful Shutdown...")
        stop_event.set()

    # Registra listeners para señales del sistema operativo
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # Simula trabajo continuo
    worker_task = asyncio.create_task(run_background_workers())

    # Espera a la señal de parada
    await stop_event.wait()

    # 1. Deja de recibir nuevas peticiones
    # 2. Espera a que las tareas en curso finalicen con un timeout de seguridad
    worker_task.cancel()
    try:
        await asyncio.wait_for(worker_task, timeout=15.0)
    except asyncio.CancelledError:
        pass
    finally:
        # 3. Cierra pools de conexiones y sockets de forma limpia
        await close_database_pools()
        print("Servicio detenido de forma segura.")
```
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Ignorar el manejo de señales de terminación provocando estados corruptos en bases de datos durante despliegues continuos en Kubernetes.
  - 🟢 **Green Flag**: Coordinar el timeout de gracia interno de la aplicación con la configuración de `terminationGracePeriodSeconds` del Pod de Kubernetes.

---

### 100. ¿Cómo planificar y ejecutar la migración masiva de una base de código de Python legacy hacia las versiones modernas (3.11-3.13)?
- **Nivel**: Principal / Staff Python Architect
- **Respuesta Técnica**:
  - **Estrategia Metodológica por Fases**:
    1. **Fase 1: Auditoría de Compatibilidad de Dependencias**:
       - Escanear el archivo de dependencias con herramientas como `caniusepython3`.
       - Identificar dependencias abandonadas sin soporte para versiones modernas de Python y sustituirlas por librerías activas (ej. migrar de librerías antiguas con C-extensions deprecadas hacia alternativas modernas).
    2. **Fase 2: Automatización de Refactorización de Sintaxis (Codemods)**:
       - Utilizar herramientas de modernización de AST automatizadas como **pyupgrade** o **Ruff**:
```bash
# Actualiza automáticamente sintaxis antigua a Python 3.12+ (tipos nativos, f-strings, super())
ruff check --select UP --fix .
```
    3. **Fase 3: Aumento de la Suite de Pruebas y Tipado Progresivo**:
       - Asegurar que la suite de pruebas unitarias y de integración alcance al menos el 80% de cobertura en flujos de negocio críticos.
       - Activar Mypy progresivamente comenzando con módulos de infraestructura.
    4. **Fase 4: Ejecución en CI/CD con Matriz de Versiones**:
       - Correr la suite de CI simultáneamente contra la versión anterior y la versión objetivo.
    5. **Fase 5: Despliegue Canario en Producción**:
       - Desplegar la nueva versión de Python a una fracción del tráfico real (5% - 10%) monitorizando picos de memoria RSS y latencia de CPU antes de la migración global.
- **Diferenciadores en la entrevista**:
  - 🚩 **Red Flag**: Intentar reescribir manualmente miles de archivos a mano en una rama gigantesca de larga duración sin automatización de codemods ni suite de pruebas de regresión.
  - 🟢 **Green Flag**: Utilizar `pyupgrade` y desplegar en producción utilizando el 10-25% de mejora de rendimiento nativo aportado por el proyecto Faster CPython a partir de Python 3.11.
