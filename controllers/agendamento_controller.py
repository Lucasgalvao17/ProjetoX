import base64
import json
import re
import time
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

COLLECTION_NAME = "reservas"
TOKEN_URI_DEFAULT = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/datastore"

_TOKEN_CACHE = {"token": None, "exp": 0.0}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _normalizar_chave_pem(raw_key: str) -> str:
    key = raw_key.replace("\\n", "\n").replace("\r\n", "\n").strip()
    match = re.search(
        r"(-----BEGIN [A-Z0-9 ]+-----)(.+?)(-----END [A-Z0-9 ]+-----)",
        key,
        flags=re.DOTALL,
    )
    if not match:
        return key
    header, body, footer = match.groups()
    clean_body = re.sub(r"\s+", "", body)
    wrapped = "\n".join(clean_body[i : i + 64] for i in range(0, len(clean_body), 64))
    return f"{header}\n{wrapped}\n{footer}\n"


@st.cache_resource
def get_rest_context():
    with open("utils/serviceAccountKey.json", "r", encoding="utf-8") as f:
        info = json.load(f)

    project_id = info["project_id"]
    client_email = info["client_email"]
    token_uri = info.get("token_uri") or TOKEN_URI_DEFAULT
    private_key_pem = _normalizar_chave_pem(info["private_key"])

    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
    )
    base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
    return private_key, client_email, token_uri, base_url, project_id


def _obter_access_token() -> str:
    now = time.time()
    if _TOKEN_CACHE["token"] and now < (_TOKEN_CACHE["exp"] - 60):
        return _TOKEN_CACHE["token"]

    private_key, client_email, token_uri, _, _ = get_rest_context()
    iat = int(now)
    exp = iat + 3600

    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": client_email,
        "sub": client_email,
        "aud": token_uri,
        "iat": iat,
        "exp": exp,
        "scope": SCOPE,
    }

    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))}.{_b64url(json.dumps(payload, separators=(',', ':')).encode('utf-8'))}".encode("ascii")
    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    assertion = f"{signing_input.decode('ascii')}.{_b64url(signature)}"

    resp = requests.post(
        token_uri,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"OAuth HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    access_token = data["access_token"]
    expires_in = int(data.get("expires_in", 3600))
    _TOKEN_CACHE["token"] = access_token
    _TOKEN_CACHE["exp"] = now + expires_in
    return access_token


def _headers() -> dict:
    token = _obter_access_token()
    return {
        "Authorization": f"Bearer {token}",
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
        _, email, _, _, pid = get_rest_context()
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
        _, _, _, base_url, _ = get_rest_context()
        url = f"{base_url}/{COLLECTION_NAME}"
        resp = requests.get(url, headers=_headers(), timeout=10)
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
    _, _, _, base_url, _ = get_rest_context()
    url = f"{base_url}/{COLLECTION_NAME}"
    body = {"fields": {k: _to_firestore_value(v) for k, v in dados.items()}}
    resp = requests.post(url, headers=_headers(), json=body, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"Firestore POST HTTP {resp.status_code}: {resp.text}")
    created = resp.json()
    name = created.get("name", "")
    return name.split("/")[-1] if "/" in name else ""


def alterar_status(id_reserva, status):
    _, _, _, base_url, _ = get_rest_context()
    url = f"{base_url}/{COLLECTION_NAME}/{id_reserva}?updateMask.fieldPaths=status"
    body = {"fields": {"status": _to_firestore_value(status)}}
    resp = requests.patch(url, headers=_headers(), json=body, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"Firestore PATCH HTTP {resp.status_code}: {resp.text}")


def pd_to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)
