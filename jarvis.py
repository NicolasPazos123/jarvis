import ollama

MODELO = "llama3.2:3b"

# Temperatura: qué tan "arriesgado" es el modelo al elegir el siguiente token.
# 0 = siempre elige el más probable (predecible). Más alto = más variado/creativo.
TEMPERATURA = 0.7

# El system prompt: las instrucciones de fondo que definen quién es Jarvis.
SYSTEM_PROMPT = """Tu nombre es Jarvis. Eres el asistente personal de Nicolás.

Quién eres:
- Fuiste creado por Nicolás como su proyecto personal de inteligencia artificial.
- Funcionas con un modelo de lenguaje que corre localmente en su Mac.

Cómo debes responder:
- Responde siempre en español.
- Sé breve: máximo 3 oraciones, salvo que te pidan más detalle.
- Habla de forma cercana y natural, como un asistente de confianza.
- Si no sabes algo, dilo con honestidad. No inventes información.
"""

# El historial vive FUERA del while: así no se borra en cada vuelta.
mensajes = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

while True:
    pregunta = input("\nTú: ")
    if pregunta == "salir":
        break

    # 1. Guardamos lo que dijiste en el historial
    mensajes.append({"role": "user", "content": pregunta})

    # 2. Pedimos la respuesta en modo streaming: llega en pedazos (chunks)
    #    a medida que el modelo genera cada token, en vez de toda al final.
    stream = ollama.chat(
        model=MODELO,
        messages=mensajes,
        stream=True,
        options={"temperature": TEMPERATURA},
    )

    print("Jarvis: ", end="", flush=True)
    texto = ""
    for chunk in stream:
        pedazo = chunk["message"]["content"]
        print(pedazo, end="", flush=True)  # lo mostramos apenas llega
        texto += pedazo                    # y lo vamos juntando
    print()

    # 3. Guardamos la respuesta completa en el historial
    mensajes.append({"role": "assistant", "content": texto})
