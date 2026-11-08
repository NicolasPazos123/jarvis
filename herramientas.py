"""Las herramientas (tools) de Jarvis: funciones normales de Python
que el modelo puede PEDIR que ejecutemos."""

from datetime import datetime
from pathlib import Path

ARCHIVO_NOTAS = Path(__file__).parent / "notas.txt"


# ---------- 1. Las funciones reales (lo que de verdad se ejecuta) ----------

def obtener_fecha_hora():
    return datetime.now().strftime("%d/%m/%Y, %H:%M")


def crear_nota(texto):
    with open(ARCHIVO_NOTAS, "a", encoding="utf-8") as archivo:
        archivo.write(f"- [{datetime.now():%d/%m/%Y %H:%M}] {texto}\n")
    return f"Nota guardada: {texto}"


def leer_notas():
    if not ARCHIVO_NOTAS.exists():
        return "No hay notas guardadas."
    return ARCHIVO_NOTAS.read_text(encoding="utf-8")


# Diccionario para encontrar la función a partir de su nombre
HERRAMIENTAS = {
    "obtener_fecha_hora": obtener_fecha_hora,
    "crear_nota": crear_nota,
    "leer_notas": leer_notas,
}


# ---------- 2. Las descripciones (lo único que el modelo VE) ----------
# El modelo nunca ve el código de arriba. Solo lee estos "menús":
# nombre, para qué sirve y qué datos necesita (parámetros).

DEFINICIONES = [
    {
        "type": "function",
        "function": {
            "name": "obtener_fecha_hora",
            "description": "Obtiene la fecha y hora actual. Úsala cuando pregunten qué día, fecha u hora es.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_nota",
            "description": "Guarda una nota para Nicolás. Úsala cuando pida anotar, apuntar o guardar algo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "El contenido de la nota"},
                },
                "required": ["texto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leer_notas",
            "description": "Lee todas las notas guardadas. Úsala cuando Nicolás pregunte por sus notas o qué anotó.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
