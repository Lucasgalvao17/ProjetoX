"""
Cliente REST único do Cloud Firestore para todo o ATILA.

TODAS as telas (Dashboard, Salas, Agendamentos, Usuários, Disciplinas...)
leem e gravam por este módulo, então não existe mais "uma fonte para o
Dashboard e outra para as abas".

Modos de conexão (escolhidos nesta ordem):
  1. emulador        -> variável de ambiente FIRESTORE_EMULATOR_HOST (dev/testes)
  2. service_account -> [gcp_service_account] nos secrets   (RECOMENDADO)
  3. api_key         -> [firestore] api_key nos secrets      (legado; exige
                        regras do Firestore abertas ao público — evite)

Não há cache de dados: cada chamada vai ao Firestore, então o que foi gravado
numa aba aparece imediatamente nas demais.
"""
from __future__ import annotations

import numbers
import os
import re
from dataclasses import dataclass
from urllib.parse import quote

import requests
import streamlit as st

DEFAULT_PROJECT_ID = "reserva-salas-bb922"
ESCOPO = "https://www.googleapis.com/auth/datastore"
TAMANHO_PAGINA = 300   # máximo aceito pela API REST (o padrão dela é só 20!)
TIMEOUT = 15


class FirestoreError(RuntimeError):
    """Erro ao falar com o Firestore (mensagem já pronta para o usuário)."""


class DocumentoJaExiste(FirestoreError):
    pass


class DocumentoNaoEncontrado(FirestoreError):
    pass


@dataclass(frozen=True)
class _Conexao:
    sessao: object
    base_url: str
    cabecalhos: dict
    modo: str
    project_id: str


def _secret(nome):
    try:
        if nome in st.secrets:
            return st.secrets[nome]
    except Exception:  # sem secrets.toml
        pass
    return None


def _base_url(project_id: str, host: str = "firestore.googleapis.com", https: bool = True) -> str:
    esquema = "https" if https else "http"
    return f"{esquema}://{host}/v1/projects/{project_id}/databases/(default)/documents"


@st.cache_resource(show_spinner=False)
def _conexao() -> _Conexao:
    cfg = _secret("firestore") or {}
    project_id = str(cfg.get("project_id", "") or DEFAULT_PROJECT_ID).strip()

    emulador = os.environ.get("FIRESTORE_EMULATOR_HOST", "").strip()
    if emulador:
        return _Conexao(requests.Session(), _base_url(project_id, emulador, https=False), {}, "emulador", project_id)

    conta = _secret("gcp_service_account")
    if conta:
        try:
            from google.auth.transport.requests import AuthorizedSession
            from google.oauth2 import service_account
        except ImportError as exc:
            raise FirestoreError("Dependência ausente: adicione 'google-auth' ao requirements.txt.") from exc
        info = dict(conta)
        info["private_key"] = normalizar_chave_privada(info.get("private_key", ""))
        problemas = problemas_conta(info)
        if problemas:
            raise FirestoreError("[gcp_service_account] com problema — " + "; ".join(problemas) + ".")
        try:
            credenciais = service_account.Credentials.from_service_account_info(info, scopes=[ESCOPO])
        except Exception as exc:
            # a mensagem do google-auth/cryptography não contém o conteúdo da chave
            raise FirestoreError(
                f"[gcp_service_account] rejeitado pelo google-auth ({type(exc).__name__}: {str(exc)[:200]})"
            ) from None
        project_id = str(info.get("project_id") or project_id)
        return _Conexao(AuthorizedSession(credenciais), _base_url(project_id), {}, "service_account", project_id)

    api_key = str(cfg.get("api_key", "") or _secret("firebase_api_key") or "").strip()
    if api_key:
        # Chave no header (e não na URL) para não vazar em mensagens de erro/logs.
        return _Conexao(requests.Session(), _base_url(project_id), {"X-Goog-Api-Key": api_key}, "api_key", project_id)

    raise FirestoreError(
        "Credenciais do Firestore não configuradas. Adicione [gcp_service_account] "
        "nos Secrets do Streamlit (veja .streamlit/secrets.toml.example)."
    )


CAMPOS_CONTA = ("type", "project_id", "private_key_id", "private_key", "client_email", "token_uri")


def normalizar_chave_privada(texto) -> str:
    """Reconstrói o PEM mesmo que a colagem nos Secrets tenha estragado as quebras de linha
    (\\n literais, \\\\n duplos, espaços no lugar de quebras, aspas sobrando, CRLF)."""
    t = str(texto or "").strip().strip("\"'")
    t = re.sub(r"\\+r", "", t)
    t = re.sub(r"\\+n", "\n", t).replace("\r", "")
    m = re.search(r"-----BEGIN ([A-Z ]*PRIVATE KEY)-----(.*?)-----END \1-----", t, re.S)
    if not m:
        return t
    corpo = re.sub(r"[^A-Za-z0-9+/=]", "", m.group(2))
    linhas = [corpo[i:i + 64] for i in range(0, len(corpo), 64)]
    return f"-----BEGIN {m.group(1)}-----\n" + "\n".join(linhas) + f"\n-----END {m.group(1)}-----\n"


def problemas_conta(info: dict) -> list[str]:
    """Lista o que está errado em [gcp_service_account], SEM revelar valores secretos."""
    achados = []
    faltando = [c for c in CAMPOS_CONTA if not str(info.get(c, "")).strip()]
    if faltando:
        achados.append("campos ausentes ou vazios: " + ", ".join(faltando))
    if info.get("type") and info.get("type") != "service_account":
        achados.append("'type' deve ser exatamente service_account")
    if info.get("client_email") and "@" not in str(info["client_email"]):
        achados.append("'client_email' não parece um e-mail")
    if info.get("token_uri") and not str(info["token_uri"]).startswith("https://"):
        achados.append("'token_uri' deve começar com https://")
    chave = str(info.get("private_key", ""))
    if chave.strip():
        m = re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY-----(.*?)-----END [A-Z ]*PRIVATE KEY-----", chave, re.S)
        if not m:
            achados.append("'private_key' sem a linha BEGIN/END PRIVATE KEY (colagem cortada?)")
        else:
            corpo = re.sub(r"[^A-Za-z0-9+/=]", "", m.group(1))
            if len(corpo) % 4 != 0 or len(corpo) < 1000:
                achados.append(f"'private_key' parece truncada/alterada (corpo com {len(corpo)} caracteres; "
                               "uma chave RSA-2048 tem ~1600)")
    return achados


def modo_conexao() -> str:
    return _conexao().modo


def project_id() -> str:
    return _conexao().project_id


# --------------------------------------------------------------------------
# Conversão de valores
# --------------------------------------------------------------------------
def para_valor(v):
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):  # numpy -> python
        try:
            v = v.item()
        except Exception:
            pass
    if v is None:
        return {"nullValue": None}
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, numbers.Integral):
        return {"integerValue": str(int(v))}
    if isinstance(v, numbers.Real):
        return {"doubleValue": float(v)}
    return {"stringValue": str(v)}


def de_valor(val):
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
    if "nullValue" in val:
        return ""
    if "timestampValue" in val:
        return val["timestampValue"]
    return str(val)


def normalizar_timestamp(ts: str) -> str:
    """O Firestore devolve frações de tamanho variável (.5Z, .123456Z). Padroniza em 9 dígitos
    para que a ordenação como texto seja cronologicamente correta."""
    base, _, fracao = str(ts).rstrip("Z").partition(".")
    return f"{base}.{fracao.ljust(9, '0')[:9]}Z"


def doc_para_dict(doc: dict) -> dict:
    """Documento REST -> dict. 'id' é SEMPRE o ID do documento no Firestore."""
    out = {k: de_valor(v) for k, v in doc.get("fields", {}).items()}
    nome = doc.get("name", "")
    if "/" in nome:
        out["id"] = nome.rsplit("/", 1)[-1]
    if not out.get("criado_em") and doc.get("createTime"):
        out["criado_em"] = normalizar_timestamp(doc["createTime"])
    return out


# --------------------------------------------------------------------------
# Requisição
# --------------------------------------------------------------------------
def _mensagem_http(resp) -> str:
    try:
        erro = resp.json().get("error", {})
        status, msg = erro.get("status", ""), erro.get("message", "")
    except Exception:
        status, msg = "", resp.text[:200]
    dica = ""
    if resp.status_code in (401, 403):
        dica = " — verifique as credenciais nos Secrets e as regras/permissões do Firestore."
    return f"HTTP {resp.status_code} {status}: {msg}{dica}".strip()


def _requisitar(metodo: str, caminho: str, *, params=None, corpo=None, permitir_404=False):
    con = _conexao()
    url = f"{con.base_url}/{caminho}"
    try:
        resp = con.sessao.request(
            metodo, url, params=params, json=corpo,
            headers=con.cabecalhos or None, timeout=TIMEOUT,
        )
    except Exception as exc:
        raise FirestoreError(f"Falha ao acessar o Firestore ({type(exc).__name__}: {str(exc)[:200]})") from None

    if resp.status_code == 404 and permitir_404:
        return None
    if resp.status_code == 404:
        raise DocumentoNaoEncontrado(_mensagem_http(resp))
    if resp.status_code == 409:
        raise DocumentoJaExiste(_mensagem_http(resp))
    if resp.status_code >= 400:
        raise FirestoreError(_mensagem_http(resp))
    return resp.json() if resp.content else {}


def _caminho(colecao: str, doc_id: str | None = None) -> str:
    return colecao if doc_id is None else f"{colecao}/{quote(str(doc_id), safe='')}"


# --------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------
def listar(colecao: str, limite: int | None = None) -> list[dict]:
    """Lista TODOS os documentos (segue a paginação da API) ou só `limite`."""
    docs: list[dict] = []
    token = None
    while True:
        params = {"pageSize": limite or TAMANHO_PAGINA}
        if token:
            params["pageToken"] = token
        dados = _requisitar("GET", _caminho(colecao), params=params)
        docs.extend(doc_para_dict(d) for d in dados.get("documents", []))
        token = dados.get("nextPageToken")
        if limite or not token:
            break
    return docs[:limite] if limite else docs


def obter(colecao: str, doc_id: str) -> dict | None:
    doc = _requisitar("GET", _caminho(colecao, doc_id), permitir_404=True)
    return None if doc is None else doc_para_dict(doc)


def criar(colecao: str, dados: dict, doc_id: str | None = None) -> dict:
    """Cria um documento. Com `doc_id`, falha com DocumentoJaExiste se já houver."""
    params = {"documentId": doc_id} if doc_id else None
    corpo = {"fields": {k: para_valor(v) for k, v in dados.items() if k != "id"}}
    return doc_para_dict(_requisitar("POST", _caminho(colecao), params=params, corpo=corpo))


def atualizar(colecao: str, doc_id: str, campos: dict) -> None:
    """Atualiza SOMENTE os campos informados; não cria o doc se ele não existir."""
    params = [("updateMask.fieldPaths", k) for k in campos] + [("currentDocument.exists", "true")]
    corpo = {"fields": {k: para_valor(v) for k, v in campos.items()}}
    _requisitar("PATCH", _caminho(colecao, doc_id), params=params, corpo=corpo)


def excluir(colecao: str, doc_id: str) -> None:
    _requisitar("DELETE", _caminho(colecao, doc_id))
