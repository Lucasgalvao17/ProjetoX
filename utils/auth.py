import hashlib
import streamlit as st
from models.csv_repository import ler_csv, adicionar_linha

COLS = ["id","nome","email","senha","perfil","ativo"]

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def garantir_admin():
    df = ler_csv("usuarios.csv", COLS)
    if df.empty:
        adicionar_linha("usuarios.csv", {
            "id": 1,
            "nome": "Administrador",
            "email": "admin@atila.local",
            "senha": hash_senha("admin123"),
            "perfil": "Administrador",
            "ativo": "Sim"
        }, COLS)

def login(email, senha):
    garantir_admin()
    df = ler_csv("usuarios.csv", COLS)
    if df.empty:
        return False
    encontrado = df[(df["email"].astype(str).str.lower() == email.strip().lower()) &
                    (df["senha"] == hash_senha(senha)) &
                    (df["ativo"].astype(str) == "Sim")]
    if encontrado.empty:
        return False
    row = encontrado.iloc[0].to_dict()
    st.session_state["usuario"] = {
        "id": int(row["id"]), "nome": row["nome"],
        "email": row["email"], "perfil": row["perfil"]
    }
    return True

def cadastrar_usuario(nome, email, senha, perfil="Professor"):
    garantir_admin()
    df = ler_csv("usuarios.csv", COLS)
    if not email or not senha or not nome:
        return False, "Preencha todos os campos."
    if not df.empty and (df["email"].astype(str).str.lower() == email.strip().lower()).any():
        return False, "Este e-mail já está cadastrado."
    novo_id = 1 if df.empty else int(df["id"].max()) + 1
    adicionar_linha("usuarios.csv", {
        "id": novo_id, "nome": nome.strip(), "email": email.strip().lower(),
        "senha": hash_senha(senha), "perfil": perfil, "ativo": "Sim"
    }, COLS)
    return True, "Conta criada com sucesso."

def usuario_logado():
    return "usuario" in st.session_state

def usuario_atual():
    return st.session_state.get("usuario")

def logout():
    st.session_state.pop("usuario", None)

def somente_admin():
    user = usuario_atual()
    return user and user["perfil"] == "Administrador"
