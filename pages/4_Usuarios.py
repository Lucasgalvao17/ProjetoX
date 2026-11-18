import streamlit as st
from models.csv_repository import ler_csv, atualizar_csv
from utils.auth import usuario_logado, somente_admin
from views.layout import configurar_pagina, menu_lateral

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Usuários")
df=ler_csv("usuarios.csv")
if not somente_admin():
    df=df[["id","nome","email","perfil","ativo"]]
    st.info("Somente administradores podem alterar usuários.")
st.dataframe(df,use_container_width=True,hide_index=True)

if somente_admin() and not df.empty:
    st.subheader("Ativar / desativar usuário")
    uid=st.selectbox("Usuário",df["id"].tolist())
    acao=st.selectbox("Situação",["Sim","Não"])
    if st.button("Salvar situação"):
        df.loc[df["id"].astype(str)==str(uid),"ativo"]=acao
        atualizar_csv("usuarios.csv",df)
        st.success("Usuário atualizado."); st.rerun()
