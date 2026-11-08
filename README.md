# Jarvis 🤖

Asistente personal de IA que estoy construyendo desde cero para aprender AI Engineering.
Corre 100% local en mi Mac (M1, 8 GB) con modelos open source, sin costo.

## Estado actual: v0 – El cerebro

- [x] Chat en la terminal con un LLM local (`llama3.2:3b` vía Ollama)
- [x] Memoria de la conversación (historial de mensajes)
- [x] Personalidad y reglas definidas con un *system prompt*

## Cómo correrlo

1. Instala [Ollama](https://ollama.com) y descarga el modelo:
   ```bash
   ollama pull llama3.2:3b
   ```
2. Crea el entorno e instala dependencias:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install ollama
   ```
3. Ejecuta:
   ```bash
   python3 jarvis.py
   ```
   Escribe `salir` para terminar.

## Lo que aprendí

- **LLM:** un modelo que predice el siguiente *token* (pedazo de texto) una y otra vez. Es como un autocompletado gigante.
- **Ollama:** el programa que descarga y ejecuta modelos en mi computadora. No es el modelo en sí.
- **El modelo no tiene memoria (*stateless*):** para que "recuerde", mi programa guarda el historial de mensajes y se lo envía completo en cada turno.
- **Ventana de contexto:** el límite de texto que el modelo puede leer de una vez. Mientras más larga la conversación, más se acerca a ese límite.
- **System prompt:** instrucciones de fondo que definen quién es el asistente y cómo responde.
- **Alucinación:** cuando el modelo inventa información con seguridad. Un buen system prompt la reduce, pero no la elimina.

## Roadmap

- [x] v0 – Cerebro: chat con memoria y personalidad
- [ ] v1 – Manos: *tool calling* y *agent loop* (que pueda ejecutar acciones)
- [ ] v2 – Memoria a largo plazo: embeddings y RAG
- [ ] v3 – Voz: hablarle y que responda hablando
- [ ] v4 – Iniciativa: que actúe por su cuenta
- [ ] v5 – Evals y seguridad
