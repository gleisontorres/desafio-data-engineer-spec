"""
Interface Web para o Pokemon Data Explorer.

Aplicacao Streamlit para interacao com o Agente de IA via linguagem natural.
Consome o endpoint POST /ask do servico agent.
"""

import base64
import os
from pathlib import Path
from typing import Optional

import requests
import streamlit as st

# Configuracao
AGENT_URL = os.getenv("AGENT_URL", "http://agent:8001")
REQUEST_TIMEOUT = 60

# Cores TOTVS (baseado na identidade visual)
TOTVS_PURPLE = "#8B5CF6"
TOTVS_PURPLE_DARK = "#7C3AED"
TOTVS_TEAL = "#0D4B5F"
TOTVS_TEAL_DARK = "#0A3847"
TOTVS_TEAL_LIGHT = "#1E6B82"


def get_base64_image(image_path: str) -> str:
    """Converte imagem para base64 para uso em HTML."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def configure_page() -> None:
    """Configura a pagina Streamlit com tema e layout."""
    st.set_page_config(
        page_title="Pokemon Data Explorer AI Agent",
        page_icon="assets/logo.png",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # CSS customizado com tema TOTVS
    st.markdown(
        f"""
        <style>
        /* Tema escuro base */
        .stApp {{
            background: linear-gradient(135deg, {TOTVS_TEAL_DARK} 0%, {TOTVS_TEAL} 50%, {TOTVS_PURPLE_DARK} 100%);
            background-attachment: fixed;
        }}

        /* Header customizado */
        .main-header {{
            background: linear-gradient(90deg, {TOTVS_TEAL} 0%, {TOTVS_PURPLE_DARK} 100%);
            padding: 1rem 2rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}

        .main-header img {{
            height: 150px;
            width: auto;
        }}

        .main-header .header-text h1 {{
            color: white;
            margin: 0;
            font-size: 2.8rem;
            font-weight: 700;
        }}

        .main-header .header-text p {{
            color: rgba(255, 255, 255, 0.6);
            margin: 0.2rem 0 0 0;
            font-size: 0.75rem;
            font-weight: 400;
        }}

        /* Container do chat com scroll */
        .chat-container {{
            max-height: 400px;
            overflow-y: auto;
            padding: 1rem;
            margin-bottom: 1rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
        }}

        /* Estilo das mensagens do chat */
        .user-message {{
            background: linear-gradient(135deg, {TOTVS_PURPLE} 0%, {TOTVS_PURPLE_DARK} 100%);
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 15px 15px 5px 15px;
            margin: 0.5rem 0;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 2px 10px rgba(139, 92, 246, 0.3);
        }}

        .user-message strong {{
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.75rem;
        }}

        .agent-message {{
            background: linear-gradient(135deg, {TOTVS_TEAL_LIGHT} 0%, {TOTVS_TEAL} 100%);
            color: #E0E0E0;
            padding: 0.75rem 1rem;
            border-radius: 15px 15px 15px 5px;
            margin: 0.5rem 0;
            max-width: 85%;
            max-height: 300px;
            overflow-y: auto;
            box-shadow: 0 2px 10px rgba(13, 75, 95, 0.3);
            font-size: 0.9rem;
            line-height: 1.4;
        }}

        .agent-message strong {{
            color: {TOTVS_PURPLE};
            font-size: 0.75rem;
        }}

        /* Botao primario */
        .stButton > button {{
            background: linear-gradient(90deg, {TOTVS_PURPLE} 0%, {TOTVS_PURPLE_DARK} 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(139, 92, 246, 0.3);
        }}

        .stButton > button:hover {{
            background: linear-gradient(90deg, {TOTVS_PURPLE_DARK} 0%, #6D28D9 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.5);
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {TOTVS_TEAL_DARK} 0%, {TOTVS_TEAL} 100%);
        }}

        [data-testid="stSidebar"] .stButton > button {{
            background: rgba(139, 92, 246, 0.2);
            border: 1px solid {TOTVS_PURPLE};
            color: white;
        }}

        [data-testid="stSidebar"] .stButton > button:hover {{
            background: {TOTVS_PURPLE};
        }}

        /* Input de texto */
        .stTextInput > div > div > input {{
            background-color: rgba(13, 75, 95, 0.5);
            border: 2px solid {TOTVS_PURPLE};
            border-radius: 10px;
            color: white;
            padding: 0.75rem 1rem;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: {TOTVS_PURPLE};
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
        }}

        /* Erro */
        .error-message {{
            background-color: rgba(239, 68, 68, 0.2);
            border-left: 4px solid #EF4444;
            color: #FCA5A5;
            padding: 0.75rem 1rem;
            border-radius: 0 15px 15px 0;
            margin: 0.5rem 0;
            max-width: 80%;
        }}

        /* Area de input fixa na parte inferior */
        .input-area {{
            background: linear-gradient(90deg, {TOTVS_TEAL_DARK} 0%, rgba(13, 75, 95, 0.95) 100%);
            padding: 1rem;
            border-radius: 15px;
            margin-top: 0.5rem;
            box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.2);
        }}

        /* Scrollbar customizada */
        ::-webkit-scrollbar {{
            width: 6px;
        }}

        ::-webkit-scrollbar-track {{
            background: {TOTVS_TEAL_DARK};
            border-radius: 3px;
        }}

        ::-webkit-scrollbar-thumb {{
            background: {TOTVS_PURPLE};
            border-radius: 3px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {TOTVS_PURPLE_DARK};
        }}

        /* Info box */
        .stAlert {{
            background-color: rgba(139, 92, 246, 0.1);
            border: 1px solid {TOTVS_PURPLE};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    """Inicializa o estado da sessao."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


def render_header() -> None:
    """Renderiza o header da aplicacao com logo."""
    logo_path = Path(__file__).parent / "assets" / "logo.png"

    if logo_path.exists():
        logo_base64 = get_base64_image(str(logo_path))
        st.markdown(
            f"""
            <div class="main-header">
                <img src="data:image/png;base64,{logo_base64}" alt="Logo">
                <div class="header-text">
                    <h1>Pokemon Data Explorer AI Agent</h1>
                    <p>Powered by Gleison Mota Data Pipeline</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="main-header">
                <div class="header-text">
                    <h1>Pokemon Data Explorer</h1>
                    <p>Powered by TOTVS IDEIA Data Pipeline</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar() -> None:
    """Renderiza a sidebar com exemplos de perguntas."""
    with st.sidebar:
        st.header("Exemplos de Perguntas")
        st.markdown("Clique em uma pergunta para usar:")

        example_questions = [
            "Qual pokemon tem o maior ataque?",
            "Liste os pokemons do tipo fogo",
            "Compare pikachu e charizard",
            "Quais sao os top 5 pokemons por defesa?",
            "Me fale sobre o bulbasaur",
        ]

        for i, question in enumerate(example_questions):
            if st.button(question, key=f"example_{i}", use_container_width=True):
                st.session_state.pending_question = question

        st.divider()

        st.markdown("### Sobre")
        st.markdown(
            """
            Esta interface permite consultar dados de Pokemon
            usando linguagem natural.

            O agente de IA processa sua pergunta e consulta
            a base de dados com informacoes dos 151 Pokemon
            da primeira geracao.
            """
        )

        st.divider()

        st.markdown("### Status")
        if check_agent_health():
            st.success("Agente online")
        else:
            st.error("Agente offline")


def check_agent_health() -> bool:
    """Verifica se o agente esta online."""
    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def ask_agent(question: str) -> Optional[str]:
    """
    Envia pergunta para o agente e retorna a resposta.

    Args:
        question: Pergunta do usuario.

    Returns:
        Resposta do agente ou None em caso de erro.
    """
    try:
        response = requests.post(
            f"{AGENT_URL}/ask",
            json={"question": question},
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "Resposta vazia do agente.")

        print(f"Erro na resposta do agente: status={response.status_code}")
        return None

    except requests.Timeout:
        print(f"Timeout ao consultar agente: {REQUEST_TIMEOUT}s")
        return None
    except requests.ConnectionError as e:
        print(f"Erro de conexao com o agente: {e}")
        return None
    except requests.RequestException as e:
        print(f"Erro na requisicao ao agente: {e}")
        return None


def render_chat_history() -> None:
    """Renderiza o historico de chat com scroll."""
    chat_html = '<div class="chat-container">'

    for entry in st.session_state.chat_history:
        # Pergunta do usuario
        chat_html += f'<div class="user-message"><strong>Voce</strong><br>{entry["question"]}</div>'

        # Resposta do agente
        answer_escaped = entry["answer"].replace("\n", "<br>")
        if entry.get("error"):
            chat_html += f'<div class="error-message"><strong>Erro</strong><br>{answer_escaped}</div>'
        else:
            chat_html += f'<div class="agent-message"><strong>Agente</strong><br>{answer_escaped}</div>'

    chat_html += "</div>"

    st.markdown(chat_html, unsafe_allow_html=True)


def process_question(question: str) -> None:
    """
    Processa uma pergunta do usuario.

    Args:
        question: Pergunta a ser processada.
    """
    with st.spinner("Consultando o agente..."):
        answer = ask_agent(question)

        if answer:
            st.session_state.chat_history.append(
                {"question": question, "answer": answer, "error": False}
            )
        else:
            st.session_state.chat_history.append(
                {
                    "question": question,
                    "answer": "Nao foi possivel obter resposta do agente. "
                    "Verifique se o servico esta online.",
                    "error": True,
                }
            )


def render_clear_button() -> None:
    """Renderiza botao para limpar historico."""
    if st.session_state.chat_history:
        col1, col2, col3 = st.columns([4, 1, 4])
        with col2:
            if st.button("Limpar", type="secondary", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()


def main() -> None:
    """Funcao principal da aplicacao."""
    configure_page()
    init_session_state()

    render_sidebar()
    render_header()

    # Processa pergunta pendente da sidebar
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
        process_question(question)

    # Area do chat com historico
    if st.session_state.chat_history:
        render_chat_history()
        render_clear_button()
    else:
        st.info(
            "Digite uma pergunta abaixo ou clique em um exemplo na barra lateral "
            "para comecar a conversar com o agente."
        )

    # Input sempre na parte inferior
    st.divider()

    col1, col2 = st.columns([5, 1])

    with col1:
        question = st.text_input(
            "Sua pergunta",
            value="",
            placeholder="Digite sua pergunta sobre Pokemon...",
            label_visibility="collapsed",
            key="question_input",
        )

    with col2:
        submit = st.button("Consultar", type="primary", use_container_width=True)

    if submit and question:
        process_question(question)
        st.rerun()


if __name__ == "__main__":
    main()
