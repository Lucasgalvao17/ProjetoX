import streamlit as st
from utils.auth import usuario_logado
from views.layout import configurar_pagina, menu_lateral
from controllers.dashboard_controller import dashboard

configurar_pagina()

if not usuario_logado():
    st.switch_page("pages/0_Login.py")

menu_lateral()
dashboard()
