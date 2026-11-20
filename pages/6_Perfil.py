import streamlit as st
from utils.auth import usuario_logado, usuario_atual, alterar_senha
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Meu Perfil")
u = usuario_atual()
c1, c2 = st.columns(2)
c1.text_input("Nome", u["nome"], disabled=True)
c2.text_input("E-mail", u["email"], disabled=True)
st.text_input("Perfil", u["perfil"], disabled=True)
st.success("Conta ativa.")

st.subheader("Alterar senha")
atual = st.text_input("Senha atual", type="password", key="pw_atual")
nova = st.text_input("Nova senha", type="password", key="pw_nova")
nova2 = st.text_input("Confirmar nova senha", type="password", key="pw_nova2")
if st.button("Alterar senha", type="primary"):
    if nova != nova2:
        st.error("As senhas não coincidem.")
    else:
        try:
            ok, msg = alterar_senha(u["id"], atual, nova)
            (st.success if ok else st.error)(msg)
        except FirestoreError as e:
            st.error(f"Falha ao salvar no Firestore: {e}")
