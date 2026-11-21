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


def atualizar(id_sala: str, dados: dict) -> int:
    """
    Edita uma sala no Firestore. As reservas guardam a sala pelo NOME, então, se o nome mudar,
    as reservas antigas são renomeadas ANTES de gravar a sala (se algo falhar no meio, a sala
    segue intacta e repetir a edição conclui o serviço). Retorna quantas reservas foram renomeadas.
    """
    atual = fs.obter(COLECAO, id_sala)
    if atual is None:
        raise ValueError("Sala não encontrada (talvez já tenha sido excluída).")

    campos = {k: v for k, v in dados.items() if k in COLS and k != "id"}
    novo_nome = str(campos.get("sala", atual.get("sala", ""))).strip()
    if not novo_nome:
        raise ValueError("Informe o nome da sala.")
    campos["sala"] = novo_nome

    outras = listar()
    outras = outras[outras["id"].astype(str) != str(id_sala)]
    if novo_nome.lower() in set(outras["sala"].astype(str).str.strip().str.lower()):
        raise ValueError(f"Já existe outra sala chamada '{novo_nome}'.")

    nome_antigo = str(atual.get("sala", "")).strip()
    renomeadas = 0
    if nome_antigo and nome_antigo != novo_nome:
        for r in fs.listar(COLECAO_RESERVAS):
            if str(r.get("sala", "")).strip() == nome_antigo:
                fs.atualizar(COLECAO_RESERVAS, r["id"], {"sala": novo_nome})
                renomeadas += 1

    fs.atualizar(COLECAO, id_sala, campos)
    return renomeadas


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
