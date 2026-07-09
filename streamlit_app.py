from pathlib import Path
import os
import re
import tempfile
import shutil
from typing import List, Dict, Tuple

import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="AeroTwin AI",
    page_icon="✈️",
    layout="wide"
)

REPO_ROOT = Path(__file__).parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
DEMO_RESPONSES_PATH = OUTPUTS_DIR / "demo_responses.md"
RAW_DATA_DIR = REPO_ROOT / "data" / "raw"

APP_TITLE = "AeroTwin AI"
APP_SUBTITLE = "Asistente experto RAG para aeropuertos de Aena"


# ============================================================
# UTILIDADES DE CONFIGURACIÓN
# ============================================================

def get_secret(name: str, default=None):
    """
    Reads a secret from Streamlit secrets or environment variables.
    This avoids writing API keys directly in the code.
    """
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    return os.getenv(name, default)


def has_google_api_key() -> bool:
    """
    Checks whether a Google API key is available.
    """
    api_key = get_secret("GOOGLE_API_KEY")
    return bool(api_key and str(api_key).strip())


# ============================================================
# MODO DEMO SIN API
# ============================================================

def read_demo_responses() -> str:
    """
    Reads the markdown file with pre-generated demo responses.
    This mode does not require Gemini API quota.
    """
    if not DEMO_RESPONSES_PATH.exists():
        return (
            "No se ha encontrado `outputs/demo_responses.md`.\n\n"
            "Ejecuta primero el notebook y genera las respuestas de demostración."
        )

    return DEMO_RESPONSES_PATH.read_text(encoding="utf-8")


def split_demo_responses(markdown_text: str) -> Dict[str, str]:
    """
    Splits demo_responses.md into sections by question.
    """
    sections = {}

    parts = re.split(r"\n## ", markdown_text)

    for part in parts:
        clean_part = part.strip()

        if not clean_part:
            continue

        if clean_part.startswith("# Respuestas"):
            sections["Introducción"] = clean_part
        else:
            title_line = clean_part.splitlines()[0].strip()
            title = title_line.replace("#", "").strip()
            sections[title] = "## " + clean_part

    return sections


# ============================================================
# MODO LIVE CON GEMINI + RAG
# ============================================================

SYSTEM_PROMPT = """
Eres AeroTwin AI, un asistente experto en aeropuertos de Aena construido para un proyecto académico de Inteligencia Artificial Generativa.

Tu función es responder preguntas utilizando una base de conocimiento oficial compuesta por documentos de Aena y ENAIRE/AIP.

Tienes dos modos principales de respuesta:

1. Passenger Voice:
   - Para pasajeros y usuarios generales del aeropuerto.
   - Usa un lenguaje claro, directo y útil.
   - Prioriza orientación práctica, pasos concretos y explicaciones sencillas.
   - Evita tecnicismos innecesarios.

2. Travel Industry Voice:
   - Para aerolíneas, agencias de viaje, turoperadores, equipos de desarrollo de rutas y profesionales turísticos.
   - Usa un tono profesional y analítico.
   - Prioriza información sobre rutas, incentivos, conectividad, operación, mercado y oportunidades de negocio.
   - Puede utilizar lenguaje sectorial, pero siempre de forma comprensible.

Reglas de respuesta:
- Responde únicamente con la información disponible en el contexto recuperado.
- Si el contexto no contiene información suficiente, dilo claramente.
- No inventes horarios, rutas, tarifas, procedimientos, normativa o datos operativos.
- No proporciones información de vuelos en tiempo real ni alertas operativas en directo.
- Si una pregunta requiere datos en tiempo real, explica que el MVP no dispone de esa información.
- Cuando sea útil, diferencia entre información para pasajeros e información para profesionales.
- Mantén la coherencia con la conversación previa.
- Responde en el mismo idioma de la pregunta del usuario, salvo que se solicite otro idioma.
- Al final de la respuesta, incluye una breve sección "Fuentes consultadas" con los nombres de los documentos recuperados.
"""


def infer_audience_from_path(path: Path) -> str:
    """
    Infers the main audience of a document from its folder.
    """
    path_parts = set(path.parts)

    if "aena_passengers" in path_parts:
        return "passenger"

    if "aena_airlines" in path_parts:
        return "travel_industry"

    if "enaire_aip" in path_parts:
        return "aviation_professional"

    return "general"


def infer_document_group(path: Path) -> str:
    """
    Infers a readable document group from the path.
    """
    path_parts = set(path.parts)

    if "aena_passengers" in path_parts:
        return "Aena passenger information"

    if "aena_airlines" in path_parts:
        return "Aena airline and route-development information"

    if "enaire_aip" in path_parts:
        return "ENAIRE/AIP aeronautical information"

    return "General documentation"


def load_html_text(path: Path) -> str:
    """
    Loads text from an HTML file.
    """
    from bs4 import BeautifulSoup

    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    return "\n".join(lines)


@st.cache_resource(show_spinner=False)
def build_live_agent():
    """
    Builds the live RAG components.

    This consumes Gemini Embeddings quota when ChromaDB is created.
    Therefore, it is only called in live mode.
    """
    if not has_google_api_key():
        raise ValueError("No hay GOOGLE_API_KEY configurada.")

    api_key = get_secret("GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = str(api_key)

    gemini_model = get_secret("GEMINI_MODEL", "gemini-2.5-flash")
    embedding_model = get_secret("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2-preview")
    embedding_dimensions = int(get_secret("GEMINI_EMBEDDING_DIMENSIONS", 768))

    from langchain_core.documents import Document
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma

    documents = []

    supported_extensions = [".pdf", ".html", ".htm"]
    excluded_folders = ["support_optional"]

    for path in sorted(RAW_DATA_DIR.rglob("*")):
        if not path.is_file():
            continue

        if path.name == ".gitkeep":
            continue

        if any(excluded in path.parts for excluded in excluded_folders):
            continue

        if path.suffix.lower() not in supported_extensions:
            continue

        metadata = {
            "source": str(path),
            "source_file": path.name,
            "source_folder": path.parent.name,
            "document_group": infer_document_group(path),
            "file_type": path.suffix.lower().replace(".", ""),
            "audience": infer_audience_from_path(path),
        }

        if path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(path))
            loaded_docs = loader.load()

            for doc in loaded_docs:
                doc.metadata.update(metadata)
                documents.append(doc)

        else:
            text = load_html_text(path)
            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata
                )
            )

    if not documents:
        raise ValueError("No se han encontrado documentos en data/raw/.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    # Modo demo para Streamlit: pocos chunks por documento para no consumir demasiada cuota.
    max_chunks_per_file = 3
    chunks_by_file = {}

    for chunk in chunks:
        source_file = chunk.metadata.get("source_file", "unknown")
        chunks_by_file.setdefault(source_file, []).append(chunk)

    chunks_for_index = []

    for source_file, file_chunks in sorted(chunks_by_file.items()):
        chunks_for_index.extend(file_chunks[:max_chunks_per_file])

    embeddings = GoogleGenerativeAIEmbeddings(
        model=embedding_model,
        output_dimensionality=embedding_dimensions
    )

    # Directorio temporal para evitar escribir ChromaDB en el repo.
    temp_dir = tempfile.mkdtemp(prefix="aerotwin_chroma_")

    vectorstore = Chroma.from_documents(
        documents=chunks_for_index,
        embedding=embeddings,
        persist_directory=temp_dir,
        collection_name="aerotwin_ai_streamlit"
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    llm = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=0
    )

    return {
        "llm": llm,
        "retriever": retriever,
        "documents_count": len(documents),
        "chunks_count": len(chunks),
        "indexed_chunks_count": len(chunks_for_index),
        "temp_dir": temp_dir,
    }


def build_retrieval_query(question: str, audience: str = "auto", airport: str = "general") -> str:
    """
    Builds an enriched query for retrieval.
    """
    airport_aliases = {
        "tenerife sur": "Tenerife Sur TFS GCTS Reina Sofía",
        "tenerife norte": "Tenerife Norte TFN GCXO Los Rodeos",
        "madrid-barajas": "Madrid-Barajas MAD LEMD Adolfo Suárez Madrid Barajas",
        "madrid": "Madrid-Barajas MAD LEMD Adolfo Suárez Madrid Barajas",
        "barcelona": "Barcelona-El Prat BCN LEBL Josep Tarradellas",
        "barcelona-el prat": "Barcelona-El Prat BCN LEBL Josep Tarradellas",
        "aena network": "Aena network airports airlines passengers Spain",
        "general": "Aena network airports airlines passengers ENAIRE AIP Spain",
    }

    normalized_airport = airport.lower().strip()
    airport_context = airport_aliases.get(normalized_airport, airport)

    audience_context = {
        "passenger": "passenger traveller airport services documentation luggage assistance PRM information points",
        "travel_industry": "airlines route development incentives marketing support airport business tourism professionals connectivity",
        "aviation_professional": "ENAIRE AIP aeronautical operational airport data ICAO procedures",
        "auto": "passengers airlines route development airport information",
    }.get(audience, audience)

    retrieval_query = f"""
User question:
{question}

Target audience:
{audience}
{audience_context}

Airport or scope:
{airport}
{airport_context}
"""

    return retrieval_query.strip()


def format_context(retrieved_docs) -> Tuple[str, List[str]]:
    """
    Formats retrieved documents for the LLM.
    """
    context_blocks = []
    sources = []

    for i, doc in enumerate(retrieved_docs, start=1):
        source_file = doc.metadata.get("source_file", "unknown")
        audience = doc.metadata.get("audience", "unknown")
        document_group = doc.metadata.get("document_group", "unknown")

        sources.append(source_file)

        block = f"""
[Documento {i}]
Fuente: {source_file}
Audiencia: {audience}
Grupo documental: {document_group}

Contenido:
{doc.page_content}
"""
        context_blocks.append(block.strip())

    unique_sources = sorted(set(sources))

    return "\n\n---\n\n".join(context_blocks), unique_sources


def answer_live(question: str, audience: str, airport: str) -> Dict:
    """
    Generates a live answer using Gemini + RAG.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    agent = build_live_agent()

    retrieval_query = build_retrieval_query(
        question=question,
        audience=audience,
        airport=airport
    )

    retrieved_docs = agent["retriever"].invoke(retrieval_query)
    context, sources = format_context(retrieved_docs)

    system_message = f"""
{SYSTEM_PROMPT}

Modo de respuesta solicitado: {audience}
Aeropuerto o ámbito indicado: {airport}

Contexto recuperado desde la base vectorial:
{context}

Fuentes recuperadas:
{", ".join(sources)}
"""

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=question)
    ]

    response = agent["llm"].invoke(messages)

    return {
        "answer": response.content,
        "sources": sources,
        "documents_count": agent["documents_count"],
        "chunks_count": agent["chunks_count"],
        "indexed_chunks_count": agent["indexed_chunks_count"],
    }


# ============================================================
# INTERFAZ STREAMLIT
# ============================================================

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

st.markdown(
    """
AeroTwin AI es un MVP académico de Inteligencia Artificial Generativa que responde preguntas sobre aeropuertos de Aena usando documentos de Aena y ENAIRE/AIP.

La app incluye dos modos:

- **Demo sin API:** muestra respuestas ya generadas en el notebook.
- **Live con Gemini:** usa RAG + Gemini en tiempo real cuando hay API key y cuota disponible.
"""
)

with st.sidebar:
    st.header("Configuración")

    app_mode = st.radio(
        "Modo de uso",
        [
            "Demo sin API",
            "Live con Gemini"
        ],
        index=0
    )

    audience = st.selectbox(
        "Audiencia",
        [
            "passenger",
            "travel_industry",
            "aviation_professional",
            "auto"
        ],
        index=0
    )

    airport = st.selectbox(
        "Aeropuerto o ámbito",
        [
            "general",
            "Aena network",
            "Tenerife Sur",
            "Tenerife Norte",
            "Madrid-Barajas",
            "Barcelona-El Prat"
        ],
        index=0
    )

    st.divider()

    st.subheader("Estado de API")

    if has_google_api_key():
        st.success("API key detectada")
    else:
        st.warning("API key no configurada")

    st.caption(
        "El modo demo no consume API. El modo live puede consumir cuota de Gemini."
    )


# ============================================================
# MODO DEMO
# ============================================================

if app_mode == "Demo sin API":
    st.header("Modo demo sin API")

    st.info(
        "Este modo no llama a Gemini. Muestra respuestas previamente generadas "
        "y guardadas en outputs/demo_responses.md."
    )

    demo_text = read_demo_responses()
    sections = split_demo_responses(demo_text)

    section_titles = list(sections.keys())

    selected_section = st.selectbox(
        "Selecciona una respuesta de demostración",
        section_titles
    )

    st.markdown(sections[selected_section])


# ============================================================
# MODO LIVE
# ============================================================

else:
    st.header("Modo live con Gemini")

    st.warning(
        "Este modo necesita una API key válida y cuota disponible de Gemini. "
        "Si has agotado la cuota gratuita, usa el modo demo hasta que se reinicie o configures otra clave."
    )

    question = st.text_area(
        "Escribe tu pregunta",
        placeholder="Ejemplo: ¿Cómo puede solicitar asistencia una persona con movilidad reducida en un aeropuerto de Aena?",
        height=120
    )

    ask_button = st.button("Preguntar a AeroTwin AI")

    if ask_button:
        if not question.strip():
            st.error("Escribe una pregunta antes de continuar.")

        elif not has_google_api_key():
            st.error(
                "No hay GOOGLE_API_KEY configurada. "
                "Configura la clave en .streamlit/secrets.toml o en Streamlit Cloud secrets."
            )

        else:
            with st.spinner("Construyendo RAG y consultando Gemini..."):
                try:
                    result = answer_live(
                        question=question,
                        audience=audience,
                        airport=airport
                    )

                    st.subheader("Respuesta")
                    st.markdown(result["answer"])

                    st.subheader("Fuentes recuperadas")
                    for source in result["sources"]:
                        st.write(f"- {source}")

                    with st.expander("Detalles técnicos"):
                        st.write("Documentos cargados:", result["documents_count"])
                        st.write("Chunks generados:", result["chunks_count"])
                        st.write("Chunks indexados en modo demo:", result["indexed_chunks_count"])

                except Exception as error:
                    st.error("No se ha podido generar la respuesta live.")
                    st.write("Detalle del error:")
                    st.code(str(error))
                    st.info(
                        "Puedes seguir usando el modo demo sin API. "
                        "Cuando vuelva la cuota de Gemini, prueba de nuevo el modo live."
                    )


# ============================================================
# PIE DE APP
# ============================================================

st.divider()

st.caption(
    "MVP académico. No proporciona información de vuelos en tiempo real, "
    "alertas operativas ni asesoramiento legal o aeronáutico."
)

