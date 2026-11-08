import ollama

MODELO = "llama3.2:3b"

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
# Empieza solo con el system prompt.
mensajes = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

while True:
    pregunta = input("Tú: ")
    if pregunta == "salir":
        break

    # 1. Guardamos lo que dijiste en el historial
    mensajes.append({"role": "user", "content": pregunta})

    # 2. Le enviamos TODA la conversación al modelo, no solo la última pregunta
    respuesta = ollama.chat(model=MODELO, messages=mensajes)
    texto = respuesta["message"]["content"]
    print("Jarvis:", texto)

    # 3. Guardamos también lo que respondió Jarvis
    mensajes.append({"role": "assistant", "content": texto})
