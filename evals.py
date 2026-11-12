"""EVALS: pruebas automáticas que miden qué tan bien funciona Jarvis.
En vez de probar a mano cada vez, tenemos un "examen con solucionario":
casos de prueba con la respuesta esperada, y un puntaje final.

Uso:
    python3 evals.py                 -> evalúa con el modelo de config.py
    python3 evals.py llama3.2:3b     -> evalúa con otro modelo para comparar
"""

import sys
import time

import ollama

from config import MODELO, SYSTEM_PROMPT
from herramientas import DEFINICIONES
from memoria import UMBRAL, embedding, similitud_coseno

modelo = sys.argv[1] if len(sys.argv) > 1 else MODELO


# =====================================================================
# EVAL 1: ¿Elige la herramienta correcta?
# Solo miramos QUÉ herramienta PIDE el modelo. No la ejecutamos,
# así que el examen no crea notas, archivos ni recordatorios de verdad.
# =====================================================================

CASOS_HERRAMIENTAS = [
    # (mensaje, herramienta esperada o None si NO debe usar ninguna)
    ("¿Qué hora es?", "obtener_fecha_hora"),
    ("Anota que debo llamar al banco", "crear_nota"),
    ("¿Qué notas tengo?", "leer_notas"),
    ("¿Qué archivos tengo?", "listar_archivos"),
    ("Lee el archivo ideas.txt", "leer_archivo"),
    ("Recuerda que mi color favorito es el azul", "guardar_recuerdo"),
    ("Recuérdame en 10 minutos estirar la espalda", "crear_recordatorio"),
    ("Recuérdame el jueves a las 9 de la mañana ir al médico", "crear_recordatorio"),
    ("Cuéntame un chiste", None),
    ("¿Cuál es la capital de Perú?", None),
    ("Hola, ¿cómo estás?", None),
    ("Explícame qué es un embedding en una línea", None),
]


def herramienta_elegida(mensaje):
    """Una sola llamada al modelo. Devuelve (nombre de la herramienta o None, argumentos)."""
    respuesta = ollama.chat(
        model=modelo,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": mensaje},
        ],
        tools=DEFINICIONES,
        options={"temperature": 0},  # temperatura 0: resultados repetibles, para comparar de forma justa
    )
    llamadas = respuesta.message.tool_calls
    if not llamadas:
        return None, {}
    return llamadas[0].function.name, llamadas[0].function.arguments or {}


def eval_herramientas():
    print(f"\n🧪 EVAL 1: elección de herramientas  (modelo: {modelo})\n")

    # Calentamiento: la primera llamada carga el modelo en la RAM (cold start).
    # La hacemos ANTES de medir, para que no ensucie los tiempos.
    print("  (cargando el modelo en la RAM...)")
    inicio = time.time()
    herramienta_elegida("hola")
    print(f"  ❄️  Cold start: {time.time() - inicio:.1f} s\n")

    aciertos = 0
    tiempos = []
    for mensaje, esperada in CASOS_HERRAMIENTAS:
        inicio = time.time()
        elegida, argumentos = herramienta_elegida(mensaje)
        tiempos.append(time.time() - inicio)
        ok = elegida == esperada
        aciertos += ok
        marca = "✅" if ok else "❌"
        detalle = f"{elegida}({argumentos})" if elegida else "ninguna"
        print(f"  {marca} {mensaje:<58} esperaba: {str(esperada):<20} eligió: {detalle}")
    promedio = sum(tiempos) / len(tiempos)
    print(f"\n  ⏱️  Tiempo promedio por respuesta (en caliente): {promedio:.2f} s")
    return aciertos, len(CASOS_HERRAMIENTAS), promedio


# =====================================================================
# EVAL 2: ¿La búsqueda en memoria (RAG) trae el recuerdo correcto?
# Usamos recuerdos de PRUEBA en memoria temporal: no tocamos tu memoria.json.
# =====================================================================

RECUERDOS_PRUEBA = [
    "Mañana tengo rutina de pesas en el gimnasio",
    "El martes tengo entrega del proyecto de Bases de Datos de la universidad",
    "Mi comida favorita es el encebollado",
    "El viernes tengo partido de fútbol",
    "La reunión con mi jefe es el jueves a las 10",
]

CASOS_MEMORIA = [
    # (pregunta, índice del recuerdo correcto, o None si NINGUNO debería pasar el umbral)
    ("¿Cuándo hago ejercicio?", 0),
    ("¿Qué tengo pendiente de la universidad?", 1),
    ("¿Qué me recomiendas almorzar?", 2),
    ("¿Tengo algún partido esta semana?", 3),
    ("¿Cuándo me reúno con mi jefe?", 4),
    ("¿Cuál es la capital de Francia?", None),
    ("¿Cómo funciona un motor de avión?", None),
]


def eval_memoria():
    print(f"\n🧪 EVAL 2: búsqueda en memoria  (umbral {UMBRAL})\n")
    vectores = [embedding(r) for r in RECUERDOS_PRUEBA]
    aciertos = 0
    for pregunta, correcto in CASOS_MEMORIA:
        v = embedding(pregunta)
        puntajes = [similitud_coseno(v, vr) for vr in vectores]
        mejor = max(range(len(puntajes)), key=lambda i: puntajes[i])
        paso_umbral = puntajes[mejor] >= UMBRAL

        if correcto is None:
            ok = not paso_umbral  # éxito = no trajo nada
            obtenido = "nada" if not paso_umbral else f"'{RECUERDOS_PRUEBA[mejor]}'"
        else:
            ok = paso_umbral and mejor == correcto  # éxito = el correcto quedó primero Y pasó el umbral
            obtenido = f"'{RECUERDOS_PRUEBA[mejor]}'" + ("" if paso_umbral else " (no pasó el umbral)")

        aciertos += ok
        marca = "✅" if ok else "❌"
        print(f"  {marca} {pregunta:<42} {puntajes[mejor]:.3f}  trajo: {obtenido}")
    return aciertos, len(CASOS_MEMORIA)


if __name__ == "__main__":
    a1, t1, velocidad = eval_herramientas()
    a2, t2 = eval_memoria()
    print(f"\n📊 RESULTADO  ({modelo})")
    print(f"  Herramientas: {a1}/{t1}  ({a1 / t1:.0%})")
    print(f"  Velocidad:    {velocidad:.2f} s por respuesta")
    print(f"  Memoria:      {a2}/{t2}  ({a2 / t2:.0%})")
