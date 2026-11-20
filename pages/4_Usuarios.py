import streamlit as st
from controllers import usuario_controller as uc
from utils.auth import usuario_logado, usuario_atual, somente_admin
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Usuários")
df = carregar(uc.listar)
if not somente_admin():
    st.info("Somente administradores podem alterar usuários.")
st.dataframe(df, use_container_width=True, hide_index=True)

if somente_admin() and not df.empty:
    st.subheader("Ativar / desativar usuário")
    rotulos = {r["id"]: f"{r['nome']} ({r['email']})" for _, r in df.iterrows()}
    uid = st.selectbox("Usuário", list(rotulos), format_func=lambda i: rotulos[i])
    acao = st.selectbox("Situação", ["Sim", "Não"])
    if st.button("Salvar situação"):
        if uid == usuario_atual()["id"] and acao == "Não":
            st.error("Você não pode desativar o seu próprio usuário.")
        else:
            try:
                uc.definir_ativo(uid, acao)
                st.success("Usuário atualizado.")
                st.rerun()
            except FirestoreError as e:
                st.error(f"Falha ao salvar no Firestore: {e}")
