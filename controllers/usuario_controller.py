"""Usuários — coleção `usuarios` no Firestore (antes ficava em CSV efêmero)."""
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

import pandas as pd

from utils import firestore_client as fs
from utils.seed import linhas_seed
from utils.tabelas import para_dataframe

COLECAO = "usuarios"
PERFIS = ("Administrador", "Professor", "Solicitante")
COLUNAS = ["id", "nome", "email", "perfil", "ativo", "criado_em", "ultimo_login"]
MIN_SENHA = 6
ITERACOES = 240_000
PREFIXO = "pbkdf2_sha256"


# ---------- senhas ----------
def gerar_hash(senha: str) -> str:
    sal = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(sal), ITERACOES)
    return f"{PREFIXO}${ITERACOES}${sal}${dk.hex()}"


def verificar_senha(senha: str, armazenado: str) -> bool:
    armazenado = str(armazenado or "")
    if armazenado.startswith(PREFIXO + "$"):
        try:
            _, it, sal, esperado = armazenado.split("$")
            dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(sal), int(it))
        except ValueError:
            return False
        return hmac.compare_digest(dk.hex(), esperado)
    # formato antigo (SHA-256 puro, sem sal) — aceito só para migrar
    return hmac.compare_digest(hashlib.sha256(senha.encode("utf-8")).hexdigest(), armazenado)


def hash_legado(armazenado: str) -> bool:
    return not str(armazenado or "").startswith(PREFIXO + "$")


# ---------- dados ----------
def id_por_email(email: str) -> str:
    """ID determinístico: garante e-mail único sem precisar de consulta."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:24]


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def garantir_usuarios_iniciais() -> None:
    """Se a coleção está vazia, importa data/seed/usuarios.csv (uma única vez)."""
    if fs.listar(COLECAO, limite=1):
        return
    for linha in linhas_seed("usuarios.csv"):
        email = str(linha.get("email", "")).strip().lower()
        if not email:
            continue
        try:
            fs.criar(COLECAO, {
                "nome": linha.get("nome", ""), "email": email,
                "senha": linha.get("senha", ""), "perfil": linha.get("perfil", "Professor"),
                "ativo": linha.get("ativo", "Sim"), "criado_em": _agora(),
            }, doc_id=id_por_email(email))
        except fs.DocumentoJaExiste:
            pass


def obter_por_email(email: str) -> dict | None:
    email = str(email or "").strip().lower()
    if not email:
        return None
    usuario = fs.obter(COLECAO, id_por_email(email))
    if usuario is None:
        garantir_usuarios_iniciais()
        usuario = fs.obter(COLECAO, id_por_email(email))
    return usuario


def obter(uid: str) -> dict | None:
    return fs.obter(COLECAO, uid)


def listar() -> pd.DataFrame:
    """Lista usuários SEM o campo de senha."""
    garantir_usuarios_iniciais()
    df = para_dataframe(fs.listar(COLECAO), COLUNAS)
    return df.sort_values("nome", key=lambda s: s.astype(str).str.lower()).reset_index(drop=True)


def criar(nome: str, email: str, senha_hash: str, perfil: str) -> str:
    """Levanta fs.DocumentoJaExiste se o e-mail já estiver cadastrado."""
    email = email.strip().lower()
    return fs.criar(COLECAO, {
        "nome": nome.strip(), "email": email, "senha": senha_hash,
        "perfil": perfil, "ativo": "Sim", "criado_em": _agora(),
    }, doc_id=id_por_email(email))["id"]


def definir_senha(uid: str, senha_hash: str) -> None:
    fs.atualizar(COLECAO, uid, {"senha": senha_hash})


def registrar_login(uid: str) -> None:
    fs.atualizar(COLECAO, uid, {"ultimo_login": _agora()})


# ---------- gestão pelo administrador (as proteções valem aqui, não só na tela) ----------
def _admins_ativos_exceto(uid: str) -> int:
    df = listar()
    return int(((df["perfil"] == "Administrador") & (df["ativo"] == "Sim") & (df["id"] != uid)).sum())


def _proteger_admin(alvo: dict, uid: str, executor_id: str | None, nova_ativo: str, novo_perfil: str) -> None:
    deixa_de_ser_admin_ativo = (
        alvo.get("perfil") == "Administrador" and alvo.get("ativo") == "Sim"
        and (nova_ativo != "Sim" or novo_perfil != "Administrador")
    )
    if not deixa_de_ser_admin_ativo:
        return
    if executor_id is not None and str(executor_id) == str(uid):
        raise ValueError("Você não pode desativar nem rebaixar o seu próprio usuário.")
    if _admins_ativos_exceto(uid) == 0:
        raise ValueError("O sistema precisa de pelo menos um administrador ativo.")


def definir_ativo(uid: str, ativo: str, executor_id: str | None = None) -> None:
    if ativo not in ("Sim", "Não"):
        raise ValueError("Situação inválida.")
    alvo = obter(uid)
    if alvo is None:
        raise ValueError("Usuário não encontrado.")
    _proteger_admin(alvo, uid, executor_id, ativo, alvo.get("perfil", ""))
    fs.atualizar(COLECAO, uid, {"ativo": ativo})


def atualizar(uid: str, nome: str, perfil: str, executor_id: str | None = None) -> None:
    """Edita nome e perfil de um usuário (o e-mail é a identidade e não muda)."""
    nome = " ".join(str(nome).split())
    if not nome:
        raise ValueError("Informe o nome.")
    if perfil not in PERFIS:
        raise ValueError("Perfil inválido.")
    alvo = obter(uid)
    if alvo is None:
        raise ValueError("Usuário não encontrado.")
    _proteger_admin(alvo, uid, executor_id, alvo.get("ativo", "Sim"), perfil)
    fs.atualizar(COLECAO, uid, {"nome": nome, "perfil": perfil})


def redefinir_senha(uid: str, nova_senha: str, por_email: str) -> None:
    """O administrador define a nova senha de alguém (guardada só como hash PBKDF2 com sal)."""
    if len(nova_senha or "") < MIN_SENHA:
        raise ValueError(f"A senha deve ter pelo menos {MIN_SENHA} caracteres.")
    if obter(uid) is None:
        raise ValueError("Usuário não encontrado.")
    fs.atualizar(COLECAO, uid, {
        "senha": gerar_hash(nova_senha),
        "senha_redefinida_por": por_email,
        "senha_redefinida_em": _agora(),
    })
