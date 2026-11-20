import streamlit as st
from utils.auth import logout, usuario_atual
from utils.firestore_client import FirestoreError

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
    div[data-testid="stMetric"] {border:1px solid #e4e8f0; border-radius:12px; padding:10px;}
    .atila-card {padding:18px;border:1px solid #e4e8f0;border-radius:12px;background:white;}
    .status {padding:5px 10px;border-radius:20px;}
    </style>
    """, unsafe_allow_html=True)

def menu_lateral():
    user = usuario_atual()
    st.sidebar.markdown("# ATILA")
    st.sidebar.caption("Gestão e Agendamento de Salas")
    st.sidebar.divider()
    st.sidebar.page_link("app.py", label="Dashboard", icon="📊")
    st.sidebar.page_link("pages/1_Salas.py", label="Salas", icon="🏫")
    st.sidebar.page_link("pages/2_Nova_Reserva.py", label="Nova Reserva", icon="📝")
    st.sidebar.page_link("pages/3_Agendamentos.py", label="Agendamentos", icon="📅")
    st.sidebar.page_link("pages/4_Usuarios.py", label="Usuários", icon="👤")
    st.sidebar.page_link("pages/5_Disciplinas.py", label="Disciplinas", icon="📚")
    st.sidebar.page_link("pages/6_Perfil.py", label="Meu Perfil", icon="⚙️")
    st.sidebar.divider()
    if user:
        st.sidebar.caption(f"Logado como: {user['nome']}")
        st.sidebar.caption(f"Perfil: {user['perfil']}")
    if st.sidebar.button("Sair", use_container_width=True):
        logout()
        st.switch_page("pages/0_Login.py")


def carregar(funcao, *args, **kwargs):
    """Executa uma leitura do Firestore; se falhar, mostra o erro real e interrompe a página
    (em vez de exibir listas vazias/contadores zerados que parecem 'dados desatualizados')."""
    try:
        return funcao(*args, **kwargs)
    except FirestoreError as e:
        st.error(f"Não foi possível acessar o Firestore: {e}")
        st.stop()
