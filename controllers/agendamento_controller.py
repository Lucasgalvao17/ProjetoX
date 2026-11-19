import json
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import requests

COLLECTION_NAME = "reservas"
DEFAULT_PROJECT_ID = "reserva-salas-bb922"


@st.cache_resource
def get_rest_config():
    api_key = ""
    project_id = DEFAULT_PROJECT_ID

    if "firestore" in st.secrets:
        api_key = str(st.secrets["firestore"].get("api_key", "")).strip()
        project_id = str(st.secrets["firestore"].get("project_id", project_id)).strip()
    elif "firebase_api_key" in st.secrets:
        api_key = str(st.secrets["firebase_api_key"]).strip()

    if not api_key:
        try:
            with open("utils/serviceAccountKey.json", "r", encoding="utf-8") as f:
                info = json.load(f)
            project_id = info.get("project_id") or project_id
            api_key = str(info.get("api_key", "")).strip()
        except Exception:
            pass

    if not api_key:
        raise RuntimeError(
            'api_key não encontrada. Adicione [firestore] api_key = "AIza..." nos Secrets do Streamlit Cloud.'
        )

    base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
    return base_url, api_key, project_id


def _url(path: str = "") -> str:
    base_url, api_key, _ = get_rest_config()
    target = f"{base_url}/{COLLECTION_NAME}" if not path else f"{base_url}/{COLLECTION_NAME}/{path}"
    sep = "&" if "?" in target else "?"
    return f"{target}{sep}key={api_key}"


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
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        _, _, pid = get_rest_config()
        return f"{type(e).__name__}: {e} | project={pid} | {utc_now}"
    except Exception:
        return f"{type(e).__name__}: {e} | {utc_now}"


def listar():
    colunas = [
        "id", "professor", "disciplina", "sala", "tipo_aula",
        "alunos", "data", "inicio", "fim", "status", "justificativa", "criado_por"
    ]
    try:
        resp = requests.get(_url(), timeout=10)
        if resp.status_code >= 400:
            raise RuntimeError(f"Firestore GET HTTP {resp.status_code}: {resp.text}")

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
    body = {"fields": {k: _to_firestore_value(v) for k, v in dados.items()}}
    resp = requests.post(_url(), json=body, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"Firestore POST HTTP {resp.status_code}: {resp.text}")
    created = resp.json()
    name = created.get("name", "")
    return name.split("/")[-1] if "/" in name else ""


def alterar_status(id_reserva, status):
    url = _url(f"{id_reserva}?updateMask.fieldPaths=status")
    body = {"fields": {"status": _to_firestore_value(status)}}
    resp = requests.patch(url, json=body, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"Firestore PATCH HTTP {resp.status_code}: {resp.text}")


def pd_to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)
