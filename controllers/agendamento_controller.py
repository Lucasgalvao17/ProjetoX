from models.csv_repository import ler_csv, adicionar_linha, atualizar_csv
from datetime import datetime

COLS = ["id","professor","disciplina","sala","tipo_aula","alunos","data","inicio","fim","status","justificativa","criado_por"]

def listar():
    return ler_csv("agendamentos.csv", COLS)

def conflitos(sala, data, inicio, fim, ignorar_id=None):
    df = listar()
    if df.empty:
        return df
    df = df[(df["sala"].astype(str) == str(sala)) &
            (df["data"].astype(str) == str(data)) &
            (df["status"].isin(["Pendente","Confirmada"]))]
    if ignorar_id is not None:
        df = df[df["id"].astype(str) != str(ignorar_id)]
    if df.empty:
        return df
    ini = datetime.strptime(str(inicio), "%H:%M").time()
    end = datetime.strptime(str(fim), "%H:%M").time()
    mask = []
    for _, r in df.iterrows():
        r_ini = datetime.strptime(str(r["inicio"]), "%H:%M").time()
        r_end = datetime.strptime(str(r["fim"]), "%H:%M").time()
        mask.append(ini < r_end and end > r_ini)
    return df[mask]

def horario_disponivel(sala, data, inicio, fim):
    return conflitos(sala, data, inicio, fim).empty

def criar(dados):
    df = listar()
    novo_id = 1 if df.empty else int(pd_to_num(df["id"]).max()) + 1
    adicionar_linha("agendamentos.csv", {"id": novo_id, **dados}, COLS)

def alterar_status(id_reserva, status):
    df = listar()
    df.loc[df["id"].astype(str) == str(id_reserva), "status"] = status
    atualizar_csv("agendamentos.csv", df)

def pd_to_num(s):
    import pandas as pd
    return pd.to_numeric(s, errors="coerce").fillna(0)
