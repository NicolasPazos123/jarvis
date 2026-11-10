"""Las herramientas (tools) de Jarvis: funciones normales de Python
que el modelo puede PEDIR que ejecutemos."""

from datetime import datetime
from pathlib import Path

from memoria import guardar_recuerdo

ARCHIVO_NOTAS = Path(__file__).parent / "notas.txt"

# La ÚNICA carpeta donde Jarvis puede leer y escribir archivos (su "sandbox").
CARPETA_TRABAJO = (Path(__file__).parent / "espacio_jarvis").resolve()
CARPETA_TRABAJO.mkdir(exist_ok=True)

# Máximo de caracteres que devolvemos al leer un archivo (para no llenar la ventana de contexto).
MAX_CARACTERES = 3000

# Herramientas que cambian algo: el programa pedirá tu confirmación antes de ejecutarlas.
HERRAMIENTAS_PELIGROSAS = {"escribir_archivo"}


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


def _ruta_segura(nombre_archivo):
    """Convierte un nombre en ruta y verifica que esté DENTRO de la carpeta permitida.
    Bloquea trucos como "../jarvis.py" para salirse del sandbox."""
    ruta = (CARPETA_TRABAJO / nombre_archivo).resolve()
    if ruta.parent != CARPETA_TRABAJO and CARPETA_TRABAJO not in ruta.parents:
        raise PermissionError("Acceso denegado: solo puedo usar archivos dentro de espacio_jarvis.")
    return ruta


def listar_archivos():
    archivos = sorted(a.name for a in CARPETA_TRABAJO.iterdir() if a.is_file())
    if not archivos:
        return "La carpeta espacio_jarvis está vacía."
    return "Archivos disponibles:\n" + "\n".join(f"- {a}" for a in archivos)


def leer_archivo(nombre):
    ruta = _ruta_segura(nombre)
    if not ruta.exists():
        return f"El archivo '{nombre}' no existe. Usa listar_archivos para ver cuáles hay."
    contenido = ruta.read_text(encoding="utf-8", errors="replace")
    if len(contenido) > MAX_CARACTERES:
        contenido = contenido[:MAX_CARACTERES] + f"\n\n[...archivo recortado: se muestran solo {MAX_CARACTERES} caracteres]"
    return contenido


def escribir_archivo(nombre, contenido):
    ruta = _ruta_segura(nombre)
    ruta.write_text(contenido, encoding="utf-8")
    return f"Archivo '{nombre}' guardado ({len(contenido)} caracteres)."


# Diccionario para encontrar la función a partir de su nombre
HERRAMIENTAS = {
    "obtener_fecha_hora": obtener_fecha_hora,
    "crear_nota": crear_nota,
    "leer_notas": leer_notas,
    "listar_archivos": listar_archivos,
    "leer_archivo": leer_archivo,
    "escribir_archivo": escribir_archivo,
    "guardar_recuerdo": guardar_recuerdo,
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
    {
        "type": "function",
        "function": {
            "name": "listar_archivos",
            "description": "Lista los archivos que hay en la carpeta de trabajo de Jarvis. Úsala cuando pregunten qué archivos hay o antes de leer uno si no conoces el nombre exacto.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leer_archivo",
            "description": "Lee el contenido de un archivo de la carpeta de trabajo. Úsala cuando pidan leer, revisar o resumir un archivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del archivo, por ejemplo ideas.txt"},
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escribir_archivo",
            "description": "Crea o reemplaza un archivo en la carpeta de trabajo con el contenido indicado. Úsala cuando pidan crear o guardar un archivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del archivo, por ejemplo plan.txt"},
                    "contenido": {"type": "string", "description": "Texto completo que tendrá el archivo"},
                },
                "required": ["nombre", "contenido"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_recuerdo",
            "description": "Guarda un dato importante sobre Nicolás en su memoria a largo plazo. Úsala cuando diga 'recuerda que...' o comparta algo personal útil para el futuro (gustos, planes, fechas, pendientes). Escribe el recuerdo claro y con contexto, por ejemplo 'Bases de Datos es una materia de la universidad'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "El recuerdo, redactado de forma clara y con contexto"},
                },
                "required": ["texto"],
            },
        },
    },
]
