"""Carga inicial ÚNICA: importa data/seed/*.csv para o Firestore quando a coleção está vazia."""
import csv
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"


def linhas_seed(nome_arquivo: str) -> list[dict]:
    caminho = SEED_DIR / nome_arquivo
    if not caminho.exists():
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
