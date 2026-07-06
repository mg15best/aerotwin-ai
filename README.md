# AeroTwin AI

**Tarea 7 – Máster Big Data e Inteligencia Artificial**

AeroTwin AI es un asistente de Inteligencia Artificial Generativa especializado en aeropuertos de Aena. Utiliza Retrieval-Augmented Generation, RAG, para responder preguntas a partir de una base de conocimiento oficial construida con documentos de Aena y ENAIRE/AIP.

El asistente está diseñado con dos modos de respuesta:

- **Passenger Voice**: para pasajeros y usuarios generales del aeropuerto.
- **Travel Industry Voice**: para aerolíneas, agencias de viaje, turoperadores, equipos de desarrollo de rutas y profesionales del sector turístico.

---

## Objetivo del proyecto

El objetivo de este MVP académico es construir un asistente experto capaz de responder preguntas sobre el ecosistema aeroportuario español usando una base de conocimiento vectorial.

El proyecto combina:

- Google Gemini como modelo de lenguaje.
- Gemini Embeddings para vectorizar documentos.
- ChromaDB como base de datos vectorial.
- LangChain y LangGraph para construir el agente RAG.
- Memoria básica de conversación.
- Interacción mediante Jupyter Notebook o Google Colab.

---

## Estructura del proyecto

```text
aerotwin-ai/
│
├── data/
│   ├── raw/
│   │   ├── aena_passengers/     # Información oficial de Aena para pasajeros
│   │   ├── aena_airlines/       # Información oficial de Aena para aerolíneas y rutas
│   │   ├── enaire_aip/          # Información aeronáutica oficial de ENAIRE/AIP
│   │   └── support_optional/    # Documentos opcionales de apoyo
│   │
│   └── processed/               # Archivos procesados generados, no se suben al repositorio
│
├── notebooks/
│   └── 01_aerotwin_ai.ipynb     # Notebook principal
│
├── outputs/
│   └── demo_questions.md        # Preguntas de demostración y ejemplos documentados
│
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Base de conocimiento

Los documentos fuente se almacenan en:

```text
data/raw/
```

La base de conocimiento incluye documentos oficiales de:

- Información de Aena para pasajeros.
- Información de Aena para aerolíneas y desarrollo de rutas.
- Información aeronáutica de ENAIRE/AIP.

La carpeta `support_optional/` contiene documentos adicionales que pueden servir como contexto, pero no necesariamente se indexan en el pipeline RAG principal.

---

## Tecnologías utilizadas

- Google Gemini
- Gemini Embeddings
- ChromaDB
- LangChain
- LangGraph
- Jupyter Notebook / Google Colab
- Python

---

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/mg15best/aerotwin-ai.git
cd aerotwin-ai
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Crear un archivo `.env` a partir del archivo de ejemplo:

```bash
cp .env.example .env
```

Después, editar `.env` y añadir la clave real de Google Gemini:

```text
GOOGLE_API_KEY=tu_clave_real_de_google_gemini
```

El archivo `.env` nunca debe subirse a GitHub.

---

## Uso

Abrir el notebook principal:

```bash
jupyter notebook notebooks/01_aerotwin_ai.ipynb
```

También se puede ejecutar el proyecto desde Google Colab clonando el repositorio de GitHub y ejecutando el notebook paso a paso.

---

## Base de datos vectorial

La base de datos vectorial de ChromaDB no se incluye en el repositorio porque se genera automáticamente al ejecutar el notebook.

El notebook realizará los siguientes pasos:

1. Cargar los documentos desde `data/raw/`.
2. Limpiar y dividir los documentos en fragmentos.
3. Generar embeddings con Gemini Embeddings.
4. Guardar los vectores en ChromaDB.
5. Ejecutar el agente RAG con LangGraph y Gemini.
6. Demostrar memoria de conversación.
7. Incluir al menos cinco preguntas de ejemplo documentadas.

---

## System prompt

El asistente utiliza un system prompt personalizado diseñado para:

- Adaptar la respuesta al tipo de usuario.
- Responder en modo Passenger Voice o Travel Industry Voice.
- Utilizar únicamente el contexto oficial recuperado.
- Evitar inventar información cuando los documentos no aportan evidencia suficiente.
- Mantener respuestas claras, útiles y fundamentadas en las fuentes.
- Conservar coherencia entre turnos de conversación.

---

## Alcance académico

Este proyecto es un MVP académico. No proporciona información de vuelos en tiempo real, alertas operativas en directo ni asesoramiento legal o aeronáutico. Cuando una respuesta requiera datos en tiempo real o información fuera de los documentos indexados, el asistente debe indicar claramente que esa información no está disponible en la base de conocimiento actual.
