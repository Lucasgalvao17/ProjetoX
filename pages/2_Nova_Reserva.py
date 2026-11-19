import streamlit as st
from datetime import date, time
import pandas as pd

from controllers.sala_controller import listar as listar_salas
from controllers.agendamento_controller import criar, horario_disponivel
from utils.auth import usuario_logado, usuario_atual
from views.layout import configurar_pagina, menu_lateral


def pd_num(serie):
    """Converte uma coluna para números sem quebrar quando houver valores vazios."""
    return pd.to_numeric(serie, errors="coerce").fillna(0)


configurar_pagina()

if not usuario_logado():
    st.switch_page("pages/0_Login.py")

menu_lateral()

st.title("Nova reserva")
st.caption("A sala será recomendada conforme capacidade, tipo e recursos.")

salas = listar_salas()

with st.form("reserva"):
    c1, c2 = st.columns(2)

    with c1:
        professor = st.text_input(
            "Professor / solicitante",
            value=usuario_atual()["nome"]
        )
        disciplina = st.text_input("Disciplina")
        tipo = st.selectbox(
            "Tipo de aula",
            ["Teórica", "Laboratório de Informática", "Auditório", "Prática"]
        )
        alunos = st.number_input(
            "Quantidade de alunos",
            min_value=1,
            max_value=500,
            value=32,
            step=1
        )

    with c2:
        data = st.date_input("Data", value=date.today())
        inicio = st.time_input("Horário inicial", value=time(14, 0))
        fim = st.time_input("Horário final", value=time(16, 0))

    sala = ""

    if salas.empty:
        st.warning("Cadastre salas antes de fazer uma reserva.")
    else:
        candidatos = salas[pd_num(salas["capacidade"]) >= alunos].copy()

        if tipo == "Laboratório de Informática" and not candidatos.empty and "computadores" in candidatos.columns:
            candidatos = candidatos[pd_num(candidatos["computadores"]) >= alunos]

        if candidatos.empty:
            st.error("Nenhuma sala atende aos requisitos informados.")
            sala = st.selectbox("Sala disponível", salas["sala"].astype(str).tolist())
        else:
            sala = st.selectbox(
                "Sala recomendada",
                candidatos["sala"].astype(str).tolist()
            )
            r = candidatos.iloc[0]
            st.info(
                f"Recomendação: **{r['sala']}** | "
                f"capacidade {int(pd_num(pd.Series([r['capacidade']])).iloc[0])} | "
                f"{r['tipo']}"
            )

    justificativa = st.text_area(
        "Justificativa para reserva excepcional",
        placeholder="Informe uma justificativa caso a reserva precise de alguma exceção."
    )

    enviar = st.form_submit_button("Solicitar reserva", type="primary")


if enviar:
    erros = []

    if not professor.strip():
        erros.append("Informe o professor ou solicitante.")

    if not disciplina.strip():
        erros.append("Informe a disciplina.")

    if not sala:
        erros.append("Selecione uma sala.")

    if fim <= inicio:
        erros.append("O horário final deve ser posterior ao horário inicial.")

    if erros:
        for erro in erros:
            st.error(erro)
    elif not horario_disponivel(
        sala,
        data,
        inicio.strftime("%H:%M"),
        fim.strftime("%H:%M")
    ):
        st.error("Já existe uma reserva pendente ou confirmada nesse horário para esta sala.")
    else:
        try:
            criar({
                "professor": professor.strip(),
                "disciplina": disciplina.strip(),
                "sala": sala,
                "tipo_aula": tipo,
                "alunos": int(alunos),
                "data": str(data),
                "inicio": inicio.strftime("%H:%M"),
                "fim": fim.strftime("%H:%M"),
                "status": "Pendente",
                "justificativa": justificativa.strip(),
                "criado_por": usuario_atual()["email"]
            })
            st.success("Reserva enviada para análise com sucesso.")
        except Exception as e:
            st.error(f"Falha ao salvar no Firestore: {e}")
