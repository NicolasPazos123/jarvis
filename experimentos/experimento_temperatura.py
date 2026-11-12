import ollama

MODELO = "llama3.2:3b"
PREGUNTA = "Inventa un nombre para una banda de rock. Responde solo con el nombre."

# Hacemos la MISMA pregunta 3 veces con cada temperatura y comparamos.
for temperatura in [0, 1.5]:
    print(f"\n--- Temperatura {temperatura} ---")
    for i in range(3):
        respuesta = ollama.chat(
            model=MODELO,
            messages=[{"role": "user", "content": PREGUNTA}],
            options={"temperature": temperatura},
        )
        print(f"{i + 1}. {respuesta['message']['content'].strip()}")
