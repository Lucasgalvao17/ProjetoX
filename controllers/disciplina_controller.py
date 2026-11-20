"""Disciplinas — coleção `disciplinas` no Firestore (antes em CSV)."""
import pandas as pd

from utils import firestore_client as fs
from utils.seed import linhas_seed
from utils.tabelas import para_dataframe

COLECAO = "disciplinas"
COLUNAS = ["id", "nome", "codigo", "curso"]


def _garantir_iniciais() -> None:
    if fs.listar(COLECAO, limite=1):
        return
    for linha in linhas_seed("disciplinas.csv"):
        fs.criar(COLECAO, {k: linha.get(k, "") for k in ("nome", "codigo", "curso")})


def listar() -> pd.DataFrame:
    _garantir_iniciais()
    df = para_dataframe(fs.listar(COLECAO), COLUNAS)
    return df.sort_values("nome", key=lambda s: s.astype(str).str.lower()).reset_index(drop=True)


def cadastrar(nome: str, codigo: str, curso: str) -> str:
    nome, codigo, curso = nome.strip(), codigo.strip(), curso.strip()
    if not nome or not codigo:
        raise ValueError("Informe o nome e o código da disciplina.")
    if codigo.lower() in set(listar()["codigo"].astype(str).str.lower()):
        raise ValueError(f"Já existe uma disciplina com o código {codigo}.")
    return fs.criar(COLECAO, {"nome": nome, "codigo": codigo, "curso": curso})["id"]
