import streamlit as st
from controllers import disciplina_controller as dc
from utils.auth import usuario_logado
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Disciplinas")
with st.form("disciplina"):
    c1, c2 = st.columns(2)
    nome = c1.text_input("Nome da disciplina")
    codigo = c2.text_input("Código")
    curso = st.text_input("Curso")
    if st.form_submit_button("Cadastrar disciplina", type="primary"):
        try:
            dc.cadastrar(nome, codigo, curso)
            st.success("Disciplina cadastrada.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
        except FirestoreError as e:
            st.error(f"Falha ao salvar no Firestore: {e}")

st.dataframe(carregar(dc.listar), use_container_width=True, hide_index=True)
