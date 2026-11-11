import re
from datetime import datetime

import ollama

from herramientas import DEFINICIONES, HERRAMIENTAS, HERRAMIENTAS_PELIGROSAS
from memoria import UMBRAL, buscar_recuerdos
from voz import hablar
from oido import escuchar
from config import MODELO, SYSTEM_PROMPT, TEMPERATURA

# Si es True, Jarvis lee en voz alta su respuesta final (Text-to-Speech).
HABLAR = True

# Verificador: frases con las que el modelo dice que YA hizo una acción.
# Si las usa sin haber ejecutado ninguna herramienta, está alucinando una acción.
FRASES_DE_ACCION = re.compile(
    r"\b(cre[eé]|he creado|guard[eé]|he guardado|anot[eé]|he anotado|program[eé]|he programado|agend[eé])\b",
    re.IGNORECASE,
)

# Freno de seguridad: máximo de vueltas del agent loop por cada mensaje tuyo.
MAX_PASOS = 5

mensajes = [
    {"role": "system", "content": SYSTEM_PROMPT},
]


def llamar_modelo():
    """Una vuelta del modelo, en streaming.
    Devuelve el texto que escribió y las herramientas que pidió (si pidió alguna)."""
    stream = ollama.chat(
        model=MODELO,
        messages=mensajes,
        tools=DEFINICIONES,
        stream=True,
        options={"temperature": TEMPERATURA},
    )
    texto = ""
    llamadas = []
    empezo_a_escribir = False
    for chunk in stream:
        if chunk.message.tool_calls:
            llamadas.extend(chunk.message.tool_calls)
        if chunk.message.content:
            if not empezo_a_escribir:
                print("Jarvis: ", end="", flush=True)
                empezo_a_escribir = True
            print(chunk.message.content, end="", flush=True)
            texto += chunk.message.content
    if empezo_a_escribir:
        print()
    return texto, llamadas


def ejecutar_herramienta(llamada):
    """Nuestro programa (el ayudante) ejecuta la función real que pidió el modelo."""
    nombre = llamada.function.name
    argumentos = llamada.function.arguments or {}
    print(f"  🔧 Jarvis usa la herramienta: {nombre}({argumentos})")

    funcion = HERRAMIENTAS.get(nombre)
    if funcion is None:
        return f"Error: la herramienta '{nombre}' no existe."

    # HUMAN-IN-THE-LOOP: las acciones que cambian algo necesitan tu permiso.
    if nombre in HERRAMIENTAS_PELIGROSAS:
        permiso = input("     ⚠️  ¿Permites esta acción? (s/n): ").strip().lower()
        if permiso != "s":
            return "El usuario rechazó esta acción, así que NO se ejecutó. Dile en segunda persona (tú) que no lo hiciste porque no lo autorizó, y pregúntale qué prefiere hacer."
    try:
        return str(funcion(**argumentos))
    except Exception as error:
        return f"Error al ejecutar {nombre}: {error}"


try:
    while True:
        # Puedes escribir tu mensaje, o dejarlo vacío y presionar Enter para HABLAR.
        pregunta = input("\nTú (escribe, o Enter para hablar): ").strip()
        if not pregunta:
            pregunta = escuchar()  # STT: tu voz -> texto
            if not pregunta:
                print("  (No escuché nada. Acércate al micrófono o habla un poco más fuerte.)")
                continue
            print(f"Tú (voz): {pregunta}")

        if pregunta.lower().strip(" .!¡") == "salir":
            break

        # ---------- RAG: Retrieval-Augmented Generation ----------
        # R (Retrieval): buscamos los recuerdos más parecidos a la pregunta.
        # Pedimos el top 3 SIN umbral para poder ver todos los puntajes (modo diagnóstico).
        candidatos = buscar_recuerdos(pregunta, umbral=0.0)
        encontrados = [(p, r) for p, r in candidatos if p >= UMBRAL]

        if candidatos:
            print(f"  🧠 Búsqueda en memoria (umbral {UMBRAL}):")
            for puntaje, recuerdo in candidatos:
                marca = "✅" if puntaje >= UMBRAL else "❌"
                print(f"     {marca} {puntaje:.3f}  {recuerdo['texto']}")

        # A (Augmented): agregamos la fecha actual y los recuerdos que pasaron el umbral
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        momento = datetime.now()
        ahora = f"{dias[momento.weekday()]} {momento:%Y-%m-%d %H:%M}"
        contenido = f"{pregunta}\n\n[Fecha y hora actual: {ahora}]"
        if encontrados:
            lista = "\n".join(f"- ({r['fecha']}) {r['texto']}" for _, r in encontrados)
            contenido += f"\n\n[Recuerdos guardados que pueden servir para responder:\n{lista}]"

        mensajes.append({"role": "user", "content": contenido})

        # G (Generation): el modelo responde, ya con esos recuerdos en su contexto
        # ---------- EL AGENT LOOP ----------
        # Pensar -> actuar -> observar, y repetir hasta que el modelo ya no pida herramientas.
        termino = False
        uso_herramientas = False
        for paso in range(MAX_PASOS):
            # PENSAR: el modelo decide si responde o pide herramientas
            texto, llamadas = llamar_modelo()

            # VERIFICADOR: ¿dice que hizo algo sin haber usado ninguna herramienta?
            if not llamadas and not uso_herramientas and FRASES_DE_ACCION.search(texto):
                print("  🚨 Verificador: dijo que hizo una acción, pero NO usó ninguna herramienta. Le pido que la haga de verdad.")
                mensajes.append({"role": "assistant", "content": texto})
                mensajes.append({
                    "role": "user",
                    "content": "[Sistema: dijiste que hiciste una acción, pero NO usaste ninguna herramienta, "
                               "así que en realidad no se hizo. Usa ahora la herramienta correcta.]",
                })
                continue

            if not llamadas:
                # Ya no necesita herramientas: esa es la respuesta final
                mensajes.append({"role": "assistant", "content": texto})
                if HABLAR and texto:
                    hablar(texto)  # TTS: Jarvis lee su respuesta en voz alta
                termino = True
                break

            # El modelo a veces pide VARIAS herramientas de golpe, aunque una dependa
            # del resultado de otra. Para obligarlo a ir paso a paso, ejecutamos solo
            # la PRIMERA. En la siguiente vuelta ya habrá visto el resultado y pedirá lo que siga.
            llamada = llamadas[0]

            # Guardamos en el historial QUÉ pidió el modelo (solo la que vamos a ejecutar)
            mensajes.append({"role": "assistant", "content": texto, "tool_calls": [llamada]})

            # ACTUAR + OBSERVAR: ejecutamos y le devolvemos el resultado
            print(f"  (paso {paso + 1})", end="")
            resultado = ejecutar_herramienta(llamada)
            uso_herramientas = True

            # Si había otras herramientas pendientes, se lo recordamos al modelo
            # junto con el resultado, para que no "olvide" su plan.
            pendientes = [l.function.name for l in llamadas[1:]]
            if pendientes:
                print(f"     ⏸  Pospuestas para el siguiente paso: {', '.join(pendientes)}")
                resultado += (
                    f"\n\n[Nota del sistema: solo se ejecutó esta herramienta. "
                    f"Todavía tenías pendiente: {', '.join(pendientes)}. "
                    f"Pídela(s) ahora usando este resultado real.]"
                )

            mensajes.append({"role": "tool", "content": resultado})

        if not termino:
            print("Jarvis: Me detuve porque necesité demasiados pasos seguidos. ¿Lo intentamos de otra forma?")
except (KeyboardInterrupt, EOFError):
    # Ctrl+C: salimos de forma ordenada en vez de mostrar un error
    print("\n👋 Hasta luego, Nicolás.")
