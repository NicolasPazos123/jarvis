import ollama

from herramientas import DEFINICIONES, HERRAMIENTAS

# Probamos otro "cerebro": Qwen 2.5 suele ser más preciso usando herramientas.
# Para volver al anterior, cambia esta línea por: MODELO = "llama3.2:3b"
MODELO = "qwen2.5:3b"

# Temperatura baja: para decidir qué herramienta usar queremos precisión, no creatividad.
TEMPERATURA = 0.3

# Freno de seguridad: máximo de vueltas del agent loop por cada mensaje tuyo.
MAX_PASOS = 5

SYSTEM_PROMPT = """Tu nombre es Jarvis. Eres el asistente personal de Nicolás.

Quién eres:
- Fuiste creado por Nicolás como su proyecto personal de inteligencia artificial.
- Funcionas con un modelo de lenguaje que corre localmente en su Mac.

Herramientas:
- Tienes herramientas para ver la fecha y hora, crear notas y leer notas.
- Úsalas SOLO cuando la petición lo necesite. Para conversar, contar chistes o responder preguntas generales, NO las uses.
- Cuando leas las notas, muéstraselas a Nicolás tal como están escritas, no solo cuántas hay.
- Usa UNA herramienta a la vez. Si un paso necesita el resultado de otro (por ejemplo, anotar la hora), primero obtén el dato y luego usa ese valor real, nunca un texto genérico.
- Si Nicolás te pide hacer algo (anotar, guardar), HAZLO tú con la herramienta. Nunca le digas a él que lo haga.

Cómo debes responder:
- Responde siempre en español.
- Sé breve: máximo 3 oraciones, salvo que te pidan más detalle.
- Habla de forma cercana y natural, como un asistente de confianza.
- Si no sabes algo, dilo con honestidad. No inventes información.
"""

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
    try:
        return str(funcion(**argumentos))
    except Exception as error:
        return f"Error al ejecutar {nombre}: {error}"


while True:
    pregunta = input("\nTú: ")
    if pregunta == "salir":
        break

    mensajes.append({"role": "user", "content": pregunta})

    # ---------- EL AGENT LOOP ----------
    # Pensar -> actuar -> observar, y repetir hasta que el modelo ya no pida herramientas.
    termino = False
    for paso in range(MAX_PASOS):
        # PENSAR: el modelo decide si responde o pide herramientas
        texto, llamadas = llamar_modelo()

        if not llamadas:
            # Ya no necesita herramientas: esa es la respuesta final
            mensajes.append({"role": "assistant", "content": texto})
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
