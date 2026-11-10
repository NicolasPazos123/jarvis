"""El oído de Jarvis: convierte tu voz en texto (Speech-to-Text, STT).
Usa Whisper, un modelo open source de reconocimiento de voz, optimizado
para los chips de Apple (M1) gracias a la librería MLX."""

import numpy as np
import sounddevice as sd
import mlx_whisper

# Whisper trabaja con audio a 16.000 muestras por segundo, en un solo canal (mono).
FRECUENCIA = 16000

# Tamaño "small": buen equilibrio entre precisión en español y velocidad en tu Mac.
MODELO_STT = "mlx-community/whisper-small-mlx"


def grabar():
    """Graba desde el micrófono hasta que presiones Enter.
    Devuelve (audio, texto_escrito): si escribiste algo mientras grababa, lo devolvemos también."""
    partes = []

    def guardar_pedazo(indata, frames, tiempo, estado):
        partes.append(indata.copy())

    with sd.InputStream(samplerate=FRECUENCIA, channels=1, dtype="float32", callback=guardar_pedazo):
        escrito = input("  🔴 Grabando... habla y presiona Enter para terminar.\n").strip()

    if not partes:
        return np.zeros(0, dtype=np.float32), escrito
    return np.concatenate(partes).flatten(), escrito


def escuchar():
    """Graba tu voz y devuelve el texto que dijiste."""
    audio, escrito = grabar()

    # Si escribiste algo mientras grababa (por ejemplo "salir"), usamos eso y no transcribimos.
    if escrito:
        return escrito

    # Menos de medio segundo de audio: no hay nada que transcribir
    if len(audio) < FRECUENCIA * 0.5:
        return ""

    # Volumen promedio muy bajo = silencio. Whisper con silencio tarda y a veces inventa texto.
    volumen = float(np.sqrt(np.mean(audio ** 2)))
    if volumen < 0.005:
        return ""

    print("  ✍️  Transcribiendo...")
    resultado = mlx_whisper.transcribe(audio, path_or_hf_repo=MODELO_STT, language="es")
    return resultado["text"].strip()
