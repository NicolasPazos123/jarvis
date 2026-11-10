"""Experimento: buscar por SIGNIFICADO usando embeddings."""

import math

import ollama

# nomic-embed-text fue entrenado sobre todo en inglés y falló con nuestras frases en español.
# bge-m3 es multilingüe: entiende bien el español.
MODELO_EMBEDDINGS = "bge-m3"

# Recuerdos guardados (imagina que Jarvis los fue anotando con el tiempo)
RECUERDOS = [
    "Mañana tengo rutina de pesas en el gimnasio",
    "El martes tengo entrega del proyecto de Bases de Datos",
    "Me gusta escuchar rock en la noche",
    "Tengo que comprar leche y pan",
    "La reunión con mi jefe es el jueves a las 10",
    "Quiero aprender a tocar piano",
]

# Preguntas que NO comparten palabras exactas con los recuerdos
CONSULTAS = [
    "¿Cuándo hago ejercicio?",
    "¿Qué tengo pendiente de la universidad?",
    "música",
]


def embedding(texto):
    """Convierte un texto en una lista de números (su 'coordenada' de significado)."""
    return ollama.embed(model=MODELO_EMBEDDINGS, input=texto)["embeddings"][0]


def similitud_coseno(a, b):
    """Qué tan parecidos son dos vectores: 1 = mismo significado, 0 = nada que ver."""
    producto = sum(x * y for x, y in zip(a, b))
    largo_a = math.sqrt(sum(x * x for x in a))
    largo_b = math.sqrt(sum(y * y for y in b))
    return producto / (largo_a * largo_b)


# 1. Veamos cómo luce un embedding por dentro
ejemplo = embedding(RECUERDOS[0])
print(f'Embedding de "{RECUERDOS[0]}":')
print(f"  Tiene {len(ejemplo)} números. Los primeros 5 son: {[round(n, 3) for n in ejemplo[:5]]}\n")

# 2. Convertimos todos los recuerdos en embeddings (una sola vez)
vectores = [embedding(r) for r in RECUERDOS]

# 3. Para cada consulta, ordenamos los recuerdos de más a menos parecido
for consulta in CONSULTAS:
    v_consulta = embedding(consulta)
    puntajes = [(similitud_coseno(v_consulta, v), r) for v, r in zip(vectores, RECUERDOS)]
    puntajes.sort(reverse=True)

    print(f'🔎 "{consulta}"')
    for puntaje, recuerdo in puntajes[:3]:
        print(f"   {puntaje:.3f}  {recuerdo}")
    print()
