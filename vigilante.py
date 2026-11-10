"""El vigilante: un proceso que corre en SEGUNDO PLANO, en otra Terminal.
No espera a que le escribas: revisa cada 30 segundos si llegó la hora de algún
recordatorio y, si es así, te avisa con una notificación de macOS.
Esto es lo que hace a Jarvis PROACTIVO."""

import subprocess
import time

import ollama

from recordatorios import marcar_avisado, vencidos

MODELO = "qwen2.5:3b"
CADA_SEGUNDOS = 30


def redactar_aviso(texto):
    """Le pedimos al LLM que convierta el recordatorio en un aviso breve y amable."""
    try:
        respuesta = ollama.chat(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres Jarvis, asistente de Nicolás. Escribe UN aviso breve (máximo 15 palabras), en español, cercano y en segunda persona. Sin emojis."},
                {"role": "user", "content": f"Avísale de este recordatorio: {texto}"},
            ],
            options={"temperature": 0.7},
        )
        return respuesta.message.content.strip()
    except Exception:
        return texto  # si el modelo falla, avisamos con el texto original


def notificar(mensaje):
    """Muestra una notificación de macOS (como las de WhatsApp o el calendario)."""
    subprocess.run([
        "osascript",
        "-e", "on run argv",
        "-e", 'display notification (item 1 of argv) with title "🤖 Jarvis"',
        "-e", "end run",
        mensaje,
    ])


print(f"👀 Vigilante activo: reviso tus recordatorios cada {CADA_SEGUNDOS} segundos. (Ctrl+C para detenerlo)")
try:
    while True:
        for recordatorio in vencidos():
            aviso = redactar_aviso(recordatorio["texto"])
            notificar(aviso)
            print(f"  🔔 {recordatorio['cuando']}  {aviso}")
            marcar_avisado(recordatorio)
        time.sleep(CADA_SEGUNDOS)
except KeyboardInterrupt:
    print("\n👋 Vigilante detenido.")
