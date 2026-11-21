import streamlit as st
from datetime import time

from controllers.agendamento_controller import listar as listar_reservas, disponibilidade, agenda_do_dia, classificar
from controllers.sala_controller import listar as listar_salas
from utils import tempo
from utils.auth import usuario_logado, somente_admin
from utils.tabelas import para_numero
from views.layout import configurar_pagina, menu_lateral, carregar

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Disponibilidade das salas")
st.caption("Veja quais salas estão livres em uma data e horário. Reservas pendentes também bloqueiam a sala.")

salas = carregar(listar_salas)
if salas.empty:
    st.info("Ainda não há salas cadastradas.")
    st.stop()
reservas = carregar(listar_reservas)

c1, c2, c3 = st.columns(3)
data = c1.date_input("Data", value=tempo.hoje(), key="disp_data")
inicio = c2.time_input("Horário inicial", value=time(14, 0), key="disp_inicio")
fim = c3.time_input("Horário final", value=time(16, 0), key="disp_fim")
f1, f2, f3 = st.columns(3)
cap_min = f1.number_input("Capacidade mínima", min_value=0, max_value=500, value=0, key="disp_cap")
tipos = ["Todos"] + sorted(set(salas["tipo"].astype(str)) - {""})
tipo = f2.selectbox("Tipo de sala", tipos, key="disp_tipo")
so_livres = f3.checkbox("Mostrar só salas livres", value=False, key="disp_livres")

if fim <= inicio:
    st.error("O horário final deve ser posterior ao horário inicial.")
    st.stop()

filtradas = salas[para_numero(salas["capacidade"]) >= cap_min]
if tipo != "Todos":
    filtradas = filtradas[filtradas["tipo"].astype(str) == tipo]

resultado = disponibilidade(filtradas, str(data), inicio.strftime("%H:%M"), fim.strftime("%H:%M"), reservas)
st.metric("Salas livres no horário", int((resultado["disponibilidade"] == "Livre").sum()))
if so_livres:
    resultado = resultado[resultado["disponibilidade"] == "Livre"]
if resultado.empty:
    st.warning("Nenhuma sala encontrada com esses filtros.")
else:
    cols = ["sala", "disponibilidade", "capacidade", "tipo", "campus", "predio", "andar", "computadores", "projetor", "ar_condicionado"]
    st.dataframe(resultado[cols], use_container_width=True, hide_index=True)

st.subheader("Agenda do dia")
nomes = salas["sala"].astype(str).tolist()
sala = st.selectbox("Sala", nomes, key="disp_sala")
agenda = classificar(agenda_do_dia(sala, str(data), reservas))
if agenda.empty:
    st.success(f"{sala} está livre durante todo o dia {data}.")
else:
    # o professor vê só os horários ocupados (sem nomes de outros professores); o admin vê tudo
    colunas = ["inicio", "fim", "situacao"] + (["professor", "disciplina"] if somente_admin() else [])
    st.dataframe(agenda[colunas], use_container_width=True, hide_index=True)
