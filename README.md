# aerotwin-ai

**Tarea 7 – Master Evolve**

Gemelo digital (digital twin) del ecosistema aeronáutico español construido con datos abiertos de AENA y ENAIRE e IA generativa (RAG + LLM).

---

## Estructura del proyecto

```
aerotwin-ai/
│
├── data/
│   ├── raw/
│   │   ├── aena_passengers/    # Estadísticas de pasajeros AENA
│   │   ├── aena_airlines/      # Directorio de aerolíneas AENA
│   │   ├── aena_airports/      # Metadatos de aeropuertos AENA
│   │   └── enaire_aip/         # Documentos AIP de ENAIRE
│   │
│   └── processed/              # Datos procesados y índice FAISS
│
├── notebooks/
│   └── 01_aerotwin_ai.ipynb    # Notebook principal (EDA + RAG)
│
├── src/
│   └── loaders.py              # Utilidades de carga de datos
│
├── outputs/
│   └── demo_questions.md       # Preguntas de demostración para el asistente
│
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/mg15best/aerotwin-ai.git
cd aerotwin-ai

# 2. Crear y activar un entorno virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y añadir tu OPENAI_API_KEY
```

## Datos

Coloca los ficheros CSV descargados del portal de estadísticas de AENA en los directorios correspondientes dentro de `data/raw/` y los documentos AIP de ENAIRE en `data/raw/enaire_aip/`.

- AENA estadísticas: https://estadisticas.aena.es/
- ENAIRE AIP: https://aip.enaire.es/

## Uso

Abre el notebook principal con Jupyter:

```bash
jupyter notebook notebooks/01_aerotwin_ai.ipynb
```

Sigue las instrucciones dentro del notebook para ejecutar el análisis exploratorio y el pipeline RAG.
