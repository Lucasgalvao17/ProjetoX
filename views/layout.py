import streamlit as st
from utils.auth import logout, revalidar_sessao, somente_admin, usuario_atual
from utils.firestore_client import FirestoreError

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


def configurar_pagina():
    st.set_page_config(
        page_title="ATILA | Gestão de Salas",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown("""
    <style>
    .block-container {max-width: 1450px; padding-top: 1.5rem;}
    [data-testid="stSidebar"] {background:#20232d;}
    [data-testid="stSidebar"] * {color:#fff !important;}
    [data-testid="stSidebarNav"] {display:none;}  /* menu automático: usamos o menu por perfil */
    div[data-testid="stMetric"] {border:1px solid #e4e8f0; border-radius:12px; padding:10px;}
    .atila-card {padding:18px;border:1px solid #e4e8f0;border-radius:12px;background:white;}
    .status {padding:5px 10px;border-radius:20px;}
    </style>
    """, unsafe_allow_html=True)


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
    st.sidebar.markdown("# ATILA")
    st.sidebar.caption("Gestão e Agendamento de Salas")
    st.sidebar.divider()
    for arquivo, rotulo, icone in (MENU_ADMIN if somente_admin() else MENU_PROFESSOR):
        st.sidebar.page_link(arquivo, label=rotulo, icon=icone)
    st.sidebar.divider()
    if user:
        st.sidebar.caption(f"Logado como: {user['nome']}")
        st.sidebar.caption(f"Perfil: {user['perfil']}")
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
