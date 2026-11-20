import streamlit as st
from controllers.agendamento_controller import listar, alterar_status, ConflitoHorario, STATUS_VALIDOS
from utils.auth import usuario_logado, usuario_atual, somente_admin
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar

COLUNAS_TABELA = ["id", "professor", "disciplina", "sala", "tipo_aula", "alunos", "data",
                  "inicio", "fim", "status", "justificativa", "criado_por"]

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Agendamentos")
todos = carregar(listar)

if todos.empty:
    st.info("Nenhum agendamento cadastrado.")
    st.stop()

df = todos
c1, c2, c3 = st.columns(3)
with c1: status = st.multiselect("Status", sorted(df["status"].astype(str).unique()))
with c2: sala = st.multiselect("Sala", sorted(df["sala"].astype(str).unique()))
with c3: busca = st.text_input("Pesquisar professor/disciplina")

if status: df = df[df["status"].isin(status)]
if sala: df = df[df["sala"].isin(sala)]
if busca:
    df = df[df["professor"].astype(str).str.contains(busca, case=False, na=False)
            | df["disciplina"].astype(str).str.contains(busca, case=False, na=False)]

st.dataframe(df[COLUNAS_TABELA], use_container_width=True, hide_index=True)

if somente_admin():
    st.subheader("Aprovação de reservas")
    # usa a lista COMPLETA (não a filtrada), para não esconder reservas do admin
    rotulos = {r["id"]: f"{r['professor']} · {r['sala']} · {r['data']} {r['inicio']}-{r['fim']} · {r['status']}"
               for _, r in todos.iterrows()}
    rid = st.selectbox("Reserva", list(rotulos), format_func=lambda i: rotulos[i])
    novo = st.selectbox("Novo status", ["Confirmada", "Reprovada", "Pendente", "Cancelada"])
    if st.button("Atualizar status", type="primary"):
        try:
            alterar_status(rid, novo, usuario_atual()["email"])
            st.success("Status atualizado.")
            st.rerun()
        except ConflitoHorario as e:
            st.error(f"Não é possível {novo.lower()}: conflito de horário. {e}")
        except ValueError as e:
            st.error(str(e))
        except FirestoreError as e:
            st.error(f"Falha ao atualizar no Firestore: {e}")
