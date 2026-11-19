import streamlit as st
from utils.firebase_utils import inicializar_firebase
from datetime import datetime
import pandas as pd

COLLECTION_NAME = "reservas"


@st.cache_resource
def get_db():
    return inicializar_firebase()


def listar():
    colunas = [
        "id", "professor", "disciplina", "sala", "tipo_aula",
        "alunos", "data", "inicio", "fim", "status", "justificativa", "criado_por"
    ]
    try:
        db = get_db()
        # Usa .get() em vez de .stream() com timeout explícito
        docs = db.collection(COLLECTION_NAME).get(timeout=8)
        dados = []
        for doc in docs:
            d = doc.to_dict() or {}
            d["id"] = doc.id
            dados.append(d)

        if not dados:
            return pd.DataFrame(columns=colunas)

        return pd.DataFrame(dados)
    except Exception as e:
        st.error(f"Erro em listar() no Firestore: {type(e).__name__} - {e}")
        return pd.DataFrame(columns=colunas)


def conflitos(sala, data, inicio, fim, ignorar_id=None):
    df = listar()
    if df.empty or "sala" not in df.columns:
        return pd.DataFrame()

    df = df[
        (df["sala"].astype(str) == str(sala)) &
        (df["data"].astype(str) == str(data)) &
        (df["status"].isin(["Pendente", "Confirmada"]))
    ]

    if ignorar_id is not None and "id" in df.columns:
        df = df[df["id"].astype(str) != str(ignorar_id)]

    if df.empty:
        return pd.DataFrame()

    ini_obj = datetime.strptime(str(inicio), "%H:%M").time()
    fim_obj = datetime.strptime(str(fim), "%H:%M").time()

    mask = []
    for _, r in df.iterrows():
        try:
            r_ini = datetime.strptime(str(r["inicio"]), "%H:%M").time()
            r_end = datetime.strptime(str(r["fim"]), "%H:%M").time()
            tem_conflito = (ini_obj < r_end) and (fim_obj > r_ini)
            mask.append(tem_conflito)
        except Exception:
            mask.append(False)

    return df[mask]


def horario_disponivel(sala, data, inicio, fim):
    conflitantes = conflitos(sala, data, inicio, fim)
    return conflitantes.empty


def criar(dados):
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document()
    doc_ref.set(dados, timeout=8)
    return doc_ref.id


def alterar_status(id_reserva, status):
    db = get_db()
    doc_ref = db.collection(COLLECTION_NAME).document(str(id_reserva))
    doc_ref.update({"status": status}, timeout=8)


def pd_to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)
