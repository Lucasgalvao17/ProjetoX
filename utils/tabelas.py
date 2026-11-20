"""Helpers pequenos de DataFrame usados por todos os controllers/telas."""
import pandas as pd


def para_dataframe(docs: list[dict], colunas: list[str]) -> pd.DataFrame:
    """Lista de dicts do Firestore -> DataFrame com exatamente `colunas`, sem NaN."""
    df = pd.DataFrame(docs)
    for c in colunas:
        if c not in df.columns:
            df[c] = ""
    return df[colunas].fillna("").reset_index(drop=True)


def para_numero(serie) -> pd.Series:
    """Converte para número sem quebrar com vazios/textos."""
    return pd.to_numeric(serie, errors="coerce").fillna(0)
