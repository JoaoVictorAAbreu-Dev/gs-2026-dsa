"""Indicadores, faixas de operação e modelagem do risco hídrico do Sistema Cantareira.

Todas as funções usam apenas informação disponível até a data de referência ``t``;
os alvos ficam em ``t + h`` e nunca entram como atributo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cantareira_diario_2024_2026.csv"

# Faixas de operação do Cantareira (Resolução Conjunta ANA/DAEE nº 925/2017),
# em % do volume útil: limite inferior de cada faixa.
FAIXAS = [
    (1, "Normal", 60.0),
    (2, "Atenção", 40.0),
    (3, "Alerta", 30.0),
    (4, "Restrição", 20.0),
    (5, "Especial", 0.0),
]
# Níveis de alerta pedidos no enunciado, associados às faixas oficiais.
NIVEIS = ["Normal", "Atenção", "Alerta", "Crítico"]
FAIXA_PARA_NIVEL = {1: 0, 2: 1, 3: 2, 4: 3, 5: 3}

# Volume útil total aproximado (hm³): 204,59 hm³ correspondem a 20,83241 % em 01/12/2025.
VOLUME_UTIL_TOTAL_HM3 = 204.59 / 0.2083241

FEATURES = [
    "storage_pct",
    "trend_7d",
    "trend_30d",
    "rain_7d",
    "rain_30d",
    "rain_90d",
    "inflow_7d",
    "inflow_30d",
    "produced_30d",
    "balance_30d",
    "dist_next_threshold",
    "doy_sin",
    "doy_cos",
]


def load_series(path: Path = DATA) -> pd.DataFrame:
    """Carrega a série diária e valida unicidade, continuidade e faixas físicas."""
    frame = pd.read_csv(path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    if frame["date"].duplicated().any():
        raise ValueError("Datas duplicadas na série")
    gaps = frame["date"].diff().dropna().dt.days
    if (gaps != 1).any():
        raise ValueError("A série precisa ser diária e contínua")
    if not frame["storage_pct"].between(0, 100).all():
        raise ValueError("Volume útil fora do intervalo 0–100 %")
    if (frame[["rain_mm", "natural_inflow_m3s", "produced_flow_m3s"]] < 0).any().any():
        raise ValueError("Valores negativos de chuva ou vazão")
    if frame.isna().any().any():
        raise ValueError("Há valores ausentes; defina o tratamento antes de seguir")
    return frame


def faixa(volume_pct: float) -> int:
    """Número da faixa de operação (1 = Normal ... 5 = Especial)."""
    if not 0 <= volume_pct <= 100:
        raise ValueError("Volume útil deve estar entre 0 e 100 %")
    for numero, _, limite in FAIXAS:
        if volume_pct >= limite:
            return numero
    return 5


def nome_faixa(numero: int) -> str:
    return {n: nome for n, nome, _ in FAIXAS}[numero]


def limite_inferior(numero: int) -> float:
    return {n: lim for n, _, lim in FAIXAS}[numero]


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores e atributos com janelas que terminam em ``t`` (sem olhar o futuro)."""
    data = frame.copy()
    vol = data["storage_pct"]
    data["faixa"] = vol.map(faixa)
    data["trend_7d"] = vol - vol.shift(7)
    data["trend_30d"] = vol - vol.shift(30)
    data["rain_7d"] = data["rain_mm"].rolling(7).sum()
    data["rain_30d"] = data["rain_mm"].rolling(30).sum()
    data["rain_90d"] = data["rain_mm"].rolling(90).sum()
    data["inflow_7d"] = data["natural_inflow_m3s"].rolling(7).mean()
    data["inflow_30d"] = data["natural_inflow_m3s"].rolling(30).mean()
    data["produced_30d"] = data["produced_flow_m3s"].rolling(30).mean()
    data["balance_30d"] = data["inflow_30d"] - data["produced_30d"]
    data["dist_next_threshold"] = vol - data["faixa"].map(limite_inferior)
    data.loc[data["faixa"] == 5, "dist_next_threshold"] = vol[data["faixa"] == 5]
    doy = data["date"].dt.dayofyear
    data["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    data["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    daily_trend = data["trend_30d"] / 30
    data["autonomia_dias"] = np.where(
        daily_trend < 0,
        np.minimum(data["dist_next_threshold"] / -daily_trend.where(daily_trend < 0), 365),
        365,
    )
    return data


def feature_table(frame: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Tabela supervisionada: atributos em ``t``; alvo = variação de volume entre ``t`` e ``t+h``."""
    if horizon < 1:
        raise ValueError("Horizonte deve ser positivo")
    data = add_indicators(frame)
    data["target_date"] = data["date"].shift(-horizon)
    data["target_storage"] = data["storage_pct"].shift(-horizon)
    data["target_delta"] = data["target_storage"] - data["storage_pct"]
    data["target_faixa"] = data["target_storage"].map(lambda v: faixa(v) if pd.notna(v) else np.nan)
    data["piora_faixa"] = (data["target_faixa"] > data["faixa"]).astype(float)
    data.loc[data["target_storage"].isna(), "piora_faixa"] = np.nan
    return data.dropna(subset=FEATURES).reset_index(drop=True)


@dataclass(frozen=True)
class Fold:
    nome: str
    inicio: pd.Timestamp
    fim: pd.Timestamp


def walk_forward_folds(start: str, end: str, months: int = 3) -> list[Fold]:
    """Janelas consecutivas de teste; cada uma treina só com alvos anteriores ao seu início."""
    folds = []
    cursor = pd.Timestamp(start)
    stop = pd.Timestamp(end)
    while cursor <= stop:
        fim = min(cursor + pd.DateOffset(months=months) - pd.Timedelta(days=1), stop)
        folds.append(Fold(f"{cursor:%m/%Y}–{fim:%m/%Y}", cursor, fim))
        cursor = fim + pd.Timedelta(days=1)
    return folds


def split_fold(table: pd.DataFrame, fold: Fold) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Treino: alvos observados antes do início do teste (evita vazamento pelo horizonte)."""
    labeled = table.dropna(subset=["target_storage"])
    train = labeled[labeled["target_date"] < fold.inicio]
    test = labeled[(labeled["date"] >= fold.inicio) & (labeled["date"] <= fold.fim)]
    return train, test


def nivel_alerta(faixa_atual: int, faixa_projetada: int) -> int:
    """Nível final: parte da faixa atual e sobe um nível se a projeção indicar piora de faixa."""
    base = FAIXA_PARA_NIVEL[faixa_atual]
    if faixa_projetada > faixa_atual:
        base = min(base + 1, len(NIVEIS) - 1)
    return base
