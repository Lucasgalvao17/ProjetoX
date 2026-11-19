import json
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import requests
import google.auth.transport.requests
from google.oauth2 import service_account

COLLECTION_NAME = "reservas"
SCOPES = ["https://www.googleapis.com/auth/datastore"]


@st.cache_resource
def get_rest_context():
    with open("utils/serviceAccountKey.json", "r", encoding="utf-8") as f:
        info = json.load(f)

    if "private_key" in info and isinstance(info["private_key"], str):
        info["private_key"] = info["private_key"].replace("\\n", "\n")

    cred = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    project_id = info["project_id"]
    client_email = info.get("client_email", "")
    base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
    return cred, base_url, project_id, client_email


def _headers(cred):
    if not cred.valid or cred.expired:
        cred.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {cred.token}",
        "Content-Type": "application/json",
    }


def _to_firestore_value(v):
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, int):
        return {"integerValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    return {"stringValue": str(v)}


def _from_firestore_value(val):
    if not isinstance(val, dict):
        return val
    if "stringValue" in val:
        return val["stringValue"]
    if "integerValue" in val:
        return int(val["integerValue"])
    if "doubleValue" in val:
        return float(val["doubleValue"])
    if "booleanValue" in val:
        return bool(val["booleanValue"])
    return str(val)


def _doc_to_dict(doc):
    out = {}
    fields = doc.get("fields", {})
    for k, v in fields.items():
        out[k] = _from_firestore_value(v)
    name = doc.get("name", "")
    if "/" in name:
        out["id"] = name.split("/")[-1]
    return out


def _detalhe_erro(e):
    try:
        _, _, pid, email = get_rest_context()
        utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"{type(e).__name__}: {e} | project={pid} | email={email} | {utc_now}"
    except Exception:
        return f"{type(e).__name__}: {e}"


def listar():
    colunas = [
        "id", "professor", "disciplina", "sala", "tipo_aula",
        "alunos", "data", "inicio", "fim", "status", "justificativa", "criado_por"
    ]
    try:
        cred, base_url, _, _ = get_rest_context()
        url = f"{base_url}/{COLLECTION_NAME}"
        resp = requests.get(url, headers=_headers(cred), timeout=10)
        resp.raise_for_status()

        payload = resp.json()
        docs = payload.get("documents", [])
        dados = [_doc_to_dict(d) for d in docs]

        if not dados:
            return pd.DataFrame(columns=colunas)

        return pd.DataFrame(dados)
    except Exception as e:
        st.error(f"Erro em listar() via REST: {_detalhe_erro(e)}")
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
    cred, base_url, _, _ = get_rest_context()
    url = f"{base_url}/{COLLECTION_NAME}"
    body = {"fields": {k: _to_firestore_value(v) for k, v in dados.items()}}
    resp = requests.post(url, headers=_headers(cred), json=body, timeout=10)
    resp.raise_for_status()
    created = resp.json()
    name = created.get("name", "")
    return name.split("/")[-1] if "/" in name else ""


def alterar_status(id_reserva, status):
    cred, base_url, _, _ = get_rest_context()
    url = f"{base_url}/{COLLECTION_NAME}/{id_reserva}?updateMask.fieldPaths=status"
    body = {"fields": {"status": _to_firestore_value(status)}}
    resp = requests.patch(url, headers=_headers(cred), json=body, timeout=10)
    resp.raise_for_status()


def pd_to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)
