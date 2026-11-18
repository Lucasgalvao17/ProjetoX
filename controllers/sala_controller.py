from models.csv_repository import ler_csv, adicionar_linha, atualizar_csv

COLS = ["id","sala","capacidade","tipo","campus","predio","andar","numero","computadores","projetor","ar_condicionado","acessibilidade","observacoes"]

def listar():
    return ler_csv("salas.csv", COLS)

def cadastrar(dados):
    df = listar()
    novo_id = 1 if df.empty else int(pd_to_num(df["id"]).max()) + 1
    adicionar_linha("salas.csv", {"id": novo_id, **dados}, COLS)

def excluir(id_sala):
    df = listar()
    df = df[df["id"].astype(str) != str(id_sala)]
    atualizar_csv("salas.csv", df)

def pd_to_num(s):
    import pandas as pd
    return pd.to_numeric(s, errors="coerce").fillna(0)
