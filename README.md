# Jarvis 🤖

Asistente personal de IA que estoy construyendo desde cero para aprender AI Engineering.
Corre 100% local en mi Mac (M1, 8 GB) con modelos open source, sin costo.

## Estado actual: v1 – Las manos (en progreso)

- [x] Chat en la terminal con un LLM local (`qwen2.5:3b` vía Ollama)
- [x] Memoria de la conversación (historial de mensajes)
- [x] Personalidad y reglas definidas con un *system prompt*
- [x] Respuestas en *streaming* (se muestran mientras se generan)
- [x] Temperatura configurable + experimento comparativo (`experimento_temperatura.py`)
- [x] *Tool calling*: herramientas para ver la fecha/hora, crear notas y leer notas (`herramientas.py`)
- [x] *Agent loop*: el modelo encadena varias herramientas (pensar → actuar → observar) con un freno de seguridad de 5 pasos

## Cómo correrlo

1. Instala [Ollama](https://ollama.com) y descarga el modelo:
   ```bash
   ollama pull qwen2.5:3b
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
- **Streaming:** recibir la respuesta en pedazos (*chunks*) a medida que se genera cada token. Tarda lo mismo, pero se siente más rápida.
- **Temperatura:** controla qué tan arriesgado es el modelo al elegir el siguiente token. Con 0 siempre elige el más probable (en mi experimento repitió el mismo nombre 3 veces); con 1.5 dio 3 nombres distintos. Baja = precisión, alta = creatividad.
- **Tool calling:** el modelo no ejecuta nada; solo *pide* usar una herramienta. Mi programa la ejecuta y le devuelve el resultado (rol `tool`). El modelo nunca ve el código, solo un "menú" en JSON Schema con nombre, descripción y parámetros.
- **Elegir el modelo importa:** con el mismo código, `llama3.2:3b` usaba herramientas hasta para contar chistes; `qwen2.5:3b` lo hizo mucho mejor.
- **Agent loop:** ciclo de pensar → actuar → observar que se repite hasta que el modelo ya no pide herramientas. Necesita un límite de pasos para evitar ciclos infinitos.
- **Parallel tool calling y dependencias:** el modelo pedía varias herramientas a la vez aunque una dependiera de otra, y rellenaba datos con texto genérico. Lo resolví ejecutando una herramienta por vuelta y recordándole las pendientes en la observación.
- **Las instrucciones sugieren, el código obliga:** las reglas críticas no pueden depender solo del prompt.
- **Diseño de herramientas:** `crear_nota` agrega la fecha y hora automáticamente, así el dato es correcto aunque el modelo no lo incluya.

## Roadmap

- [x] v0 – Cerebro: chat con memoria y personalidad
- [ ] v1 – Manos: *tool calling* y *agent loop* (que pueda ejecutar acciones)
- [ ] v2 – Memoria a largo plazo: embeddings y RAG
- [ ] v3 – Voz: hablarle y que responda hablando
- [ ] v4 – Iniciativa: que actúe por su cuenta
- [ ] v5 – Evals y seguridad
