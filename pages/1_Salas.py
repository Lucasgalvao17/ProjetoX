import streamlit as st
from controllers.sala_controller import listar, cadastrar, atualizar, excluir
from utils.auth import usuario_logado, exigir_admin
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar, avisar

TIPOS = ["Teórica", "Laboratório de Informática", "Auditório", "Prática"]
SIM_NAO = ["Sim", "Não"]


def _i(opcoes, valor):
    return opcoes.index(valor) if valor in opcoes else 0


def _n(valor, padrao, minimo, maximo):
    """Valor inicial do campo numérico, sempre dentro do intervalo aceito (dados antigos podem fugir dele)."""
    try:
        v = int(float(valor))
    except (TypeError, ValueError):
        v = padrao
    return max(minimo, min(maximo, v))


configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()
exigir_admin()

st.title("Cadastro e gerenciamento de salas")
st.caption("Gerencie capacidade, localização, equipamentos e acessibilidade.")

df = carregar(listar)
aba_lista, aba_nova, aba_editar, aba_excluir = st.tabs(
    [f"Salas cadastradas ({len(df)})", "Cadastrar sala", "Editar sala", "Excluir sala"])

with aba_lista:
    st.dataframe(df, use_container_width=True, hide_index=True)

with aba_nova:
    with st.form("sala_form"):
        st.subheader("Dados da sala")
        c1,c2 = st.columns(2)
        with c1:
            sala=st.text_input("Nome da sala")
            capacidade=st.number_input("Capacidade",1,500,40)
            tipo=st.selectbox("Tipo",TIPOS)
            campus=st.text_input("Campus","Campus Central")
            predio=st.text_input("Prédio","Prédio A")
            numero=st.text_input("Número","105")
        with c2:
            andar=st.number_input("Andar",0,30,1)
            computadores=st.number_input("Computadores",0,500,40)
            projetor=st.selectbox("Projetor",SIM_NAO)
            ar=st.selectbox("Ar-condicionado",SIM_NAO)
            acess=st.selectbox("Acessibilidade",SIM_NAO)
            obs=st.text_area("Observações")
        if st.form_submit_button("Cadastrar sala", type="primary"):
            try:
                cadastrar({"sala":sala,"capacidade":capacidade,"tipo":tipo,"campus":campus,"predio":predio,"andar":andar,"numero":numero,"computadores":computadores,"projetor":projetor,"ar_condicionado":ar,"acessibilidade":acess,"observacoes":obs})
                avisar("success", "Sala cadastrada.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            except FirestoreError as e:
                st.error(f"Falha ao salvar no Firestore: {e}")

with aba_editar:
    if df.empty:
        st.info("Nenhuma sala cadastrada para editar.")
    else:
        rotulos = dict(zip(df["id"], df["sala"].astype(str)))
        sid = st.selectbox("Sala para editar", df["id"].tolist(), format_func=lambda i: rotulos.get(i, i), key="editar_sala_sel")
        atual = df[df["id"] == sid].iloc[0]
        k = lambda campo: f"ed_{campo}_{sid}"      # a chave inclui o ID: ao trocar de sala, o formulário recarrega os valores dela
        with st.form(f"form_editar_{sid}"):
            e1, e2 = st.columns(2)
            with e1:
                n_sala = st.text_input("Nome da sala", str(atual["sala"]), key=k("sala"))
                n_cap = st.number_input("Capacidade", 1, 500, _n(atual["capacidade"], 40, 1, 500), key=k("capacidade"))
                n_tipo = st.selectbox("Tipo", TIPOS, index=_i(TIPOS, atual["tipo"]), key=k("tipo"))
                n_campus = st.text_input("Campus", str(atual["campus"]), key=k("campus"))
                n_predio = st.text_input("Prédio", str(atual["predio"]), key=k("predio"))
                n_numero = st.text_input("Número", str(atual["numero"]), key=k("numero"))
            with e2:
                n_andar = st.number_input("Andar", 0, 30, _n(atual["andar"], 0, 0, 30), key=k("andar"))
                n_pcs = st.number_input("Computadores", 0, 500, _n(atual["computadores"], 0, 0, 500), key=k("computadores"))
                n_proj = st.selectbox("Projetor", SIM_NAO, index=_i(SIM_NAO, atual["projetor"]), key=k("projetor"))
                n_ar = st.selectbox("Ar-condicionado", SIM_NAO, index=_i(SIM_NAO, atual["ar_condicionado"]), key=k("ar"))
                n_acess = st.selectbox("Acessibilidade", SIM_NAO, index=_i(SIM_NAO, atual["acessibilidade"]), key=k("acess"))
                n_obs = st.text_area("Observações", str(atual["observacoes"]), key=k("obs"))
            if st.form_submit_button("Salvar alterações", type="primary"):
                try:
                    renomeadas = atualizar(sid, {"sala": n_sala, "capacidade": n_cap, "tipo": n_tipo, "campus": n_campus,
                                                 "predio": n_predio, "andar": n_andar, "numero": n_numero,
                                                 "computadores": n_pcs, "projetor": n_proj, "ar_condicionado": n_ar,
                                                 "acessibilidade": n_acess, "observacoes": n_obs})
                    extra = f" {renomeadas} reserva(s) foram atualizadas com o novo nome." if renomeadas else ""
                    avisar("success", f"Sala atualizada.{extra}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except FirestoreError as e:
                    st.error(f"Falha ao salvar no Firestore: {e}")

with aba_excluir:
    if df.empty:
        st.info("Nenhuma sala cadastrada.")
    else:
        rotulos = dict(zip(df["id"], df["sala"].astype(str)))
        id_excluir = st.selectbox("Sala para excluir", df["id"].tolist(), format_func=lambda i: rotulos.get(i, i))
        st.warning("A exclusão é permanente. Salas com reservas pendentes ou aprovadas não podem ser excluídas.")
        confirmado = st.checkbox("Confirmo que quero excluir esta sala", key=f"sala_del_ok_{id_excluir}")
        if st.button("Excluir sala", disabled=not confirmado):
            if not confirmado:
                st.error("Marque a caixa de confirmação para excluir.")
            else:
                try:
                    excluir(id_excluir)
                    avisar("success", "Sala excluída.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except FirestoreError as e:
                    st.error(f"Falha ao excluir no Firestore: {e}")
