import streamlit as st
from utils.auth import logout, revalidar_sessao, somente_admin, usuario_atual
from utils.firestore_client import FirestoreError
from views.tema import CSS, CSS_LOGIN, html_marca, html_usuario

# (arquivo, rótulo, ícone) — quem vê o quê. O bloqueio de verdade está em cada página (exigir_admin).
MENU_ADMIN = [
    ("app.py", "Dashboard", "📊"),
    ("pages/3_Agendamentos.py", "Agendamentos", "📅"),
    ("pages/2_Nova_Reserva.py", "Nova Reserva", "📝"),
    ("pages/8_Disponibilidade.py", "Disponibilidade", "🔎"),
    ("pages/1_Salas.py", "Salas", "🏫"),
    ("pages/5_Disciplinas.py", "Disciplinas", "📚"),
    ("pages/4_Usuarios.py", "Usuários", "👤"),
    ("pages/6_Perfil.py", "Meu Perfil", "⚙️"),
]
MENU_PROFESSOR = [
    ("app.py", "Início", "🏠"),
    ("pages/2_Nova_Reserva.py", "Solicitar Reserva", "📝"),
    ("pages/7_Minhas_Reservas.py", "Minhas Reservas", "📅"),
    ("pages/8_Disponibilidade.py", "Disponibilidade das Salas", "🔎"),
    ("pages/6_Perfil.py", "Meu Perfil", "⚙️"),
]


def configurar_pagina(login: bool = False):
    st.set_page_config(
        page_title="ATILA | Gestão de Salas",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)  # identidade visual: views/tema.py
    if login:
        st.markdown(f"<style>{CSS_LOGIN}</style>", unsafe_allow_html=True)


def avisar(tipo: str, texto: str):
    """Guarda uma mensagem que sobrevive ao st.rerun() (senão ela some antes de ser lida)."""
    st.session_state.setdefault("_avisos", []).append((tipo, texto))


def mostrar_avisos():
    for tipo, texto in st.session_state.pop("_avisos", []):
        getattr(st, tipo if tipo in ("success", "error", "warning", "info") else "info")(texto)


def menu_lateral():
    if not revalidar_sessao():
        st.warning("Sua sessão não é mais válida (usuário desativado ou removido). Entre novamente.")
        st.switch_page("pages/0_Login.py")
    user = usuario_atual()
    st.sidebar.markdown(html_marca(), unsafe_allow_html=True)
    st.sidebar.divider()
    for arquivo, rotulo, icone in (MENU_ADMIN if somente_admin() else MENU_PROFESSOR):
        st.sidebar.page_link(arquivo, label=rotulo, icon=icone)
    st.sidebar.divider()
    if user:
        st.sidebar.markdown(html_usuario(user["nome"], user["perfil"]), unsafe_allow_html=True)
    if st.sidebar.button("Sair", use_container_width=True):
        logout()
        st.switch_page("pages/0_Login.py")
    mostrar_avisos()


def carregar(funcao, *args, **kwargs):
    """Executa uma leitura do Firestore; se falhar, mostra o erro real e interrompe a página
    (em vez de exibir listas vazias/contadores zerados que parecem 'dados desatualizados')."""
    try:
        return funcao(*args, **kwargs)
    except FirestoreError as e:
        st.error(f"Não foi possível acessar o Firestore: {e}")
        st.stop()
