"""Disciplinas — coleção `disciplinas` no Firestore. É daqui que sai a lista da Nova Reserva."""
import hashlib
import re
import unicodedata

import pandas as pd

from controllers import agendamento_controller as ag
from utils import firestore_client as fs
from utils import tempo
from utils.seed import linhas_seed
from utils.tabelas import para_dataframe

COLECAO = "disciplinas"
COLECAO_RESERVAS = "reservas"
COLECAO_CONFIG = "config"
MARCADOR_SEED = "seed_disciplinas"      # existe = a carga inicial já foi feita (não repetir)
COLUNAS = ["id", "nome", "codigo", "curso", "ativa"]


def normalizar(texto) -> str:
    """'Programação  Web!' e 'programacao web' viram a mesma coisa (para barrar duplicatas)."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def normalizar_codigo(codigo) -> str:
    return re.sub(r"\s+", "", str(codigo)).upper()


def id_por_codigo(codigo) -> str:
    """ID determinístico: o Firestore recusa criar duas disciplinas com o mesmo código."""
    return hashlib.sha256(normalizar_codigo(codigo).encode("utf-8")).hexdigest()[:20]


def rotulo(linha) -> str:
    return f"{linha['codigo']} — {linha['nome']}" if str(linha["codigo"]).strip() else str(linha["nome"])


def _marcar_seed() -> None:
    """Registra que a carga inicial já aconteceu, para que apagar todas as disciplinas
    não faça as do seed voltarem sozinhas."""
    try:
        fs.criar(COLECAO_CONFIG, {"feito_em": tempo.agora().isoformat(timespec="seconds")}, doc_id=MARCADOR_SEED)
    except fs.DocumentoJaExiste:
        pass


def _garantir_iniciais() -> None:
    if fs.listar(COLECAO, limite=1):
        return
    if fs.obter(COLECAO_CONFIG, MARCADOR_SEED) is not None:   # já semeou antes; vazio agora é de propósito
        return
    for linha in linhas_seed("disciplinas.csv"):
        codigo = normalizar_codigo(linha.get("codigo", ""))
        if not codigo:
            continue
        try:
            fs.criar(COLECAO, {"nome": str(linha.get("nome", "")).strip(), "codigo": codigo,
                               "curso": str(linha.get("curso", "")).strip(), "ativa": "Sim"},
                     doc_id=id_por_codigo(codigo))
        except fs.DocumentoJaExiste:
            pass
    _marcar_seed()


def listar() -> pd.DataFrame:
    """Todas as disciplinas (inclusive inativas), para o admin."""
    _garantir_iniciais()
    df = para_dataframe(fs.listar(COLECAO), COLUNAS)
    df["ativa"] = df["ativa"].replace("", "Sim")      # documentos antigos não tinham o campo
    return df.sort_values("nome", key=lambda s: s.astype(str).str.lower()).reset_index(drop=True)


def listar_ativas() -> pd.DataFrame:
    df = listar()
    return df[df["ativa"] == "Sim"].reset_index(drop=True)


def _duplicada(df: pd.DataFrame, nome: str, codigo: str | None = None) -> str | None:
    if codigo is not None and normalizar_codigo(codigo) in set(df["codigo"].map(normalizar_codigo)):
        return f"Já existe uma disciplina com o código {normalizar_codigo(codigo)}."
    if normalizar(nome) in set(df["nome"].map(normalizar)):
        return f"Já existe uma disciplina com nome equivalente a '{nome.strip()}'."
    return None


def cadastrar(nome: str, codigo: str, curso: str = "") -> str:
    nome, curso = " ".join(str(nome).split()), " ".join(str(curso).split())
    codigo = normalizar_codigo(codigo)
    if not nome or not codigo:
        raise ValueError("Informe o nome e o código da disciplina.")
    erro = _duplicada(listar(), nome, codigo)
    if erro:
        raise ValueError(erro)
    try:
        return fs.criar(COLECAO, {"nome": nome, "codigo": codigo, "curso": curso, "ativa": "Sim"},
                        doc_id=id_por_codigo(codigo))["id"]
    except fs.DocumentoJaExiste:
        raise ValueError(f"Já existe uma disciplina com o código {codigo}.") from None


def atualizar(id_disciplina: str, nome: str, curso: str, ativa: str) -> None:
    """Edita nome/curso e ativa/desativa. O código é a identidade e não muda.
    Reservas antigas guardam o nome da época e não são alteradas."""
    atual = fs.obter(COLECAO, id_disciplina)
    if atual is None:
        raise ValueError("Disciplina não encontrada.")
    nome, curso = " ".join(str(nome).split()), " ".join(str(curso).split())
    if not nome:
        raise ValueError("Informe o nome da disciplina.")
    if ativa not in ("Sim", "Não"):
        raise ValueError("Valor inválido para 'ativa'.")
    outras = listar()
    outras = outras[outras["id"].astype(str) != str(id_disciplina)]
    erro = _duplicada(outras, nome)
    if erro:
        raise ValueError(erro)
    fs.atualizar(COLECAO, id_disciplina, {"nome": nome, "curso": curso, "ativa": ativa})


def reservas_por_vir(disciplina: dict) -> list[dict]:
    """Reservas Pendentes/Confirmadas dessa disciplina que ainda não terminaram.
    Reservas novas casam pelo `disciplina_id`; as antigas (sem o campo) pelo nome."""
    agora = tempo.agora()
    nome = normalizar(disciplina.get("nome", ""))
    achadas = []
    for r in fs.listar(COLECAO_RESERVAS):
        if r.get("status") not in ag.STATUS_ATIVOS:
            continue
        if r.get("disciplina_id"):
            casa = str(r["disciplina_id"]) == str(disciplina.get("id"))
        else:
            casa = normalizar(r.get("disciplina", "")) == nome
        if casa and not ag.ja_passou(r.get("data"), r.get("fim"), agora):
            achadas.append(r)
    return achadas


def excluir(id_disciplina: str) -> str:
    """Exclui a disciplina e devolve o nome dela.
    Bloqueia se houver reserva pendente/aprovada por vir. Reservas já realizadas, canceladas ou
    reprovadas guardam o NOME da disciplina, então o histórico continua legível depois da exclusão."""
    disciplina = fs.obter(COLECAO, id_disciplina)
    if disciplina is None:
        raise ValueError("Disciplina não encontrada (talvez já tenha sido excluída).")
    nome = str(disciplina.get("nome", ""))
    por_vir = reservas_por_vir(disciplina)
    if por_vir:
        raise ValueError(
            f"A disciplina '{nome}' tem {len(por_vir)} reserva(s) pendente(s)/aprovada(s) ainda por vir. "
            "Cancele ou reprove essas reservas antes de excluir — ou, se só quiser tirá-la da lista "
            "da Nova Reserva, desative em 'Editar / ativar'."
        )
    _marcar_seed()          # antes de apagar: se for a última, o seed não pode repovoar a lista
    fs.excluir(COLECAO, id_disciplina)
    return nome
