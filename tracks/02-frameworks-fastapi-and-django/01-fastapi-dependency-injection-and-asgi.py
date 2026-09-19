#!/usr/bin/env python3
"""
================================================================================
LAB 02: FASTAPI DEPENDENCY INJECTION ENGINE & ASGI PROTOCOL INTERNALS
================================================================================
Demuestra a nivel Senior:
1. El protocolo ASGI (Asynchronous Server Gateway Interface): Scope, Receive, Send.
2. Motor de Inyección de Dependencias (DI) estilo FastAPI:
   - Resolución en grafo (DAG) de dependencias anidadas.
   - Dependencias con generadores (`yield`) para setup y teardown garantizado.
   - Cacheo de dependencias en el mismo scope de request (`use_cache=True`).
================================================================================
"""

import asyncio
from typing import Callable, Any, Dict, List
import inspect

print("=" * 80)
print("🌐 [1/2] ASGI PROTOCOL INTERNALS: ESPECIFICACIÓN ASINCRONA DE SERVIDOR")
print("=" * 80)

# Una app ASGI es simplemente un callable asíncrono que recibe (scope, receive, send)
async def minimal_asgi_app(scope: dict, receive: Callable, send: Callable):
    assert scope["type"] == "http"
    
    path = scope.get("path", "/")
    method = scope.get("method", "GET")
    
    # Enviar cabeceras HTTP de respuesta
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            [b"content-type", b"application/json"],
            [b"x-framework", b"Python-Mastery-ASGI"]
        ]
    })
    
    # Enviar cuerpo
    body = f'{{"status":"ok","route":"{method} {path}","protocol":"ASGI/3.0"}}'.encode("utf-8")
    await send({
        "type": "http.response.body",
        "body": body,
        "more_body": False
    })

# Simulación de llamada ASGI por un servidor como Uvicorn / Hypercorn
async def simulate_asgi_request():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/health",
        "headers": []
    }
    
    sent_events = []
    
    async def mock_receive():
        return {"type": "http.request", "body": b"", "more_body": False}
        
    async def mock_send(event: dict):
        sent_events.append(event)
        
    await minimal_asgi_app(scope, mock_receive, mock_send)
    
    print("✅ Petición ASGI simulada:")
    for event in sent_events:
        print(f"   Evento ASGI emitido: {event['type']} -> {event}")

asyncio.run(simulate_asgi_request())

print("\n" + "=" * 80)
print("💉 [2/2] MOTOR DE INYECCIÓN DE DEPENDENCIAS (FASTAPI DEPENDS & LIFECYCLE)")
print("=" * 80)

# Simulador de Depends de FastAPI
class Depends:
    def __init__(self, dependency: Callable[..., Any], use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache

class DependencyInjector:
    """Resuelve grafos de dependencias con soporte para generadores (setup/teardown)."""
    
    def __init__(self):
        self.cache: Dict[Callable, Any] = {}
        self.cleanups: List[Any] = []

    async def resolve(self, target: Callable[..., Any]) -> Any:
        sig = inspect.signature(target)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if isinstance(param.default, Depends):
                dep_fn = param.default.dependency
                use_cache = param.default.use_cache

                if use_cache and dep_fn in self.cache:
                    resolved_value = self.cache[dep_fn]
                else:
                    # Si la dependencia también tiene parámetros, resolver recursivamente
                    dep_kwargs = await self._resolve_kwargs(dep_fn)
                    
                    if inspect.isgeneratorfunction(dep_fn):
                        # Soporte para yield (ej: base de datos / transacciones)
                        gen = dep_fn(**dep_kwargs)
                        resolved_value = next(gen)
                        self.cleanups.append(gen)
                    elif inspect.iscoroutinefunction(dep_fn):
                        resolved_value = await dep_fn(**dep_kwargs)
                    else:
                        resolved_value = dep_fn(**dep_kwargs)

                    if use_cache:
                        self.cache[dep_fn] = resolved_value

                kwargs[param_name] = resolved_value

        if inspect.iscoroutinefunction(target):
            return await target(**kwargs)
        return target(**kwargs)

    async def _resolve_kwargs(self, fn: Callable) -> dict:
        sig = inspect.signature(fn)
        sub_kwargs = {}
        for p_name, p in sig.parameters.items():
            if isinstance(p.default, Depends):
                sub_kwargs[p_name] = await self.resolve(p.default.dependency)
        return sub_kwargs

    def close(self):
        """Ejecuta los teardoowns posteriores al yield (cerrar conexiones, rollback/commit)."""
        for gen in reversed(self.cleanups):
            try:
                next(gen)
            except StopIteration:
                pass

# Definición de dependencias de prueba
def get_db_connection():
    print("      [DB] 🔌 Abriendo conexión a BD / transacción...")
    conn = {"connection_id": "pg-session-8821", "status": "active"}
    yield conn
    print("      [DB] 🔒 Cerrando conexión a BD de forma garantizada.")

def get_auth_token():
    return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

def get_current_user(token: str = Depends(get_auth_token)):
    return {"user_id": 42, "role": "admin", "token": token[:15] + "..."}

# Endpoint
async def checkout_endpoint(
    db = Depends(get_db_connection),
    user = Depends(get_current_user)
):
    print(f"      [ENDPOINT] Procesando pago para usuario: {user['user_id']} con DB: {db['connection_id']}")
    return {"status": "success", "order_id": 99201}

# Demostración del ciclo de vida
async def run_di_demo():
    injector = DependencyInjector()
    try:
        print("\nResolviendo dependencias para checkout_endpoint:")
        result = await injector.resolve(checkout_endpoint)
        print(f"Resultado final del endpoint: {result}")
    finally:
        print("\nFase de Teardown (Cierre de recursos):")
        injector.close()

asyncio.run(run_di_demo())

print("\n" + "=" * 80)
print("🎯 CONCLUSIÓN SENIOR FASTAPI:")
print("- FastAPI desacopla infraestructura de lógica de negocio usando el sistema de Depends.")
print("- Toda llamada HTTP es orquestada sobre la especificación ASGI 3.0.")
print("=" * 80)
