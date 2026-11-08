import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src import hydro


def serie(volumes, start="2025-01-01"):
    n = len(volumes)
    return pd.DataFrame({"date": pd.date_range(start, periods=n), "system": "X", "storage_pct": volumes,
                         "rain_mm": np.zeros(n), "natural_inflow_m3s": np.full(n, 10.0),
                         "produced_flow_m3s": np.full(n, 25.0)})


class FaixaTests(unittest.TestCase):
    def test_limites_oficiais(self):
        self.assertEqual([hydro.faixa(v) for v in (60, 59.99, 40, 30, 20, 19.9)], [1, 2, 2, 3, 4, 5])

    def test_faixa_estendida_reserva_tecnica(self):
        self.assertEqual(hydro.faixa_estendida(-12.5), 5)
        self.assertEqual(hydro.faixa_estendida(102.7), 1)

    def test_volume_invalido(self):
        with self.assertRaises(ValueError):
            hydro.faixa(101)

    def test_nivel_sobe_com_sinal_de_piora(self):
        self.assertEqual(hydro.NIVEIS[hydro.nivel_alerta(2, 2)], "Atenção")
        self.assertEqual(hydro.NIVEIS[hydro.nivel_alerta(2, 3)], "Alerta")
        self.assertEqual(hydro.NIVEIS[hydro.nivel_alerta(4, 5)], "Crítico")


class IndicadoresTests(unittest.TestCase):
    def test_tendencia_e_autonomia(self):
        # queda de 0,1 p.p./dia a partir de 45 %: 5 p.p. até o limite de 40 % => 50 dias
        ind = hydro.add_indicators(serie(np.linspace(54, 45, 91)))
        ult = ind.iloc[-1]
        self.assertAlmostEqual(ult.trend_30d, -3.0, places=6)
        self.assertAlmostEqual(ult.autonomia_dias, 50.0, places=6)
        self.assertAlmostEqual(ult.balance_30d, -15.0)

    def test_sem_queda_autonomia_maxima(self):
        ind = hydro.add_indicators(serie(np.linspace(40, 50, 91)))
        self.assertEqual(ind.iloc[-1].autonomia_dias, 365)


class SemVazamentoTests(unittest.TestCase):
    def test_alvo_usa_futuro_e_atributos_nao(self):
        vol = np.linspace(70, 35, 200)
        tab = hydro.feature_table(serie(vol), horizon=30)
        linha = tab.iloc[0]
        i = int((linha.date - pd.Timestamp("2025-01-01")).days)
        self.assertAlmostEqual(linha.target_delta, vol[i + 30] - vol[i])
        self.assertAlmostEqual(linha.storage_pct, vol[i])

    def test_treino_termina_antes_do_teste(self):
        tab = hydro.feature_table(serie(np.linspace(70, 35, 300)), horizon=30)
        fold = hydro.walk_forward_folds("2025-08-01", "2025-09-30", months=2)[0]
        treino, teste = hydro.split_fold(tab, fold)
        self.assertLess(treino.target_date.max(), fold.inicio)
        self.assertGreaterEqual(teste.date.min(), fold.inicio)

    def test_serie_com_lacuna_rejeitada(self):
        s = serie(np.linspace(70, 60, 10)).drop(index=4)
        with tempfile.TemporaryDirectory() as pasta:
            path = Path(pasta) / "serie.csv"
            s.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "contínua"):
                hydro.load_series(path)


if __name__ == "__main__":
    unittest.main()
