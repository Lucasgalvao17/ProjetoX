"""Hora local do sistema. O Streamlit Cloud roda em UTC; aqui usamos o fuso do campus
(padrão: America/Porto_Velho, UTC-4). Troque com a variável de ambiente ATILA_FUSO."""
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _fuso():
    nome = os.environ.get("ATILA_FUSO", "America/Porto_Velho")
    try:
        return ZoneInfo(nome)
    except (ZoneInfoNotFoundError, ValueError):
        return timezone(timedelta(hours=-4))


FUSO = _fuso()


def agora() -> datetime:
    """Data/hora local, sem fuso (comparável com as datas gravadas nas reservas)."""
    return datetime.now(FUSO).replace(tzinfo=None)


def hoje() -> date:
    return agora().date()
