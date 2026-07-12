from pathlib import Path
import os
import re
import tempfile
import textwrap
from typing import List, Dict, Tuple

import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="AeroTwin AI | Airport Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

REPO_ROOT = Path(__file__).parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
DEMO_RESPONSES_PATH = OUTPUTS_DIR / "demo_responses.md"
RAW_DATA_DIR = REPO_ROOT / "data" / "raw"

APP_TITLE = "AeroTwin AI"
APP_SUBTITLE = "Asistente experto RAG para aeropuertos de Aena"

AUDIENCE_LABELS = {
    "passenger": "Pasajeros",
    "travel_industry": "Industria turística y aerolíneas",
    "aviation_professional": "Profesionales de aviación",
    "auto": "Detección automática",
}

AIRPORT_LABELS = {
    "general": "Consulta general",
    "Aena network": "Red de aeropuertos Aena",
    "Tenerife Sur": "Tenerife Sur · TFS",
    "Tenerife Norte": "Tenerife Norte · TFN",
    "Madrid-Barajas": "Madrid-Barajas · MAD",
    "Barcelona-El Prat": "Barcelona-El Prat · BCN",
}

MODE_LABELS = {
    "Demo sin API": "Demo sin API",
    "Live con Gemini": "Live con Gemini",
}


# ============================================================
# CAPA VISUAL
# ============================================================


def inject_custom_css() -> None:
    """Aplica una identidad visual aeroportuaria sin alterar la lógica de la app."""
    st.markdown(
        textwrap.dedent("""
        <style>
        :root {
            --at-bg: #050b14;
            --at-bg-soft: #091525;
            --at-panel: rgba(14, 29, 48, 0.86);
            --at-panel-solid: #0d1b2d;
            --at-border: rgba(134, 185, 222, 0.18);
            --at-text: #f4f8fc;
            --at-muted: #9fb1c4;
            --at-cyan: #43d7ff;
            --at-blue: #4f8cff;
            --at-red: #ef3f6b;
            --at-amber: #ffc768;
            --at-green: #44d7a8;
            --at-shadow: 0 24px 70px rgba(0, 0, 0, 0.28);
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            color: var(--at-text);
            background:
                radial-gradient(circle at 88% 4%, rgba(67, 215, 255, 0.10), transparent 24rem),
                radial-gradient(circle at 48% 90%, rgba(239, 63, 107, 0.08), transparent 30rem),
                linear-gradient(145deg, #050a12 0%, #08111e 52%, #050b14 100%);
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        .main .block-container {
            max-width: 1320px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(10, 23, 39, 0.98), rgba(6, 14, 25, 0.99));
            border-right: 1px solid var(--at-border);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.1rem;
        }

        section[data-testid="stSidebar"] hr {
            border-color: var(--at-border);
        }

        .sidebar-brand {
            position: relative;
            overflow: hidden;
            margin: 0 0 1.35rem 0;
            padding: 1.05rem;
            border: 1px solid var(--at-border);
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(24, 52, 82, 0.72), rgba(11, 25, 43, 0.92));
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.18);
        }

        .sidebar-brand::after {
            content: "";
            position: absolute;
            width: 130px;
            height: 130px;
            right: -70px;
            top: -70px;
            border-radius: 50%;
            border: 1px solid rgba(67, 215, 255, 0.28);
            box-shadow: 0 0 0 18px rgba(67, 215, 255, 0.03), 0 0 0 36px rgba(67, 215, 255, 0.025);
        }

        .sidebar-brand__icon {
            display: inline-grid;
            place-items: center;
            width: 42px;
            height: 42px;
            margin-bottom: 0.7rem;
            border-radius: 13px;
            background: linear-gradient(135deg, var(--at-red), #ff7e68);
            box-shadow: 0 10px 30px rgba(239, 63, 107, 0.25);
            font-size: 1.25rem;
        }

        .sidebar-brand__title {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        .sidebar-brand__subtitle {
            margin-top: 0.24rem;
            color: var(--at-muted);
            font-size: 0.77rem;
            line-height: 1.45;
        }

        .sidebar-section-label {
            margin: 1rem 0 0.45rem 0;
            color: #dce8f3;
            font-size: 0.73rem;
            font-weight: 800;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }

        .api-status {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin: 0.35rem 0 0.55rem 0;
            padding: 0.75rem 0.82rem;
            border: 1px solid var(--at-border);
            border-radius: 13px;
            background: rgba(255, 255, 255, 0.035);
            color: #e9f2f8;
            font-size: 0.84rem;
            font-weight: 650;
        }

        .api-status__dot {
            width: 9px;
            height: 9px;
            flex: 0 0 auto;
            border-radius: 50%;
            box-shadow: 0 0 0 5px rgba(255, 199, 104, 0.10);
            background: var(--at-amber);
        }

        .api-status--ready .api-status__dot {
            background: var(--at-green);
            box-shadow: 0 0 0 5px rgba(68, 215, 168, 0.10);
        }

        /* Hero */
        .hero-shell {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(330px, 0.65fr);
            gap: 2rem;
            align-items: stretch;
            margin-bottom: 1.5rem;
            padding: clamp(1.45rem, 3vw, 2.35rem);
            border: 1px solid var(--at-border);
            border-radius: 28px;
            background:
                linear-gradient(125deg, rgba(15, 35, 58, 0.95), rgba(7, 17, 30, 0.92)),
                radial-gradient(circle at 20% 20%, rgba(67, 215, 255, 0.16), transparent 25rem);
            box-shadow: var(--at-shadow);
        }

        .hero-shell::before {
            content: "";
            position: absolute;
            inset: auto -10% -52% 32%;
            height: 280px;
            border: 1px solid rgba(67, 215, 255, 0.18);
            border-radius: 50%;
            transform: rotate(-8deg);
            box-shadow: 0 0 0 34px rgba(67, 215, 255, 0.025), 0 0 0 68px rgba(67, 215, 255, 0.018);
            pointer-events: none;
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.48rem;
            margin-bottom: 1rem;
            padding: 0.42rem 0.72rem;
            border: 1px solid rgba(67, 215, 255, 0.24);
            border-radius: 999px;
            background: rgba(67, 215, 255, 0.07);
            color: #bcefff;
            font-size: 0.73rem;
            font-weight: 800;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }

        .hero-kicker__pulse {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--at-green);
            box-shadow: 0 0 0 5px rgba(68, 215, 168, 0.10);
        }

        .hero-title {
            margin: 0;
            color: var(--at-text);
            font-size: clamp(2.4rem, 5vw, 4.65rem);
            font-weight: 850;
            line-height: 0.98;
            letter-spacing: -0.055em;
        }

        .hero-title__accent {
            color: transparent;
            background: linear-gradient(90deg, #ffffff 0%, #b9edff 48%, #6bdcff 100%);
            -webkit-background-clip: text;
            background-clip: text;
        }

        .hero-description {
            max-width: 760px;
            margin: 1.1rem 0 1.3rem 0;
            color: #b6c5d4;
            font-size: clamp(0.98rem, 1.5vw, 1.12rem);
            line-height: 1.75;
        }

        .hero-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
        }

        .hero-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.48rem 0.7rem;
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 11px;
            background: rgba(255, 255, 255, 0.045);
            color: #d8e5ef;
            font-size: 0.78rem;
            font-weight: 650;
        }

        .airport-board {
            position: relative;
            z-index: 1;
            align-self: stretch;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(3, 9, 16, 0.84), rgba(8, 18, 31, 0.84));
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 18px 45px rgba(0, 0, 0, 0.22);
        }

        .board-header, .board-row {
            display: grid;
            grid-template-columns: 54px 1fr auto;
            gap: 0.7rem;
            align-items: center;
        }

        .board-header {
            padding: 0.25rem 0.4rem 0.7rem 0.4rem;
            color: #6f8499;
            font-size: 0.64rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .board-row {
            margin-top: 0.52rem;
            padding: 0.76rem 0.72rem;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.035);
        }

        .board-code {
            color: var(--at-amber);
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
            font-size: 0.95rem;
            font-weight: 800;
            letter-spacing: 0.08em;
        }

        .board-airport {
            overflow: hidden;
            color: #e7f0f7;
            font-size: 0.79rem;
            font-weight: 700;
            white-space: nowrap;
            text-overflow: ellipsis;
        }

        .board-status {
            padding: 0.25rem 0.45rem;
            border-radius: 7px;
            background: rgba(68, 215, 168, 0.10);
            color: #79e8c4;
            font-size: 0.62rem;
            font-weight: 850;
            letter-spacing: 0.08em;
        }

        /* Secciones y tarjetas */
        .section-heading {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin: 1.7rem 0 0.4rem 0;
        }

        .section-heading__icon {
            display: grid;
            place-items: center;
            width: 38px;
            height: 38px;
            border: 1px solid rgba(67, 215, 255, 0.18);
            border-radius: 12px;
            background: rgba(67, 215, 255, 0.07);
            font-size: 1rem;
        }

        .section-heading__eyebrow {
            color: var(--at-cyan);
            font-size: 0.69rem;
            font-weight: 850;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .section-heading__title {
            margin: 0.1rem 0 0 0;
            color: var(--at-text);
            font-size: clamp(1.45rem, 2.6vw, 2rem);
            font-weight: 800;
            letter-spacing: -0.035em;
        }

        .mode-banner {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 0.8rem;
            align-items: start;
            margin: 1rem 0 1.2rem 0;
            padding: 1rem 1.05rem;
            border: 1px solid rgba(67, 215, 255, 0.17);
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(67, 215, 255, 0.075), rgba(79, 140, 255, 0.045));
        }

        .mode-banner__icon {
            display: grid;
            place-items: center;
            width: 34px;
            height: 34px;
            border-radius: 10px;
            background: rgba(67, 215, 255, 0.10);
        }

        .mode-banner__title {
            margin: 0 0 0.18rem 0;
            color: #eaf7fd;
            font-size: 0.9rem;
            font-weight: 800;
        }

        .mode-banner__text {
            margin: 0;
            color: var(--at-muted);
            font-size: 0.84rem;
            line-height: 1.55;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--at-border) !important;
            border-radius: 20px !important;
            background: linear-gradient(145deg, rgba(14, 29, 48, 0.82), rgba(9, 20, 34, 0.80));
            box-shadow: 0 20px 55px rgba(0, 0, 0, 0.15);
        }

        /* Widgets */
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            border: 1px solid rgba(134, 185, 222, 0.18) !important;
            border-radius: 13px !important;
            background: rgba(3, 10, 18, 0.72) !important;
            color: var(--at-text) !important;
            box-shadow: none !important;
        }

        .stTextArea textarea:focus,
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="input"] > div:focus-within {
            border-color: rgba(67, 215, 255, 0.58) !important;
            box-shadow: 0 0 0 3px rgba(67, 215, 255, 0.08) !important;
        }

        label[data-testid="stWidgetLabel"] p {
            color: #dce7f0 !important;
            font-size: 0.84rem;
            font-weight: 700;
        }

        .stButton > button {
            min-height: 42px;
            border: 1px solid rgba(67, 215, 255, 0.20);
            border-radius: 12px;
            background: linear-gradient(135deg, #196f98, #3d67c9);
            color: #ffffff;
            font-weight: 750;
            box-shadow: 0 11px 30px rgba(30, 95, 168, 0.20);
            transition: transform 160ms ease, border-color 160ms ease, filter 160ms ease;
        }

        .stButton > button:hover {
            border-color: rgba(122, 231, 255, 0.70);
            color: #ffffff;
            filter: brightness(1.08);
            transform: translateY(-1px);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        section[data-testid="stSidebar"] .stButton > button {
            background: rgba(255, 255, 255, 0.045);
            box-shadow: none;
        }

        div[data-testid="stRadio"] label {
            padding: 0.28rem 0;
        }

        div[data-testid="stAlert"] {
            border: 1px solid var(--at-border);
            border-radius: 15px;
            background: rgba(13, 33, 53, 0.78);
        }

        details[data-testid="stExpander"] {
            border-color: var(--at-border) !important;
            border-radius: 14px !important;
            background: rgba(255, 255, 255, 0.025);
        }

        div[data-testid="stChatMessage"] {
            border: 1px solid var(--at-border);
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(14, 29, 48, 0.84), rgba(8, 19, 32, 0.84));
        }

        /* Markdown de respuestas */
        .main p, .main li {
            color: #c5d3df;
            line-height: 1.72;
        }

        .main h1, .main h2, .main h3, .main h4 {
            color: var(--at-text);
            letter-spacing: -0.025em;
        }

        .main a {
            color: var(--at-cyan);
        }

        .main code {
            color: #bfefff;
            background: rgba(67, 215, 255, 0.08);
            border: 1px solid rgba(67, 215, 255, 0.11);
            border-radius: 6px;
            padding: 0.12rem 0.3rem;
        }

        .main pre code {
            border: 0;
            background: transparent;
        }

        .footer-shell {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 0.8rem 1.5rem;
            align-items: center;
            margin-top: 2.4rem;
            padding: 1.05rem 0.1rem 0.2rem 0.1rem;
            border-top: 1px solid var(--at-border);
            color: #71869a;
            font-size: 0.73rem;
        }

        .footer-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.34rem 0.55rem;
            border: 1px solid rgba(255, 199, 104, 0.15);
            border-radius: 999px;
            color: #c9b485;
            background: rgba(255, 199, 104, 0.035);
        }

        @media (max-width: 980px) {
            .hero-shell {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 640px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero-shell {
                padding: 1.25rem;
                border-radius: 22px;
            }

            .airport-board {
                display: none;
            }
        }
        </style>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.markdown(
        textwrap.dedent("""
        <div class="sidebar-brand">
            <div class="sidebar-brand__icon">✈</div>
            <div class="sidebar-brand__title">AeroTwin AI</div>
            <div class="sidebar-brand__subtitle">Airport knowledge assistant · RAG + Gemini</div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_hero(app_mode: str) -> None:
    mode_text = "DEMO LOCAL" if app_mode == "Demo sin API" else "GEMINI LIVE"
    st.markdown(
        textwrap.dedent(f"""
        <section class="hero-shell">
            <div>
                <div class="hero-kicker">
                    <span class="hero-kicker__pulse"></span>
                    {mode_text} · AIRPORT INTELLIGENCE
                </div>
                <h1 class="hero-title"><span class="hero-title__accent">AeroTwin</span> AI</h1>
                <p class="hero-description">
                    Asistente experto que transforma documentación oficial de Aena y ENAIRE/AIP
                    en respuestas claras para pasajeros, profesionales turísticos y equipos de aviación.
                </p>
                <div class="hero-tags">
                    <span class="hero-tag">◉ RAG documental</span>
                    <span class="hero-tag">✦ Respuesta por audiencia</span>
                    <span class="hero-tag">⌖ Ámbito aeroportuario</span>
                    <span class="hero-tag">▣ Fuentes recuperadas</span>
                </div>
            </div>

            <div class="airport-board" aria-label="Panel visual de aeropuertos">
                <div class="board-header">
                    <span>Código</span><span>Aeropuerto</span><span>Estado</span>
                </div>
                <div class="board-row">
                    <span class="board-code">TFS</span><span class="board-airport">Tenerife Sur</span><span class="board-status">READY</span>
                </div>
                <div class="board-row">
                    <span class="board-code">TFN</span><span class="board-airport">Tenerife Norte</span><span class="board-status">READY</span>
                </div>
                <div class="board-row">
                    <span class="board-code">MAD</span><span class="board-airport">Madrid-Barajas</span><span class="board-status">READY</span>
                </div>
                <div class="board-row">
                    <span class="board-code">BCN</span><span class="board-airport">Barcelona-El Prat</span><span class="board-status">READY</span>
                </div>
            </div>
        </section>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_section_heading(icon: str, eyebrow: str, title: str) -> None:
    st.markdown(
        textwrap.dedent(f"""
        <div class="section-heading">
            <div class="section-heading__icon">{icon}</div>
            <div>
                <div class="section-heading__eyebrow">{eyebrow}</div>
                <div class="section-heading__title">{title}</div>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_mode_banner(icon: str, title: str, text: str) -> None:
    st.markdown(
        textwrap.dedent(f"""
        <div class="mode-banner">
            <div class="mode-banner__icon">{icon}</div>
            <div>
                <p class="mode-banner__title">{title}</p>
                <p class="mode-banner__text">{text}</p>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        textwrap.dedent("""
        <div class="footer-shell">
            <span>© AeroTwin AI · MVP académico de Inteligencia Artificial Generativa</span>
            <span class="footer-badge">⚠ Sin datos de vuelos en tiempo real</span>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )


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
    """Checks whether a Google API key is available."""
    api_key = get_secret("GOOGLE_API_KEY")
    return bool(api_key and str(api_key).strip())


# ============================================================
# MODO DEMO SIN API
# ============================================================


def read_demo_responses() -> str:
    """Reads the markdown file with pre-generated demo responses."""
    if not DEMO_RESPONSES_PATH.exists():
        return (
            "No se ha encontrado `outputs/demo_responses.md`.\n\n"
            "Ejecuta primero el notebook y genera las respuestas de demostración."
        )

    return DEMO_RESPONSES_PATH.read_text(encoding="utf-8")


def split_demo_responses(markdown_text: str) -> Dict[str, str]:
    """Splits demo_responses.md into sections by question."""
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
    """Infers the main audience of a document from its folder."""
    path_parts = set(path.parts)

    if "aena_passengers" in path_parts:
        return "passenger"

    if "aena_airlines" in path_parts:
        return "travel_industry"

    if "enaire_aip" in path_parts:
        return "aviation_professional"

    return "general"


def infer_document_group(path: Path) -> str:
    """Infers a readable document group from the path."""
    path_parts = set(path.parts)

    if "aena_passengers" in path_parts:
        return "Aena passenger information"

    if "aena_airlines" in path_parts:
        return "Aena airline and route-development information"

    if "enaire_aip" in path_parts:
        return "ENAIRE/AIP aeronautical information"

    return "General documentation"


def load_html_text(path: Path) -> str:
    """Loads text from an HTML file."""
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
            documents.append(Document(page_content=text, metadata=metadata))

    if not documents:
        raise ValueError("No se han encontrado documentos en data/raw/.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
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
        output_dimensionality=embedding_dimensions,
    )

    # Directorio temporal para evitar escribir ChromaDB en el repo.
    temp_dir = tempfile.mkdtemp(prefix="aerotwin_chroma_")

    vectorstore = Chroma.from_documents(
        documents=chunks_for_index,
        embedding=embeddings,
        persist_directory=temp_dir,
        collection_name="aerotwin_ai_streamlit",
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )

    llm = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=0,
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
    """Builds an enriched query for retrieval."""
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
    """Formats retrieved documents for the LLM."""
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
    """Generates a live answer using Gemini + RAG."""
    from langchain_core.messages import HumanMessage, SystemMessage

    agent = build_live_agent()

    retrieval_query = build_retrieval_query(
        question=question,
        audience=audience,
        airport=airport,
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
        HumanMessage(content=question),
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

inject_custom_css()

with st.sidebar:
    render_sidebar_brand()

    st.markdown('<div class="sidebar-section-label">Configuración</div>', unsafe_allow_html=True)

    app_mode = st.radio(
        "Modo de uso",
        ["Demo sin API", "Live con Gemini"],
        index=0,
        format_func=lambda value: MODE_LABELS[value],
        help="El modo demo usa respuestas guardadas. El modo live consulta Gemini en tiempo real.",
    )

    audience = st.selectbox(
        "Audiencia",
        ["passenger", "travel_industry", "aviation_professional", "auto"],
        index=0,
        format_func=lambda value: AUDIENCE_LABELS[value],
        help="Adapta el tono y el tipo de información de la respuesta.",
    )

    airport = st.selectbox(
        "Aeropuerto o ámbito",
        [
            "general",
            "Aena network",
            "Tenerife Sur",
            "Tenerife Norte",
            "Madrid-Barajas",
            "Barcelona-El Prat",
        ],
        index=0,
        format_func=lambda value: AIRPORT_LABELS[value],
        help="Añade contexto aeroportuario a la recuperación documental.",
    )

    st.divider()
    st.markdown('<div class="sidebar-section-label">Estado del sistema</div>', unsafe_allow_html=True)

    if has_google_api_key():
        st.markdown(
            textwrap.dedent("""
            <div class="api-status api-status--ready">
                <span class="api-status__dot"></span>
                API de Gemini configurada
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            textwrap.dedent("""
            <div class="api-status">
                <span class="api-status__dot"></span>
                API de Gemini no configurada
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )

    st.caption("El modo demo no consume cuota. El modo live puede consumir cuota de Gemini.")

render_hero(app_mode)


# ============================================================
# MODO DEMO
# ============================================================

if app_mode == "Demo sin API":
    render_section_heading("▣", "Experiencia de demostración", "Explora respuestas ya generadas")
    render_mode_banner(
        "◉",
        "Modo seguro sin consumo de API",
        "Las respuestas se leen desde outputs/demo_responses.md. Puedes mostrar el flujo y la calidad del asistente aunque Gemini no esté disponible.",
    )

    demo_text = read_demo_responses()
    sections = split_demo_responses(demo_text)
    section_titles = list(sections.keys())

    selected_section = st.selectbox(
        "Selecciona una respuesta de demostración",
        section_titles,
    )

    with st.container(border=True):
        st.markdown(sections[selected_section])


# ============================================================
# MODO LIVE
# ============================================================

else:
    render_section_heading("✦", "Consulta en tiempo real", "Pregunta a AeroTwin AI")
    render_mode_banner(
        "⚡",
        "RAG + Gemini en directo",
        "La consulta recupera fragmentos relevantes de la base documental, genera una respuesta contextualizada y muestra las fuentes utilizadas.",
    )

    if "live_question" not in st.session_state:
        st.session_state.live_question = ""

    quick_questions = {
        "passenger": [
            ("♿ Asistencia PMR", "¿Cómo puede solicitar asistencia una persona con movilidad reducida en un aeropuerto de Aena?"),
            ("🧳 Equipaje", "¿Qué información general ofrece Aena sobre equipaje y servicios al pasajero?"),
            ("📍 Orientación", "¿Qué servicios de orientación e información puede encontrar un pasajero en el aeropuerto?"),
        ],
        "travel_industry": [
            ("📈 Desarrollo de rutas", "¿Qué información puede ser útil para analizar oportunidades de desarrollo de rutas en la red de Aena?"),
            ("🤝 Incentivos", "¿Qué documentación recuperada menciona incentivos o apoyo a aerolíneas?"),
            ("🌍 Conectividad", "¿Cómo puede utilizarse la documentación para estudiar conectividad y oportunidades turísticas?"),
        ],
        "aviation_professional": [
            ("🗺 Información AIP", "¿Qué tipo de información aeronáutica aparece en la documentación ENAIRE/AIP disponible?"),
            ("🛬 Operación", "Resume la información operacional recuperable para el aeropuerto seleccionado."),
            ("📄 Fuentes", "¿Qué documentos técnicos son más relevantes para una consulta profesional de aviación?"),
        ],
        "auto": [
            ("♿ Asistencia", "¿Cómo puede solicitar asistencia una persona con movilidad reducida en un aeropuerto de Aena?"),
            ("📈 Rutas", "¿Qué información existe sobre desarrollo de rutas e incentivos para aerolíneas?"),
            ("🗺 AIP", "¿Qué tipo de información técnica contiene la documentación ENAIRE/AIP?"),
        ],
    }

    st.caption("Preguntas rápidas")
    question_cols = st.columns(3)
    for col, (button_label, example_question) in zip(question_cols, quick_questions[audience]):
        with col:
            if st.button(button_label, use_container_width=True):
                st.session_state.live_question = example_question

    question = st.text_area(
        "Escribe tu pregunta",
        key="live_question",
        placeholder="Ejemplo: ¿Cómo puede solicitar asistencia una persona con movilidad reducida en un aeropuerto de Aena?",
        height=135,
    )

    ask_button = st.button("Preguntar a AeroTwin AI  →", type="primary", use_container_width=True)

    if ask_button:
        if not question.strip():
            st.error("Escribe una pregunta antes de continuar.")

        elif not has_google_api_key():
            st.error(
                "No hay GOOGLE_API_KEY configurada. "
                "Configura la clave en .streamlit/secrets.toml o en Streamlit Cloud secrets."
            )

        else:
            with st.spinner("Recuperando documentos y consultando Gemini..."):
                try:
                    result = answer_live(
                        question=question,
                        audience=audience,
                        airport=airport,
                    )

                    render_section_heading("✈", "Respuesta generada", "AeroTwin AI")
                    with st.chat_message("assistant", avatar="✈️"):
                        st.markdown(result["answer"])

                    with st.expander("Fuentes recuperadas y detalles técnicos"):
                        st.markdown("**Fuentes recuperadas**")
                        for source in result["sources"]:
                            st.write(f"• {source}")

                        st.divider()
                        tech_col_1, tech_col_2, tech_col_3 = st.columns(3)
                        tech_col_1.metric("Documentos", result["documents_count"])
                        tech_col_2.metric("Chunks generados", result["chunks_count"])
                        tech_col_3.metric("Chunks indexados", result["indexed_chunks_count"])

                except Exception as error:
                    st.error("No se ha podido generar la respuesta live.")
                    with st.expander("Ver detalle técnico del error"):
                        st.code(str(error))
                    st.info(
                        "Puedes seguir usando el modo demo sin API. "
                        "Cuando vuelva la cuota de Gemini, prueba de nuevo el modo live."
                    )


# ============================================================
# PIE DE APP
# ============================================================

render_footer()
