import streamlit as st
from controllers.agendamento_controller import listar, alterar_status
from utils.auth import usuario_logado, somente_admin
from views.layout import configurar_pagina, menu_lateral

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Agendamentos")
df = listar()

if df.empty:
    st.info("Nenhum agendamento cadastrado.")
else:
    c1, c2, c3 = st.columns(3)
    with c1: status = st.multiselect("Status", sorted(df["status"].unique()))
    with c2: sala = st.multiselect("Sala", sorted(df["sala"].unique()))
    with c3: busca = st.text_input("Pesquisar professor/disciplina")
    
    if status: df = df[df["status"].isin(status)]
    if sala: df = df[df["sala"].isin(sala)]
    if busca: df = df[df["professor"].str.contains(busca, case=False, na=False) | df["disciplina"].str.contains(busca, case=False, na=False)]
    
    st.dataframe(df, use_container_width=True, hide_index=True)

    if somente_admin() and not df.empty:
        st.subheader("Aprovação de reservas")
        rid = st.selectbox("Reserva", df["id"].tolist())
        novo = st.selectbox("Novo status", ["Confirmada", "Reprovada", "Pendente", "Cancelada"])
        if st.button("Atualizar status", type="primary"):
            alterar_status(rid, novo)
            st.success("Status atualizado.")
            st.rerun()
