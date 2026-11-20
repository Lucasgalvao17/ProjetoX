"""Agendamentos/Reservas — coleção `reservas` no Firestore."""
from datetime import datetime, timezone

import pandas as pd

from utils import firestore_client as fs
from utils.tabelas import para_dataframe

COLECAO = "reservas"
STATUS_VALIDOS = ("Pendente", "Confirmada", "Reprovada", "Cancelada")
STATUS_ATIVOS = ("Pendente", "Confirmada")   # ocupam a sala

COLUNAS = [
    "id", "professor", "disciplina", "sala", "tipo_aula", "alunos", "data",
    "inicio", "fim", "status", "justificativa", "criado_por", "criado_em",
    "atualizado_por", "atualizado_em",
]


class ConflitoHorario(ValueError):
    """A sala já está reservada (Pendente/Confirmada) no intervalo pedido."""


def listar() -> pd.DataFrame:
    df = para_dataframe(fs.listar(COLECAO), COLUNAS)
    return df.sort_values(["data", "inicio"], ascending=False).reset_index(drop=True)


def _hora(valor):
    texto = str(valor).strip()
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    raise ValueError(f"Horário inválido: '{valor}'")


def conflitos(sala, data, inicio, fim, ignorar_id=None, df=None) -> pd.DataFrame:
    """Reservas ativas da mesma sala/data cujo intervalo se sobrepõe ao pedido."""
    if df is None:
        df = listar()
    if df.empty:
        return df.iloc[0:0]

    df = df[
        (df["sala"].astype(str) == str(sala))
        & (df["data"].astype(str) == str(data))
        & (df["status"].isin(STATUS_ATIVOS))
    ]
    if ignorar_id is not None:
        df = df[df["id"].astype(str) != str(ignorar_id)]
    if df.empty:
        return df

    ini, fi = _hora(inicio), _hora(fim)
    sobrepoe = []
    for _, r in df.iterrows():
        try:
            sobrepoe.append(ini < _hora(r["fim"]) and fi > _hora(r["inicio"]))
        except ValueError:
            sobrepoe.append(False)
    return df[sobrepoe]


def horario_disponivel(sala, data, inicio, fim) -> bool:
    return conflitos(sala, data, inicio, fim).empty


def _descrever(conf: pd.DataFrame) -> str:
    r = conf.iloc[0]
    return (f"{r['sala']} já está {str(r['status']).lower()} em {r['data']} "
            f"das {r['inicio']} às {r['fim']} ({r['professor']}).")


def _chave_ordem(registro):
    """(createTime normalizado, id): decide quem 'chegou primeiro' numa disputa."""
    base, _, fracao = str(registro.get("criado_em", "")).rstrip("Z").partition(".")
    return (base, fracao.ljust(9, "0"), str(registro.get("id", "")))


def criar(dados: dict) -> str:
    """
    Cria uma reserva Pendente já validada contra conflitos. Retorna o ID.

    O Firestore REST não tem "unique constraint", então a proteção é em duas
    etapas: (1) checa antes de gravar; (2) depois de gravar, confere de novo e,
    se outra reserva conflitante CHEGOU ANTES, desfaz a própria e avisa.
    Assim, duas pessoas reservando ao mesmo tempo não ficam com a sala duplicada.
    """
    faltando = [c for c in ("professor", "disciplina", "sala", "data", "inicio", "fim")
                if not str(dados.get(c, "")).strip()]
    if faltando:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(faltando)}.")
    if _hora(dados["fim"]) <= _hora(dados["inicio"]):
        raise ValueError("O horário final deve ser posterior ao horário inicial.")

    sala, data, inicio, fim = dados["sala"], dados["data"], dados["inicio"], dados["fim"]

    existente = conflitos(sala, data, inicio, fim)
    if not existente.empty:
        raise ConflitoHorario(_descrever(existente))

    novo = fs.criar(COLECAO, {**dados, "status": dados.get("status") or "Pendente"})

    rivais = conflitos(sala, data, inicio, fim, ignorar_id=novo["id"])
    if not rivais.empty:
        anteriores = rivais[[(_chave_ordem(r) < _chave_ordem(novo)) for _, r in rivais.iterrows()]]
        if not anteriores.empty:
            fs.excluir(COLECAO, novo["id"])
            raise ConflitoHorario(_descrever(anteriores))
    return novo["id"]


def alterar_status(id_reserva: str, status: str, usuario: str | None = None) -> None:
    """Muda o status. Reativar (Pendente/Confirmada) revalida conflitos."""
    if status not in STATUS_VALIDOS:
        raise ValueError(f"Status inválido: {status}")
    reserva = fs.obter(COLECAO, id_reserva)
    if reserva is None:
        raise ValueError("Reserva não encontrada (talvez tenha sido removida).")

    if status in STATUS_ATIVOS:
        conf = conflitos(reserva.get("sala"), reserva.get("data"),
                         reserva.get("inicio"), reserva.get("fim"), ignorar_id=id_reserva)
        if not conf.empty:
            raise ConflitoHorario(_descrever(conf))

    fs.atualizar(COLECAO, id_reserva, {
        "status": status,
        "atualizado_por": usuario or "",
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
