"""Dashboard — usa EXATAMENTE os mesmos controllers/Firestore das abas Salas e Agendamentos."""
from datetime import date

import pandas as pd
import streamlit as st

from controllers import agendamento_controller, sala_controller, usuario_controller
from utils import firestore_client as fs
from utils.auth import somente_admin
from views.layout import carregar


def obter_dados() -> dict:
    """Lê tudo do Firestore (sem cache) e devolve métricas + tabelas prontas."""
    salas = sala_controller.listar()
    reservas = agendamento_controller.listar()
    usuarios = usuario_controller.listar()

    status = reservas["status"]
    hoje = str(date.today())
    futuras = reservas[status.isin(agendamento_controller.STATUS_ATIVOS) & (reservas["data"].astype(str) >= hoje)]

    visao = salas.copy()
    visao["reservas_ativas"] = visao["sala"].astype(str).map(
        futuras["sala"].astype(str).value_counts()
    ).fillna(0).astype(int)

    recentes = reservas.sort_values("criado_em", ascending=False).head(10)

    nomes_salas = set(salas["sala"].astype(str))
    orfas = reservas[~reservas["sala"].astype(str).isin(nomes_salas)]

    return {
        "salas": salas,
        "reservas": reservas,
        "usuarios": usuarios,
        "visao_salas": visao,
        "recentes": recentes,
        "reservas_orfas": orfas,
        "metricas": {
            "Salas": len(salas),
            "Reservas": len(reservas),
            "Confirmadas": int((status == "Confirmada").sum()),
            "Pendentes": int((status == "Pendente").sum()),
            "Usuários": len(usuarios),
        },
    }


def dashboard():
    st.title("ATILA")
    st.caption("Sistema de Gestão e Agendamento de Salas")
    st.divider()

    topo1, topo2 = st.columns([5, 1])
    topo1.header("Dashboard")
    if topo2.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

    d = carregar(obter_dados)

    if somente_admin() and fs.modo_conexao() == "api_key":
        st.warning(
            "O app está no modo legado (API key), que exige regras do Firestore abertas ao público. "
            "Configure [gcp_service_account] nos Secrets e feche as regras (veja o README)."
        )

    cols = st.columns(len(d["metricas"]))
    for col, (rotulo, valor) in zip(cols, d["metricas"].items()):
        col.metric(rotulo, valor)

    if not d["reservas_orfas"].empty:
        nomes = ", ".join(sorted(set(d["reservas_orfas"]["sala"].astype(str))))
        st.warning(f"Há reservas apontando para salas que não estão cadastradas: {nomes}.")

    st.subheader("Visão geral das salas")
    if d["visao_salas"].empty:
        st.info("Nenhuma sala cadastrada.")
    else:
        mostrar = d["visao_salas"].rename(columns={"reservas_ativas": "reservas ativas (hoje em diante)"})
        st.dataframe(mostrar, use_container_width=True, hide_index=True)

    st.subheader("Agendamentos recentes")
    if d["recentes"].empty:
        st.info("Nenhum agendamento cadastrado.")
    else:
        cols_tab = ["id", "professor", "disciplina", "sala", "data", "inicio", "fim", "status"]
        st.dataframe(d["recentes"][cols_tab], use_container_width=True, hide_index=True)
