"""Componente de tela compartilhado: as 4 tabelas de reservas (Aprovados, Pendentes, Cancelados, Histórico)."""
import streamlit as st

from controllers.agendamento_controller import ABAS

VAZIO = {
    "Aprovados": "Nenhuma reserva aprovada por vir.",
    "Pendentes": "Nenhuma reserva aguardando aprovação.",
    "Cancelados": "Nenhuma reserva cancelada.",
    "Histórico": "Histórico vazio (reprovadas e reservas já realizadas aparecem aqui).",
}


def rotulo_reserva(r) -> str:
    return f"{r['professor']} · {r['sala']} · {r['data']} {r['inicio']}-{r['fim']} · {r['situacao']}"


def mapa_rotulos(sub) -> dict:
    return {r["id"]: rotulo_reserva(r) for _, r in sub.iterrows()}


def abas_reservas(df, colunas, acoes=None):
    """`df` já classificado (colunas `aba`/`situacao`). `acoes`: {nome_da_aba: função(sub_df)}."""
    acoes = acoes or {}
    # Rótulos FIXOS: se o contador mudasse no título, o Streamlit voltaria para a 1ª aba após cada ação.
    st.caption(" · ".join(f"{a}: {int((df['aba'] == a).sum())}" for a in ABAS))
    tabs = st.tabs(list(ABAS))
    for tab, aba in zip(tabs, ABAS):
        with tab:
            sub = df[df["aba"] == aba]
            if sub.empty:
                st.info(VAZIO[aba])
                continue
            st.dataframe(sub[colunas], use_container_width=True, hide_index=True)
            if aba in acoes:
                acoes[aba](sub)
