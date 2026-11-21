import streamlit as st
from controllers import usuario_controller as uc
from utils.auth import usuario_logado, usuario_atual, exigir_admin, cadastrar_usuario
from utils.firestore_client import FirestoreError
from views.layout import configurar_pagina, menu_lateral, carregar, avisar

configurar_pagina()
if not usuario_logado(): st.switch_page("pages/0_Login.py")
menu_lateral()
exigir_admin()

eu = usuario_atual()
st.title("Usuários")
st.caption("Todos os usuários ficam no Firestore. As senhas são guardadas só como hash seguro (nunca em texto).")

df = carregar(uc.listar)
rotulos = {r["id"]: f"{r['nome']} ({r['email']}) · {r['perfil']}" for _, r in df.iterrows()}

aba_lista, aba_novo, aba_editar, aba_senha = st.tabs(
    [f"Usuários ({len(df)})", "Novo usuário", "Editar / ativar", "Redefinir senha"])


def tentar(acao, sucesso):
    try:
        acao()
        avisar("success", sucesso)
        st.rerun()
    except ValueError as e:
        st.error(str(e))
    except FirestoreError as e:
        st.error(f"Falha ao salvar no Firestore: {e}")


with aba_lista:
    st.dataframe(df, use_container_width=True, hide_index=True)

with aba_novo:
    n_nome = st.text_input("Nome completo", key="novo_nome")
    n_email = st.text_input("E-mail", key="novo_email")
    n_perfil = st.selectbox("Perfil", list(uc.PERFIS), index=list(uc.PERFIS).index("Professor"), key="novo_perfil")
    n_senha = st.text_input("Senha inicial", type="password", key="novo_senha")
    n_senha2 = st.text_input("Confirmar senha", type="password", key="novo_senha2")
    if st.button("Criar usuário", type="primary", key="btn_criar_usuario"):
        if n_senha != n_senha2:
            st.error("As senhas não coincidem.")
        else:
            try:
                ok, msg = cadastrar_usuario(n_nome, n_email, n_senha, n_perfil)
            except FirestoreError as e:
                ok, msg = False, f"Falha ao salvar no Firestore: {e}"
            if ok:
                avisar("success", f"Usuário criado: {n_email.strip().lower()}")
                st.rerun()
            else:
                st.error(msg)

with aba_editar:
    if df.empty:
        st.info("Nenhum usuário.")
    else:
        uid = st.selectbox("Usuário", list(rotulos), format_func=lambda i: rotulos[i], key="edit_uid")
        alvo = df[df["id"] == uid].iloc[0]
        perfis = list(uc.PERFIS)
        e_nome = st.text_input("Nome", str(alvo["nome"]), key=f"edit_nome_{uid}")
        e_perfil = st.selectbox("Perfil", perfis, index=perfis.index(alvo["perfil"]) if alvo["perfil"] in perfis else 0,
                                key=f"edit_perfil_{uid}")
        if st.button("Salvar nome e perfil", type="primary", key="btn_salvar_usuario"):
            tentar(lambda: uc.atualizar(uid, e_nome, e_perfil, executor_id=eu["id"]), "Usuário atualizado.")
        st.divider()
        ativo_atual = str(alvo["ativo"])
        st.write(f"Situação atual: **{'Ativo' if ativo_atual == 'Sim' else 'Desativado'}** "
                 "(usuário desativado não consegue entrar, mas o cadastro e o histórico são mantidos).")
        novo_ativo = "Não" if ativo_atual == "Sim" else "Sim"
        if st.button("Desativar usuário" if novo_ativo == "Não" else "Reativar usuário", key="btn_alternar_ativo"):
            tentar(lambda: uc.definir_ativo(uid, novo_ativo, executor_id=eu["id"]),
                   "Usuário desativado." if novo_ativo == "Não" else "Usuário reativado.")

with aba_senha:
    if df.empty:
        st.info("Nenhum usuário.")
    else:
        uid_s = st.selectbox("Usuário", list(rotulos), format_func=lambda i: rotulos[i], key="senha_uid")
        s_nova = st.text_input("Nova senha", type="password", key="senha_nova")
        s_nova2 = st.text_input("Confirmar nova senha", type="password", key="senha_nova2")
        st.caption(f"Mínimo de {uc.MIN_SENHA} caracteres. Informe a nova senha ao usuário por um canal seguro.")
        if st.button("Redefinir senha", type="primary", key="btn_redefinir_senha"):
            if s_nova != s_nova2:
                st.error("As senhas não coincidem.")
            else:
                tentar(lambda: uc.redefinir_senha(uid_s, s_nova, eu["email"]), "Senha redefinida.")
