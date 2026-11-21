import streamlit as st
from controllers import disciplina_controller as dc
from utils.auth import usuario_logado, exigir_admin
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar, avisar

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()
exigir_admin()

st.title("Disciplinas")
st.caption("Estas disciplinas aparecem como lista de seleção na Nova Reserva. "
           "Cada código e cada nome só podem existir uma vez (evita duplicatas por erro de digitação).")

df = carregar(dc.listar)
aba_lista, aba_nova, aba_editar = st.tabs([f"Disciplinas ({len(df)})", "Cadastrar disciplina", "Editar / ativar"])

with aba_lista:
    st.dataframe(df, use_container_width=True, hide_index=True)

with aba_nova:
    with st.form("disciplina"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome da disciplina")
        codigo = c2.text_input("Código")
        curso = st.text_input("Curso")
        if st.form_submit_button("Cadastrar disciplina", type="primary"):
            try:
                dc.cadastrar(nome, codigo, curso)
                avisar("success", "Disciplina cadastrada.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            except FirestoreError as e:
                st.error(f"Falha ao salvar no Firestore: {e}")

with aba_editar:
    if df.empty:
        st.info("Nenhuma disciplina cadastrada.")
    else:
        rotulos = {r["id"]: f"{dc.rotulo(r)}{'' if r['ativa'] == 'Sim' else '  (inativa)'}" for _, r in df.iterrows()}
        did = st.selectbox("Disciplina", list(rotulos), format_func=lambda i: rotulos[i], key="disc_edit_sel")
        atual = df[df["id"] == did].iloc[0]
        with st.form(f"form_disc_{did}"):
            e_nome = st.text_input("Nome", str(atual["nome"]), key=f"disc_nome_{did}")
            e_curso = st.text_input("Curso", str(atual["curso"]), key=f"disc_curso_{did}")
            e_ativa = st.selectbox("Ativa (aparece na Nova Reserva)", ["Sim", "Não"],
                                   index=0 if atual["ativa"] == "Sim" else 1, key=f"disc_ativa_{did}")
            st.caption("O código não pode ser alterado. Reservas já feitas mantêm o nome da época.")
            if st.form_submit_button("Salvar alterações", type="primary"):
                try:
                    dc.atualizar(did, e_nome, e_curso, e_ativa)
                    avisar("success", "Disciplina atualizada.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except FirestoreError as e:
                    st.error(f"Falha ao salvar no Firestore: {e}")
