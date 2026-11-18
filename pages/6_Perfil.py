import streamlit as st
from utils.auth import usuario_logado, usuario_atual
from views.layout import configurar_pagina, menu_lateral

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Meu Perfil")
u=usuario_atual()
c1,c2=st.columns(2)
c1.text_input("Nome",u["nome"],disabled=True)
c2.text_input("E-mail",u["email"],disabled=True)
st.text_input("Perfil",u["perfil"],disabled=True)
st.success("Conta ativa.")
