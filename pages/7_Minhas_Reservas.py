import streamlit as st
from controllers.agendamento_controller import listar, classificar, do_usuario, cancelar_propria
from utils.auth import usuario_logado, usuario_atual
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar, avisar
from views.reservas_view import abas_reservas, mapa_rotulos

COLUNAS = ["data", "inicio", "fim", "sala", "disciplina", "alunos", "situacao", "motivo", "justificativa"]

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

usuario = usuario_atual()
st.title("Minhas reservas")
st.caption("Acompanhe o andamento das suas solicitações. Se uma for reprovada, o motivo aparece no Histórico.")

minhas = classificar(do_usuario(carregar(listar), usuario))
if minhas.empty:
    st.info("Você ainda não fez nenhuma solicitação. Use **Solicitar Reserva** no menu.")
    st.stop()


def cancelar(sub, chave):
    st.markdown("**Cancelar uma das minhas reservas**")
    rotulos = mapa_rotulos(sub)
    rid = st.selectbox("Reserva", list(rotulos), format_func=lambda i: rotulos[i], key=f"sel_{chave}")
    if st.button("Cancelar minha reserva", key=f"btn_cancelar_{chave}"):
        try:
            cancelar_propria(rid, usuario["email"])
            avisar("success", "Reserva cancelada.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
        except FirestoreError as e:
            st.error(f"Falha ao atualizar no Firestore: {e}")


abas_reservas(minhas, COLUNAS, {
    "Pendentes": lambda sub: cancelar(sub, "pendentes"),
    "Aprovados": lambda sub: cancelar(sub, "aprovados"),
})
