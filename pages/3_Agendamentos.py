import streamlit as st
from controllers.agendamento_controller import listar, classificar, alterar_status, ConflitoHorario
from utils.auth import usuario_logado, usuario_atual, exigir_admin
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar, avisar
from views.reservas_view import abas_reservas, mapa_rotulos

COLUNAS = ["id", "professor", "disciplina", "sala", "data", "inicio", "fim", "alunos",
           "situacao", "motivo", "justificativa", "criado_por"]

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()
exigir_admin()

st.title("Agendamentos")
st.caption("Reservas reprovadas ou já realizadas ficam no Histórico — nada é apagado do Firestore.")
todos = classificar(carregar(listar))

if todos.empty:
    st.info("Nenhum agendamento cadastrado.")
    st.stop()

c1, c2 = st.columns(2)
with c1: salas = st.multiselect("Sala", sorted(todos["sala"].astype(str).unique()))
with c2: busca = st.text_input("Pesquisar professor/disciplina")
df = todos
if salas: df = df[df["sala"].isin(salas)]
if busca:
    df = df[df["professor"].astype(str).str.contains(busca, case=False, na=False)
            | df["disciplina"].astype(str).str.contains(busca, case=False, na=False)]

admin = usuario_atual()["email"]


def executar(acao, sucesso):
    """Roda a alteração no Firestore e recarrega a tela já com a reserva na tabela certa."""
    try:
        acao()
        avisar("success", sucesso)
        st.rerun()
    except ConflitoHorario as e:
        st.error(f"Não foi possível: conflito de horário. {e}")
    except ValueError as e:
        st.error(str(e))
    except FirestoreError as e:
        st.error(f"Falha ao atualizar no Firestore: {e}")


def acoes_pendentes(sub):
    st.markdown("**Analisar solicitação**")
    rotulos = mapa_rotulos(sub)
    rid = st.selectbox("Solicitação", list(rotulos), format_func=lambda i: rotulos[i], key="sel_pendentes")
    motivo = st.text_input("Motivo (opcional; aparece para o solicitante se reprovar)", key="motivo_pendentes")
    b1, b2 = st.columns(2)
    if b1.button("✅ Aprovar", type="primary", key="btn_aprovar"):
        executar(lambda: alterar_status(rid, "Confirmada", admin), "Reserva aprovada.")
    if b2.button("⛔ Reprovar", key="btn_reprovar"):
        executar(lambda: alterar_status(rid, "Reprovada", admin, motivo),
                 "Reserva reprovada. O registro foi mantido no Histórico.")


def acoes_aprovados(sub):
    st.markdown("**Cancelar reserva aprovada**")
    rotulos = mapa_rotulos(sub)
    rid = st.selectbox("Reserva", list(rotulos), format_func=lambda i: rotulos[i], key="sel_aprovados")
    motivo = st.text_input("Motivo do cancelamento (opcional)", key="motivo_aprovados")
    if st.button("Cancelar reserva", key="btn_cancelar"):
        executar(lambda: alterar_status(rid, "Cancelada", admin, motivo), "Reserva cancelada.")


def _reabrir(sub, chave):
    st.markdown("**Reabrir como pendente** (volta para análise; só se o horário ainda estiver livre)")
    rotulos = mapa_rotulos(sub)
    rid = st.selectbox("Reserva", list(rotulos), format_func=lambda i: rotulos[i], key=f"sel_{chave}")
    if st.button("Reabrir como pendente", key=f"btn_reabrir_{chave}"):
        executar(lambda: alterar_status(rid, "Pendente", admin), "Reserva reaberta como pendente.")


def acoes_cancelados(sub):
    _reabrir(sub, "cancelados")


def acoes_historico(sub):
    reprovadas = sub[sub["situacao"] == "Reprovada"]
    if reprovadas.empty:
        st.caption("Reservas já realizadas não podem ser reabertas.")
    else:
        _reabrir(reprovadas, "historico")


abas_reservas(df, COLUNAS, {
    "Pendentes": acoes_pendentes, "Aprovados": acoes_aprovados,
    "Cancelados": acoes_cancelados, "Histórico": acoes_historico,
})
