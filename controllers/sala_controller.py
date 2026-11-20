"""Salas — coleção `salas` no Firestore."""
import pandas as pd

from utils import firestore_client as fs
from utils.tabelas import para_dataframe

COLECAO = "salas"
COLECAO_RESERVAS = "reservas"

COLS = [
    "id", "sala", "capacidade", "tipo", "campus", "predio", "andar",
    "numero", "computadores", "projetor", "ar_condicionado",
    "acessibilidade", "observacoes",
]


def listar() -> pd.DataFrame:
    df = para_dataframe(fs.listar(COLECAO), COLS)
    return df.sort_values("sala", key=lambda s: s.astype(str).str.lower()).reset_index(drop=True)


def cadastrar(dados: dict) -> str:
    """Cadastra uma sala. O ID é o gerado pelo Firestore. Retorna o ID."""
    nome = str(dados.get("sala", "")).strip()
    if not nome:
        raise ValueError("Informe o nome da sala.")
    existentes = listar()["sala"].astype(str).str.strip().str.lower()
    if nome.lower() in set(existentes):
        raise ValueError(f"Já existe uma sala chamada '{nome}'.")
    return fs.criar(COLECAO, {**dados, "sala": nome})["id"]


def excluir(id_sala: str) -> None:
    """Exclui a sala, desde que não tenha reservas Pendentes/Confirmadas."""
    sala = fs.obter(COLECAO, id_sala)
    if sala is None:
        raise ValueError("Sala não encontrada (talvez já tenha sido excluída).")
    ativas = [
        r for r in fs.listar(COLECAO_RESERVAS)
        if str(r.get("sala", "")) == str(sala.get("sala", ""))
        and r.get("status") in ("Pendente", "Confirmada")
    ]
    if ativas:
        raise ValueError(
            f"A sala '{sala.get('sala')}' tem {len(ativas)} reserva(s) pendente(s)/confirmada(s). "
            "Cancele ou reprove essas reservas antes de excluir."
        )
    fs.excluir(COLECAO, id_sala)
