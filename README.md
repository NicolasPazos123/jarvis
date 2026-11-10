# Jarvis 🤖

Asistente personal de IA que estoy construyendo desde cero para aprender AI Engineering.
Corre 100% local en mi Mac (M1, 8 GB) con modelos open source, sin costo.

## Estado actual: v2 – Memoria a largo plazo

- [x] Chat en la terminal con un LLM local (`qwen2.5:3b` vía Ollama)
- [x] Memoria de la conversación (historial de mensajes)
- [x] Personalidad y reglas definidas con un *system prompt*
- [x] Respuestas en *streaming* (se muestran mientras se generan)
- [x] Temperatura configurable + experimento comparativo (`experimento_temperatura.py`)
- [x] *Tool calling*: herramientas para ver la fecha/hora, crear notas y leer notas (`herramientas.py`)
- [x] *Agent loop*: el modelo encadena varias herramientas (pensar → actuar → observar) con un freno de seguridad de 5 pasos
- [x] Archivos con *sandbox* (`espacio_jarvis/`) y confirmación humana antes de escribir (*human-in-the-loop*)
- [x] Memoria a largo plazo con **RAG**: recuerdos guardados con embeddings (`bge-m3`) en `memoria.json` y búsqueda semántica antes de cada respuesta (`memoria.py`)

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

- **Sandbox y human-in-the-loop:** el agente solo puede tocar archivos dentro de una carpeta (lo garantiza el código, no el prompt) y las acciones que cambian algo requieren mi confirmación.
- **Embeddings:** un vector que representa el significado de un texto. Su dimensión depende del modelo (`bge-m3` = 1024), no del largo del texto. `nomic-embed-text` falló en español; `bge-m3` (multilingüe) funcionó.
- **Similitud coseno y top-k:** comparar el vector de la consulta con el de cada documento y quedarse con los k más parecidos.
- **RAG (Retrieval-Augmented Generation):** buscar los recuerdos relevantes, agregarlos al mensaje y que el LLM responda con ellos. El modelo no memoriza nada: mi código le pone la información correcta en el contexto.
- **Calibrar el umbral con datos:** empecé con 0.55 a ojo y bloqueaba todo. Midiendo puntajes reales lo bajé a 0.45. Hay un trade-off entre falsos negativos y falsos positivos; en RAG suele ser peor perder un recuerdo relevante.

## Roadmap

- [x] v0 – Cerebro: chat con memoria y personalidad
- [ ] v1 – Manos: *tool calling* y *agent loop* (que pueda ejecutar acciones)
- [x] v2 – Memoria a largo plazo: embeddings y RAG
- [ ] v3 – Voz: hablarle y que responda hablando
- [ ] v4 – Iniciativa: que actúe por su cuenta
- [ ] v5 – Evals y seguridad
