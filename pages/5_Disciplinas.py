import streamlit as st
from models.csv_repository import ler_csv, adicionar_linha
from utils.auth import usuario_logado
from views.layout import configurar_pagina, menu_lateral

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Disciplinas")
with st.form("disciplina"):
    c1,c2=st.columns(2)
    nome=c1.text_input("Nome da disciplina")
    codigo=c2.text_input("Código")
    curso=st.text_input("Curso")
    if st.form_submit_button("Cadastrar disciplina",type="primary"):
        df=ler_csv("disciplinas.csv",["id","nome","codigo","curso"])
        novo=1 if df.empty else int(pd_num(df["id"]).max())+1
        adicionar_linha("disciplinas.csv",{"id":novo,"nome":nome,"codigo":codigo,"curso":curso},["id","nome","codigo","curso"])
        st.success("Disciplina cadastrada."); st.rerun()
st.dataframe(ler_csv("disciplinas.csv"),use_container_width=True,hide_index=True)

def pd_num(s):
    import pandas as pd
    return pd.to_numeric(s,errors="coerce").fillna(0)
