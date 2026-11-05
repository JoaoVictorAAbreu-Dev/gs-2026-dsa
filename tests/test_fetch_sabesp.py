import unittest

from src.fetch_sabesp import normalize


class NormalizeTests(unittest.TestCase):
    def test_normalize_realistic_shape(self):
        source = {"data": [{"idSistema": 64, "date": "2024-01-01T00:00:00", "volumeUtilArmazenadoPorcentagem": 71.2, "chuva": 0}]}
        self.assertEqual(normalize(source)[0]["storage_pct"], "71.2")

    def test_reject_wrong_system(self):
        source = {"data": [{"idSistema": 65, "date": "2024-01-01T00:00:00", "volumeUtilArmazenadoPorcentagem": 71.2}]}
        with self.assertRaisesRegex(ValueError, "system ID"):
            normalize(source)


if __name__ == "__main__":
    unittest.main()
