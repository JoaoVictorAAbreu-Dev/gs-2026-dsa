"""Download a fixed daily Cantareira series from Sabesp's current web endpoint."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


START = date(2024, 1, 1)
END = date(2025, 12, 31)
SYSTEM_ID = 64  # Cantareira in the Sabesp website's /api/v4/sistemas response.
URL = (
    "https://mananciais.sabesp.com.br/api/v4/sistemas/"
    f"{SYSTEM_ID}/dados/diario/{START.isoformat()}/{END.isoformat()}"
)
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/cantareira_2024_2025.json"
CSV = ROOT / "data/processed/cantareira_daily.csv"
METADATA = ROOT / "data/processed/source_metadata.json"


def normalize(payload: dict) -> list[dict[str, str]]:
    observations = payload.get("data")
    if not isinstance(observations, list) or not observations:
        raise ValueError("Expected a nonempty data array")
    normalized: list[dict[str, str]] = []
    for item in observations:
        if item.get("idSistema") != SYSTEM_ID:
            raise ValueError("Unexpected system ID")
        observed = date.fromisoformat(item["date"][:10])
        if not START <= observed <= END:
            raise ValueError("Date outside requested interval")
        value = item.get("volumeUtilArmazenadoPorcentagem")
        if value is None:
            raise ValueError(f"Missing storage percentage at {observed}")
        storage = float(value)
        if not 0 <= storage <= 100:
            raise ValueError(f"Invalid storage percentage at {observed}")
        rain = item.get("chuva")
        normalized.append(
            {
                "date": observed.isoformat(),
                "system": "Cantareira",
                "storage_pct": str(storage),
                "rain_mm": "" if rain is None else str(float(rain)),
            }
        )
    normalized.sort(key=lambda row: row["date"])
    if len({row["date"] for row in normalized}) != len(normalized):
        raise ValueError("Duplicate dates in source")
    return normalized


def main() -> None:
    request = Request(URL, headers={"User-Agent": "GS-FIAP-academic-research/1.0"})
    with urlopen(request, timeout=45) as response:
        raw = response.read()
    payload = json.loads(raw)
    rows = normalize(payload)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(raw)
    with CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "system", "storage_pct", "rain_mm"])
        writer.writeheader()
        writer.writerows(rows)
    METADATA.write_text(
        json.dumps(
            {
                "source_page": "https://mananciais.sabesp.com.br/base-dados",
                "data_url": URL,
                "system_id": SYSTEM_ID,
                "system": "Cantareira",
                "period_start": rows[0]["date"],
                "period_end": rows[-1]["date"],
                "rows": len(rows),
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "sha256_raw": hashlib.sha256(raw).hexdigest(),
                "units": {"storage_pct": "% of useful stored volume", "rain_mm": "mm (daily rain)"},
                "license": "Not located; raw data excluded from repository pending confirmation",
                "endpoint_status": "Used by Sabesp website JS; not confirmed as documented public API",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Downloaded {len(rows)} daily observations: {rows[0]['date']}..{rows[-1]['date']}")
    print(CSV)


if __name__ == "__main__":
    main()
