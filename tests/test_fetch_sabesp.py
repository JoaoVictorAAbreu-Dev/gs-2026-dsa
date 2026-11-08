import unittest
from datetime import date

from src.fetch_sabesp import months, normalize

ITEM = {"idSistema": 64, "date": "2024-01-01T00:00:00", "volumeUtilArmazenadoPorcentagem": 71.39608,
        "chuva": 0, "vazaoNatural": 10.918, "vazaoProduzida": 24.3946}


class NormalizeTests(unittest.TestCase):
    def test_normaliza_formato_do_portal(self):
        row = normalize({"data": [ITEM]}, date(2024, 1, 1), date(2024, 1, 31))[0]
        self.assertEqual(row["storage_pct"], "71.39608")
        self.assertEqual(row["natural_inflow_m3s"], "10.91800")

    def test_rejeita_outro_sistema(self):
        with self.assertRaisesRegex(ValueError, "system ID"):
            normalize({"data": [{**ITEM, "idSistema": 65}]}, date(2024, 1, 1), date(2024, 1, 31))

    def test_rejeita_variavel_ausente(self):
        with self.assertRaisesRegex(ValueError, "vazaoNatural"):
            normalize({"data": [{k: v for k, v in ITEM.items() if k != "vazaoNatural"}]}, date(2024, 1, 1), date(2024, 1, 31))

    def test_meses_cobrem_o_intervalo(self):
        blocos = list(months(date(2025, 12, 15), date(2026, 2, 3)))
        self.assertEqual(blocos[0], (date(2025, 12, 15), date(2025, 12, 31)))
        self.assertEqual(blocos[-1], (date(2026, 2, 1), date(2026, 2, 3)))
        self.assertEqual(len(blocos), 3)


if __name__ == "__main__":
    unittest.main()
