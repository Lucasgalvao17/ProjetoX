import streamlit as st
from controllers.sala_controller import listar, cadastrar, excluir
from utils.auth import usuario_logado, somente_admin
from views.layout import configurar_pagina, menu_lateral

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()

st.title("Cadastro e gerenciamento de salas")
st.caption("Gerencie capacidade, localização, equipamentos e acessibilidade.")

if somente_admin():
    with st.form("sala_form"):
        st.subheader("Dados da sala")
        c1,c2 = st.columns(2)
        with c1:
            sala=st.text_input("Nome da sala")
            capacidade=st.number_input("Capacidade",1,500,40)
            tipo=st.selectbox("Tipo",["Teórica","Laboratório de Informática","Auditório","Prática"])
            campus=st.text_input("Campus","Campus Central")
            predio=st.text_input("Prédio","Prédio A")
            numero=st.text_input("Número","105")
        with c2:
            andar=st.number_input("Andar",0,30,1)
            computadores=st.number_input("Computadores",0,500,40)
            projetor=st.selectbox("Projetor",["Sim","Não"])
            ar=st.selectbox("Ar-condicionado",["Sim","Não"])
            acess=st.selectbox("Acessibilidade",["Sim","Não"])
            obs=st.text_area("Observações")
        if st.form_submit_button("Cadastrar sala", type="primary"):
            if not sala.strip():
                st.error("Informe o nome da sala.")
            else:
                cadastrar({"sala":sala,"capacidade":capacidade,"tipo":tipo,"campus":campus,"predio":predio,"andar":andar,"numero":numero,"computadores":computadores,"projetor":projetor,"ar_condicionado":ar,"acessibilidade":acess,"observacoes":obs})
                st.success("Sala cadastrada.")
                st.rerun()
else:
    st.info("Somente administradores podem cadastrar ou excluir salas.")

st.subheader("Salas cadastradas")
df=listar()
st.dataframe(df,use_container_width=True,hide_index=True)

if somente_admin() and not df.empty:
    id_excluir=st.selectbox("ID da sala para excluir",df["id"].tolist())
    if st.button("Excluir sala"):
        excluir(id_excluir); st.success("Sala excluída."); st.rerun()
