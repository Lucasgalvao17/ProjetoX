"""Agendamentos/Reservas — coleção `reservas` no Firestore."""
from datetime import date, datetime, timezone

import pandas as pd

from utils import firestore_client as fs
from utils import tempo
from utils.tabelas import para_dataframe

COLECAO = "reservas"
COLECAO_DISCIPLINAS = "disciplinas"
STATUS_VALIDOS = ("Pendente", "Confirmada", "Reprovada", "Cancelada")
STATUS_ATIVOS = ("Pendente", "Confirmada")   # ocupam a sala

# As 4 tabelas da tela de agendamentos. A 4ª reúne o que "saiu de cena" sem ser apagado:
# reprovadas + aprovadas já realizadas. Para trocar, mude `aba` em `classificar`.
ABAS = ("Aprovados", "Pendentes", "Cancelados", "Histórico")

COLUNAS = [
    "id", "professor", "disciplina", "disciplina_id", "sala", "tipo_aula", "alunos", "data",
    "inicio", "fim", "status", "justificativa", "motivo", "criado_por", "criado_em",
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


def _fim_datetime(data, fim):
    try:
        return datetime.combine(date.fromisoformat(str(data)), _hora(fim))
    except ValueError:
        return None


def ja_passou(data, fim, agora: datetime | None = None) -> bool:
    """True se a reserva já terminou. Data/hora ilegível conta como 'não passou' (decisão conservadora)."""
    termino = _fim_datetime(data, fim)
    return termino is not None and termino < (agora or tempo.agora())


# ---------------------------------------------------------------- classificação
def classificar(df: pd.DataFrame, agora: datetime | None = None) -> pd.DataFrame:
    """Acrescenta `situacao` (rótulo amigável) e `aba` (qual das 4 tabelas). Nada é gravado:
    'Concluída' é derivado de data/hora, então não depende de ninguém atualizar o Firestore."""
    agora = agora or tempo.agora()
    df = df.copy()
    situacoes, abas = [], []
    for _, r in df.iterrows():
        fim = _fim_datetime(r["data"], r["fim"])
        passou = fim is not None and fim < agora
        status = r["status"]
        if status == "Confirmada":
            s, a = ("Concluída", "Histórico") if passou else ("Aprovada", "Aprovados")
        elif status == "Pendente":
            s, a = ("Pendente (data vencida)" if passou else "Pendente"), "Pendentes"
        elif status == "Cancelada":
            s, a = "Cancelada", "Cancelados"
        elif status == "Reprovada":
            s, a = "Reprovada", "Histórico"
        else:
            s, a = (str(status) or "Sem status"), "Histórico"
        situacoes.append(s)
        abas.append(a)
    df["situacao"] = situacoes
    df["aba"] = abas
    return df


def do_usuario(df: pd.DataFrame, usuario: dict) -> pd.DataFrame:
    """Reservas criadas pelo usuário (reservas antigas sem `criado_por` casam pelo nome)."""
    por_email = df["criado_por"].astype(str).str.lower() == str(usuario.get("email", "")).lower()
    antigas = (df["criado_por"].astype(str) == "") & (df["professor"].astype(str) == str(usuario.get("nome", "")))
    return df[por_email | antigas]


# ---------------------------------------------------------------- conflitos
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


def disponibilidade(salas: pd.DataFrame, data, inicio, fim, reservas: pd.DataFrame | None = None) -> pd.DataFrame:
    """Marca cada sala como Livre/Ocupada no intervalo pedido."""
    reservas = listar() if reservas is None else reservas
    out = salas.copy()
    out["disponibilidade"] = [
        "Ocupada" if not conflitos(s, data, inicio, fim, df=reservas).empty else "Livre"
        for s in out["sala"]
    ]
    return out


def agenda_do_dia(sala, data, reservas: pd.DataFrame | None = None) -> pd.DataFrame:
    """Reservas ativas (Pendente/Confirmada) de uma sala num dia, em ordem de horário."""
    reservas = listar() if reservas is None else reservas
    dia = reservas[
        (reservas["sala"].astype(str) == str(sala))
        & (reservas["data"].astype(str) == str(data))
        & (reservas["status"].isin(STATUS_ATIVOS))
    ]
    return dia.sort_values("inicio").reset_index(drop=True)


def _descrever(conf: pd.DataFrame) -> str:
    r = conf.iloc[0]
    return (f"{r['sala']} já está {str(r['status']).lower()} em {r['data']} "
            f"das {r['inicio']} às {r['fim']} ({r['professor']}).")


def _chave_ordem(registro):
    """(createTime normalizado, id): decide quem 'chegou primeiro' numa disputa."""
    base, _, fracao = str(registro.get("criado_em", "")).rstrip("Z").partition(".")
    return (base, fracao.ljust(9, "0"), str(registro.get("id", "")))


# ---------------------------------------------------------------- escrita
def criar(dados: dict) -> str:
    """
    Cria uma reserva Pendente já validada contra conflitos. Retorna o ID.

    O Firestore REST não tem "unique constraint", então a proteção é em duas
    etapas: (1) checa antes de gravar; (2) depois de gravar, confere de novo e,
    se outra reserva conflitante CHEGOU ANTES, desfaz a própria e avisa.
    """
    faltando = [c for c in ("professor", "disciplina", "sala", "data", "inicio", "fim")
                if not str(dados.get(c, "")).strip()]
    if faltando:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(faltando)}.")
    if _hora(dados["fim"]) <= _hora(dados["inicio"]):
        raise ValueError("O horário final deve ser posterior ao horário inicial.")

    if dados.get("disciplina_id"):   # a disciplina precisa existir e estar ativa no Firestore
        disc = fs.obter(COLECAO_DISCIPLINAS, dados["disciplina_id"])
        if disc is None or str(disc.get("ativa") or "Sim") != "Sim":
            raise ValueError("Disciplina inexistente ou inativa. Atualize a página e escolha outra.")

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


def alterar_status(id_reserva: str, status: str, usuario: str | None = None, motivo: str | None = None) -> None:
    """
    Muda o status (o registro NUNCA é apagado: reprovar/cancelar só atualiza o status e o motivo).
    Reativar (Pendente/Confirmada) revalida conflitos.
    """
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
        "motivo": (motivo or "").strip(),
        "atualizado_por": usuario or "",
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


def cancelar_propria(id_reserva: str, email: str) -> None:
    """O próprio solicitante cancela uma reserva sua que ainda esteja Pendente ou Aprovada."""
    reserva = fs.obter(COLECAO, id_reserva)
    if reserva is None:
        raise ValueError("Reserva não encontrada.")
    if str(reserva.get("criado_por", "")).lower() != str(email).lower():
        raise ValueError("Você só pode cancelar as suas próprias reservas.")
    if reserva.get("status") not in STATUS_ATIVOS:
        raise ValueError("Só é possível cancelar reservas pendentes ou aprovadas.")
    fim = _fim_datetime(reserva.get("data"), reserva.get("fim"))
    if fim is not None and fim < tempo.agora():
        raise ValueError("Essa reserva já foi realizada e não pode mais ser cancelada.")
    alterar_status(id_reserva, "Cancelada", email, motivo="Cancelada pelo solicitante")
