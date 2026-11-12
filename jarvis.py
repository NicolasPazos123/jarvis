import re
import time
from datetime import datetime

import ollama

from herramientas import (
    DEFINICIONES,
    HERRAMIENTAS,
    HERRAMIENTAS_EXTERNAS,
    HERRAMIENTAS_PELIGROSAS,
    HERRAMIENTAS_QUE_MODIFICAN,
)
from memoria import UMBRAL, buscar_recuerdos
from voz import esperar_a_que_termine, hablar_frase
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

# ¿Se leyó contenido externo (un archivo) en este turno? Se reinicia con cada mensaje tuyo.
contexto_externo = False

# Medición de LATENCIA de cada turno
inicio_turno = 0.0          # cuándo presionaste Enter
primera_voz = None          # cuándo se mandó a decir la primera frase

# Una frase termina en . ! ? o salto de línea
FIN_DE_FRASE = re.compile(r"(.+?[.!?\n])(\s|$)", re.DOTALL)


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
    global primera_voz
    texto = ""
    llamadas = []
    empezo_a_escribir = False
    pendiente_de_hablar = ""  # texto que llegó pero todavía no forma una frase completa

    for chunk in stream:
        if chunk.message.tool_calls:
            llamadas.extend(chunk.message.tool_calls)
        if chunk.message.content:
            if not empezo_a_escribir:
                print("Jarvis: ", end="", flush=True)
                empezo_a_escribir = True
            print(chunk.message.content, end="", flush=True)
            texto += chunk.message.content

            # VOZ EN STREAMING: apenas se completa una frase, se manda a decir
            # mientras el modelo sigue generando la siguiente.
            if HABLAR:
                pendiente_de_hablar += chunk.message.content
                while (frase := FIN_DE_FRASE.match(pendiente_de_hablar)):
                    hablar_frase(frase.group(1))
                    if primera_voz is None:
                        primera_voz = time.time()
                    pendiente_de_hablar = pendiente_de_hablar[frase.end():]

    # Lo que quedó al final sin punto también se dice
    if HABLAR and pendiente_de_hablar.strip() and not llamadas:
        hablar_frase(pendiente_de_hablar)
        if primera_voz is None:
            primera_voz = time.time()

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

    # DEFENSA 3 (contexto contaminado): si en este turno se leyó un archivo y ahora
    # el modelo quiere GUARDAR o CREAR algo, puede ser una orden escondida en ese archivo.
    contaminado = contexto_externo and nombre in HERRAMIENTAS_QUE_MODIFICAN
    if contaminado:
        print("     🛡️  Esta acción viene DESPUÉS de leer un archivo externo: podría ser un prompt injection.")

    # HUMAN-IN-THE-LOOP: las acciones peligrosas o "contaminadas" necesitan tu permiso.
    if nombre in HERRAMIENTAS_PELIGROSAS or contaminado:
        permiso = input("     ⚠️  ¿Permites esta acción? (s/n): ").strip().lower()
        if permiso != "s":
            return "El usuario rechazó esta acción, así que NO se ejecutó. Dile en segunda persona (tú) que no lo hiciste porque no lo autorizó, y pregúntale qué prefiere hacer."
    try:
        return str(funcion(**argumentos))
    except Exception as error:
        return f"Error al ejecutar {nombre}: {error}"


try:
    while True:
        # Esperamos a que Jarvis termine de hablar (para que el micrófono no lo grabe a él)
        esperar_a_que_termine()

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

        inicio_turno = time.time()
        primera_voz = None

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
        contexto_externo = False
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
                # Medimos la latencia del turno
                fin = time.time()
                if HABLAR and primera_voz is not None:
                    print(f"  ⏱️  Empezó a hablar a los {primera_voz - inicio_turno:.1f} s · "
                          f"respuesta completa a los {fin - inicio_turno:.1f} s "
                          f"(antes esperaba los {fin - inicio_turno:.1f} s completos para hablar)")
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
            if llamada.function.name in HERRAMIENTAS_EXTERNAS:
                contexto_externo = True

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

        # DEFENSA 5 (higiene del contexto): al terminar el turno, borramos del historial
        # el texto completo de los archivos leídos. Así, si un archivo traía instrucciones
        # maliciosas, no se quedan "envenenando" los siguientes mensajes.
        for m in mensajes:
            if isinstance(m, dict) and m.get("role") == "tool" and "<<<INICIO DEL ARCHIVO" in m.get("content", ""):
                m["content"] = "[Aquí estaba el contenido de un archivo leído antes. Se quitó por seguridad; si lo necesitas, vuelve a leerlo.]"
except (KeyboardInterrupt, EOFError):
    # Ctrl+C: salimos de forma ordenada en vez de mostrar un error
    print("\n👋 Hasta luego, Nicolás.")
