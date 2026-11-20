import re

import streamlit as st

from controllers import usuario_controller as uc
from utils.firestore_client import DocumentoJaExiste


def login(email, senha):
    """True se as credenciais forem válidas e o usuário estiver ativo."""
    usuario = uc.obter_por_email(email)
    if not usuario or str(usuario.get("ativo")) != "Sim":
        return False
    if not uc.verificar_senha(senha, usuario.get("senha")):
        return False
    if uc.hash_legado(usuario.get("senha")):      # migra SHA-256 puro -> PBKDF2 com sal
        uc.definir_senha(usuario["id"], uc.gerar_hash(senha))
    st.session_state["usuario"] = {
        "id": usuario["id"], "nome": usuario.get("nome", ""),
        "email": usuario.get("email", ""), "perfil": usuario.get("perfil", "Professor"),
    }
    return True


def cadastrar_usuario(nome, email, senha, perfil="Professor"):
    if not (nome or "").strip() or not (email or "").strip() or not senha:
        return False, "Preencha todos os campos."
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
        return False, "Informe um e-mail válido."
    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."
    if perfil not in uc.PERFIS:
        return False, "Perfil inválido."
    try:
        uc.criar(nome, email, uc.gerar_hash(senha), perfil)
    except DocumentoJaExiste:
        return False, "Este e-mail já está cadastrado."
    return True, "Conta criada com sucesso."


def alterar_senha(uid, senha_atual, nova_senha):
    usuario = uc.obter(uid)
    if not usuario or not uc.verificar_senha(senha_atual, usuario.get("senha")):
        return False, "Senha atual incorreta."
    if len(nova_senha) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres."
    uc.definir_senha(uid, uc.gerar_hash(nova_senha))
    return True, "Senha alterada com sucesso."


def usuario_logado():
    return "usuario" in st.session_state


def usuario_atual():
    return st.session_state.get("usuario")


def logout():
    st.session_state.pop("usuario", None)


def somente_admin():
    user = usuario_atual()
    return bool(user and user["perfil"] == "Administrador")
