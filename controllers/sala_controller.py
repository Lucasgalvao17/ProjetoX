import json
import pandas as pd
import requests
import streamlit as st

COLLECTION_NAME = "salas"
DEFAULT_PROJECT_ID = "reserva-salas-bb922"

COLS = [
    "id",
    "sala",
    "capacidade",
    "tipo",
    "campus",
    "predio",
    "andar",
    "numero",
    "computadores",
    "projetor",
    "ar_condicionado",
    "acessibilidade",
    "observacoes",
]


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
    for k, v in doc.get("fields", {}).items():
        out[k] = _from_firestore_value(v)
    name = doc.get("name", "")
    if "/" in name:
        out["id"] = name.split("/")[-1]
    return out


def listar():
    try:
        resp = requests.get(_url(), timeout=10)
        if resp.status_code >= 400:
            raise RuntimeError(f"Firestore GET HTTP {resp.status_code}: {resp.text}")
        docs = resp.json().get("documents", [])
        dados = [_doc_to_dict(d) for d in docs]
        if not dados:
            return pd.DataFrame(columns=COLS)
        df = pd.DataFrame(dados)
        for col in COLS:
            if col not in df.columns:
                df[col] = ""
        return df[COLS]
    except Exception as e:
        st.error(f"Erro ao listar salas no Firestore: {e}")
        return pd.DataFrame(columns=COLS)


def cadastrar(dados: dict):
    df = listar()
    novo_id = 1 if df.empty else int(pd.to_numeric(df["id"], errors="coerce").fillna(0).max()) + 1
    payload = {"id": novo_id, **dados}
    body = {"fields": {k: _to_firestore_value(v) for k, v in payload.items()}}
    resp = requests.post(_url(), json=body, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"Firestore POST HTTP {resp.status_code}: {resp.text}")
    return novo_id


def excluir(id_sala):
    resp = requests.get(_url(), timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"Firestore GET HTTP {resp.status_code}: {resp.text}")
    docs = resp.json().get("documents", [])
    for doc in docs:
        doc_path = doc.get("name", "")
        doc_id = doc_path.split("/")[-1] if "/" in doc_path else ""
        campos = _doc_to_dict(doc)
        if str(campos.get("id", "")) == str(id_sala) or str(doc_id) == str(id_sala):
            del_resp = requests.delete(_url(doc_id), timeout=10)
            if del_resp.status_code >= 400:
                raise RuntimeError(f"Firestore DELETE HTTP {del_resp.status_code}: {del_resp.text}")
