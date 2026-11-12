"""La voz de Jarvis: convierte texto en audio (Text-to-Speech, TTS).
Usa el comando 'say' que ya viene incluido en macOS: gratis y sin instalar nada."""

import queue
import re
import shutil
import subprocess
import threading

# Voz en español. Si no la tienes instalada, se usa la voz por defecto del sistema.
VOZ = "Paulina"


def _limpiar(texto):
    """Quita símbolos de formato (*, #, `) y emojis para que no los lea en voz alta."""
    texto = re.sub(r"[*_#`>\[\]]", "", texto)
    texto = re.sub(r"[^\w\s.,;:¿?¡!()\-/%$]", "", texto)
    return texto.strip()


def hablar(texto):
    texto = _limpiar(texto)
    if not texto or shutil.which("say") is None:
        return
    resultado = subprocess.run(["say", "-v", VOZ, texto], capture_output=True)
    if resultado.returncode != 0:
        # La voz elegida no está disponible: usamos la del sistema
        subprocess.run(["say", texto])


# ---------- Voz en streaming: hablar FRASE POR FRASE mientras el modelo sigue escribiendo ----------
# Una "cola" es como la fila de un banco: las frases entran en orden y un trabajador
# en segundo plano (un hilo, "thread") las va diciendo una por una, sin bloquear al resto.
_cola = queue.Queue()


def _trabajador():
    while True:
        frase = _cola.get()
        hablar(frase)
        _cola.task_done()


threading.Thread(target=_trabajador, daemon=True).start()


def hablar_frase(frase):
    """Pone una frase en la fila para ser dicha en voz alta. Vuelve de inmediato."""
    if _limpiar(frase):
        _cola.put(frase)


def esperar_a_que_termine():
    """Espera a que se digan todas las frases de la fila."""
    _cola.join()
