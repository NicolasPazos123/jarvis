"""Recordatorios de Jarvis: se guardan con fecha y hora en recordatorios.json.
Jarvis los CREA cuando se lo pides; el vigilante los REVISA y te avisa solo."""

import json
from datetime import datetime, timedelta
from pathlib import Path

ARCHIVO = Path(__file__).parent / "recordatorios.json"
FORMATO = "%Y-%m-%d %H:%M"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _proximo_dia(dia_semana, hora):
    """Calcula la fecha exacta del próximo 'viernes a las 18:00', por ejemplo.
    Este cálculo lo hace el CÓDIGO, porque al modelo pequeño le sale mal."""
    dia = dia_semana.strip().lower().replace("miercoles", "miércoles").replace("sabado", "sábado")
    if dia not in DIAS:
        raise ValueError(f"Día no válido: {dia_semana}")
    h, m = (int(x) for x in hora.split(":"))
    ahora = datetime.now()
    dias_hasta = (DIAS.index(dia) - ahora.weekday()) % 7
    cuando = (ahora + timedelta(days=dias_hasta)).replace(hour=h, minute=m, second=0, microsecond=0)
    if cuando <= ahora:  # si es hoy pero la hora ya pasó, es la próxima semana
        cuando += timedelta(days=7)
    return cuando


def _cargar():
    if not ARCHIVO.exists():
        return []
    return json.loads(ARCHIVO.read_text(encoding="utf-8"))


def _guardar(lista):
    ARCHIVO.write_text(json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8")


def crear_recordatorio(texto, en_minutos=None, dia_semana=None, hora=None, fecha_hora=None):
    """Crea un recordatorio. El modelo puede indicar la hora de dos formas:
    - en_minutos: "dentro de X minutos" (más fácil para el modelo, el cálculo lo hace el código)
    - fecha_hora: una fecha exacta en formato AAAA-MM-DD HH:MM"""
    if en_minutos is not None:
        cuando = datetime.now() + timedelta(minutes=int(en_minutos))
    elif dia_semana and hora:
        cuando = _proximo_dia(dia_semana, hora)
    elif fecha_hora:
        cuando = datetime.strptime(fecha_hora, FORMATO)
    else:
        return "Error: indica en_minutos o fecha_hora."

    if cuando < datetime.now() - timedelta(minutes=1):
        return f"Error: la hora {cuando:%d/%m/%Y %H:%M} ya pasó."

    lista = _cargar()
    lista.append({"texto": texto, "cuando": cuando.strftime(FORMATO), "avisado": False})
    _guardar(lista)
    # Devolvemos también el DÍA de la semana: así cualquier error queda a la vista
    return f"Recordatorio creado para el {DIAS[cuando.weekday()]} {cuando:%d/%m/%Y a las %H:%M}: {texto}"


def vencidos():
    """Devuelve los recordatorios cuya hora ya llegó y todavía no se avisaron."""
    ahora = datetime.now()
    return [r for r in _cargar() if not r["avisado"] and datetime.strptime(r["cuando"], FORMATO) <= ahora]


def marcar_avisado(recordatorio):
    lista = _cargar()
    for r in lista:
        if r["texto"] == recordatorio["texto"] and r["cuando"] == recordatorio["cuando"]:
            r["avisado"] = True
    _guardar(lista)
