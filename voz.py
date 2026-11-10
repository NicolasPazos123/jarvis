"""La voz de Jarvis: convierte texto en audio (Text-to-Speech, TTS).
Usa el comando 'say' que ya viene incluido en macOS: gratis y sin instalar nada."""

import re
import shutil
import subprocess

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
