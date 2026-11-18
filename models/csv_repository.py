from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def ler_csv(nome, colunas=None):
    caminho = DATA_DIR / nome
    if not caminho.exists():
        df = pd.DataFrame(columns=colunas or [])
        df.to_csv(caminho, index=False)
        return df
    try:
        return pd.read_csv(caminho)
    except Exception:
        return pd.DataFrame(columns=colunas or [])

def atualizar_csv(nome, df):
    df.to_csv(DATA_DIR / nome, index=False)

def adicionar_linha(nome, dados, colunas):
    df = ler_csv(nome, colunas)
    for c in colunas:
        if c not in df.columns:
            df[c] = ""
    df = pd.concat([df[colunas], pd.DataFrame([dados], columns=colunas)], ignore_index=True)
    atualizar_csv(nome, df)
    return df
