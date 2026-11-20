import streamlit as st
from utils.auth import login, cadastrar_usuario, usuario_logado
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina

configurar_pagina()

if usuario_logado():
    st.switch_page("app.py")

st.markdown("<h1 style='text-align:center;color:#2f70ff'>ATILA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center'>Gestão e Agendamento de Salas</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔐 Entrar", "👤 Criar conta"])

with tab1:
    st.subheader("Acesse sua conta")
    email = st.text_input("E-mail", key="login_email")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Entrar", type="primary", use_container_width=True):
        try:
            if login(email, senha):
                st.success("Login realizado.")
                st.switch_page("app.py")
            else:
                st.error("E-mail ou senha inválidos.")
        except FirestoreError as e:
            st.error(f"Não foi possível acessar o Firestore: {e}")

with tab2:
    st.subheader("Crie sua conta")
    nome = st.text_input("Nome completo", key="cad_nome")
    email2 = st.text_input("E-mail", key="cad_email")
    senha2 = st.text_input("Senha", type="password", key="cad_senha")
    senha3 = st.text_input("Confirmar senha", type="password", key="cad_senha2")
    perfil = st.selectbox("Perfil", ["Professor", "Solicitante"])
    if st.button("Criar conta", type="primary", use_container_width=True):
        if senha2 != senha3:
            st.error("As senhas não coincidem.")
        else:
            try:
                ok, msg = cadastrar_usuario(nome, email2, senha2, perfil)
                (st.success if ok else st.error)(msg)
            except FirestoreError as e:
                st.error(f"Não foi possível acessar o Firestore: {e}")
