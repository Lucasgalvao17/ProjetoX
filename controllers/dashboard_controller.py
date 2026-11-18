import streamlit as st
from models.csv_repository import ler_csv

def dashboard():
    st.title("ATILA")
    st.caption("Sistema de Gestão e Agendamento de Salas")
    st.divider()
    st.header("Dashboard")

    salas = ler_csv("salas.csv")
    reservas = ler_csv("agendamentos.csv")
    usuarios = ler_csv("usuarios.csv")
    confirmadas = int((reservas["status"] == "Confirmada").sum()) if not reservas.empty and "status" in reservas else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Salas", len(salas))
    c2.metric("Reservas", len(reservas))
    c3.metric("Confirmadas", confirmadas)
    c4.metric("Usuários", len(usuarios))

    st.subheader("Visão geral das salas")
    if salas.empty:
        st.info("Nenhuma sala cadastrada.")
    else:
        st.dataframe(salas, use_container_width=True, hide_index=True)

    st.subheader("Agendamentos recentes")
    if reservas.empty:
        st.info("Nenhum agendamento cadastrado.")
    else:
        st.dataframe(reservas.tail(10), use_container_width=True, hide_index=True)
