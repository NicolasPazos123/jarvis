"""Memoria a largo plazo de Jarvis: guarda recuerdos con su embedding
y los busca por SIGNIFICADO (búsqueda semántica)."""

import json
import math
from datetime import datetime
from pathlib import Path

import ollama

MODELO_EMBEDDINGS = "bge-m3"          # multilingüe: entiende bien el español
ARCHIVO_MEMORIA = Path(__file__).parent / "memoria.json"
TOP_K = 3                             # cuántos recuerdos traer como máximo
UMBRAL = 0.45                         # calibrado con pruebas reales: deja pasar lo relevante, bloquea lo que no tiene relación


def _cargar():
    if not ARCHIVO_MEMORIA.exists():
        return []
    return json.loads(ARCHIVO_MEMORIA.read_text(encoding="utf-8"))


def _guardar(recuerdos):
    ARCHIVO_MEMORIA.write_text(json.dumps(recuerdos, ensure_ascii=False), encoding="utf-8")


def embedding(texto):
    """Texto -> vector de 1024 números."""
    return ollama.embed(model=MODELO_EMBEDDINGS, input=texto)["embeddings"][0]


def similitud_coseno(a, b):
    """Dos vectores -> un número entre 0 y 1 (qué tan parecidos son)."""
    producto = sum(x * y for x, y in zip(a, b))
    largo_a = math.sqrt(sum(x * x for x in a))
    largo_b = math.sqrt(sum(y * y for y in b))
    return producto / (largo_a * largo_b)


# ---------- FASE 1: indexar (guardar el recuerdo con su vector) ----------

def guardar_recuerdo(texto):
    recuerdos = _cargar()
    recuerdos.append({
        "texto": texto,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "vector": embedding(texto),
    })
    _guardar(recuerdos)
    return f"Recuerdo guardado: {texto}"


# ---------- FASE 2: buscar (consulta -> top-k recuerdos que pasen el umbral) ----------

def buscar_recuerdos(consulta, k=TOP_K, umbral=UMBRAL):
    recuerdos = _cargar()
    if not recuerdos:
        return []
    v_consulta = embedding(consulta)
    puntajes = [(similitud_coseno(v_consulta, r["vector"]), r) for r in recuerdos]
    puntajes.sort(key=lambda par: par[0], reverse=True)
    return [(p, r) for p, r in puntajes[:k] if p >= umbral]
