import streamlit as st
from datetime import date, time

from controllers.sala_controller import listar as listar_salas
from controllers.agendamento_controller import criar, ConflitoHorario
from utils.auth import usuario_logado, usuario_atual
from utils.firestore_client import FirestoreError
from utils.tabelas import para_numero
from views.layout import configurar_pagina, menu_lateral, carregar

configurar_pagina()

if not usuario_logado():
    st.switch_page("pages/0_Login.py")

menu_lateral()

st.title("Nova reserva")
st.caption("A sala será recomendada conforme capacidade, tipo e recursos.")

salas = carregar(listar_salas)
if salas.empty:
    st.warning("Cadastre salas antes de fazer uma reserva.")
    st.stop()

# Sem st.form: assim a lista de salas recomendadas se atualiza na hora
# quando o usuário muda a quantidade de alunos ou o tipo de aula.
c1, c2 = st.columns(2)
with c1:
    professor = st.text_input("Professor / solicitante", value=usuario_atual()["nome"])
    disciplina = st.text_input("Disciplina")
    tipo = st.selectbox("Tipo de aula", ["Teórica", "Laboratório de Informática", "Auditório", "Prática"])
    alunos = st.number_input("Quantidade de alunos", min_value=1, max_value=500, value=32, step=1)
with c2:
    data = st.date_input("Data", value=date.today())
    inicio = st.time_input("Horário inicial", value=time(14, 0))
    fim = st.time_input("Horário final", value=time(16, 0))

candidatos = salas[para_numero(salas["capacidade"]) >= alunos].copy()
if tipo == "Laboratório de Informática":
    candidatos = candidatos[para_numero(candidatos["computadores"]) >= alunos]

excepcional = candidatos.empty
if excepcional:
    st.warning("Nenhuma sala atende à capacidade/recursos pedidos. Você pode escolher outra "
               "sala, mas a reserva será excepcional e exige justificativa.")
    opcoes = salas
else:
    # melhor encaixe primeiro: mesmo tipo de aula e menor capacidade suficiente
    candidatos["_fora_do_tipo"] = candidatos["tipo"].astype(str) != tipo
    candidatos["_cap"] = para_numero(candidatos["capacidade"])
    opcoes = candidatos.sort_values(["_fora_do_tipo", "_cap"])

sala = st.selectbox(
    "Sala (reserva excepcional)" if excepcional else "Sala recomendada",
    opcoes["sala"].astype(str).tolist(),
)
escolhida = opcoes[opcoes["sala"].astype(str) == sala].iloc[0]
st.info(f"**{escolhida['sala']}** | capacidade {int(para_numero(escolhida[['capacidade']]).iloc[0])} | {escolhida['tipo']}")

justificativa = st.text_area(
    "Justificativa para reserva excepcional",
    placeholder="Informe uma justificativa caso a reserva precise de alguma exceção.",
)

if st.button("Solicitar reserva", type="primary"):
    erros = []
    if not professor.strip():
        erros.append("Informe o professor ou solicitante.")
    if not disciplina.strip():
        erros.append("Informe a disciplina.")
    if fim <= inicio:
        erros.append("O horário final deve ser posterior ao horário inicial.")
    if data < date.today():
        erros.append("A data da reserva não pode estar no passado.")
    if excepcional and not justificativa.strip():
        erros.append("Informe a justificativa da reserva excepcional.")

    if erros:
        for erro in erros:
            st.error(erro)
    else:
        try:
            novo_id = criar({
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
                "criado_por": usuario_atual()["email"],
            })
            st.success(f"Reserva enviada para análise com sucesso! ID: {novo_id}")
        except ConflitoHorario as e:
            st.error(f"Conflito de horário: {e}")
        except ValueError as e:
            st.error(str(e))
        except FirestoreError as e:
            st.error(f"Falha ao salvar no Firestore: {e}")
