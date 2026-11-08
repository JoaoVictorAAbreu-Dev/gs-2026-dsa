"""Baixa a série diária do Sistema Cantareira no Portal dos Mananciais (Sabesp), mês a mês.

Uso: python -m src.fetch_sabesp [AAAA-MM-DD início] [AAAA-MM-DD fim]
Gera data/raw/monthly/AAAA-MM.csv e data/cantareira_diario_2024_2026.csv.
O endpoint é o mesmo usado pelo site da Sabesp e não é uma API documentada.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

SYSTEM_ID = 64  # Cantareira no cadastro /api/v4/sistemas do portal
BASE = "https://mananciais.sabesp.com.br/api/v4/sistemas/{id}/dados/diario/{inicio}/{fim}"
ROOT = Path(__file__).resolve().parents[1]
MONTHLY = ROOT / "data" / "raw" / "monthly"
CSV_OUT = ROOT / "data" / "cantareira_diario_2024_2026.csv"
FIELDS = {
    "storage_pct": "volumeUtilArmazenadoPorcentagem",
    "rain_mm": "chuva",
    "natural_inflow_m3s": "vazaoNatural",
    "produced_flow_m3s": "vazaoProduzida",
}


def normalize(payload: dict, start: date, end: date) -> list[dict[str, str]]:
    """Valida e normaliza um bloco JSON do portal para linhas diárias."""
    observations = payload.get("data")
    if not isinstance(observations, list) or not observations:
        raise ValueError("Esperado um array 'data' não vazio")
    rows = []
    for item in observations:
        if item.get("idSistema") not in (None, SYSTEM_ID):
            raise ValueError("Unexpected system ID")
        observed = date.fromisoformat(str(item["date"])[:10])
        if not start <= observed <= end:
            raise ValueError("Data fora do intervalo pedido")
        row = {"date": observed.isoformat()}
        for column, key in FIELDS.items():
            value = item.get(key)
            if value is None:
                raise ValueError(f"{key} ausente em {observed}")
            row[column] = f"{float(value):.5f}"
        if not 0 <= float(row["storage_pct"]) <= 100:
            raise ValueError(f"Volume útil inválido em {observed}")
        rows.append(row)
    rows.sort(key=lambda r: r["date"])
    if len({r["date"] for r in rows}) != len(rows):
        raise ValueError("Datas duplicadas na fonte")
    return rows


def months(start: date, end: date):
    cursor = start.replace(day=1)
    while cursor <= end:
        nxt = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
        yield max(cursor, start), min(nxt - timedelta(days=1), end)
        cursor = nxt


def main(start: date, end: date) -> None:
    MONTHLY.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for inicio, fim in months(start, end):
        url = BASE.format(id=SYSTEM_ID, inicio=inicio.isoformat(), fim=fim.isoformat())
        with urlopen(Request(url, headers={"User-Agent": "GS-FIAP-pesquisa-academica/2.0"}), timeout=45) as resp:
            rows = normalize(json.loads(resp.read()), inicio, fim)
        with (MONTHLY / f"{inicio:%Y-%m}.csv").open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows([[r["date"], *[r[c] for c in FIELDS]] for r in rows])
        all_rows.extend(rows)
        print(f"{inicio:%Y-%m}: {len(rows)} dias")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "system", *FIELDS])
        writer.writeheader()
        writer.writerows({**r, "system": "Cantareira"} for r in all_rows)
    print(f"{len(all_rows)} dias gravados em {CSV_OUT}")


if __name__ == "__main__":
    args = [date.fromisoformat(a) for a in sys.argv[1:3]]
    main(args[0] if args else date(2024, 1, 1), args[1] if len(args) > 1 else date(2026, 11, 7))
