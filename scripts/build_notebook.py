"""Build an unexecuted source notebook and a local executed submission candidate."""

import sys
from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks/analysis.ipynb"
EXECUTED = ROOT / "deliverables/GS2026_DSA_Cantareira_executed.ipynb"

SETUP = """\
# Funciona aberto da raiz do projeto ou de notebooks/: localiza a pasta que contém src/.
import os, sys
from pathlib import Path
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src' / 'analyze.py').exists())
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import json
from dataclasses import asdict
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Image
from src.fetch_sabesp import main as fetch_data, CSV, METADATA
from src.quality import inspect_csv
from src.analyze import run, indicator_table, INDICATORS

# Baixa a série apenas se a cópia local não existir (reexecução offline possível).
if not CSV.exists():
    fetch_data()
print(json.dumps(json.loads(METADATA.read_text()), ensure_ascii=False, indent=2))"""

QUALITY = """\
quality = inspect_csv(CSV, 'Sabesp Portal dos Mananciais')
print(json.dumps({**asdict(quality), 'usable': quality.usable}, ensure_ascii=False, indent=2))
assert quality.usable and not any(quality.date_gaps.values())"""

EDA = """\
frame = pd.read_csv(CSV, parse_dates=['date'])
display(frame[['storage_pct', 'rain_mm']].describe().round(2))
monthly = frame.set_index('date').resample('MS').agg(
    volume_medio_pct=('storage_pct', 'mean'), volume_min_pct=('storage_pct', 'min'), chuva_mm=('rain_mm', 'sum'))
display(monthly.round(1))
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(monthly.index, monthly['volume_medio_pct'], marker='o', color='#146c94', label='Volume útil médio (%)')
ax.set_ylabel('% do volume útil')
ax2 = ax.twinx()
ax2.bar(monthly.index, monthly['chuva_mm'], width=20, alpha=0.3, color='#0a9396', label='Chuva no mês (mm)')
ax2.set_ylabel('mm')
ax.set_title('Cantareira — volume útil médio e chuva mensal (Sabesp)')
fig.legend(loc='upper right')
plt.show()"""

INDICATORS_CELL = """\
display(pd.DataFrame(INDICATORS).T)
indicators = indicator_table(frame)
display(indicators.dropna().set_index('date').tail(10).round(2))
print('Pior variação em 30 dias (p.p.):', round(indicators['storage_change_30d_pp'].min(), 2),
      'em', indicators.loc[indicators['storage_change_30d_pp'].idxmin(), 'date'].date())"""

MODELS = """\
result = run()
def mae_table(metrics):
    return pd.DataFrame(metrics).T.round(3)
print('Horizonte de 1 dia (teste jul–dez/2025)'); display(mae_table(result['metrics']))
print('Horizonte de 7 dias (teste jul–dez/2025)'); display(mae_table(result['seven_day_horizon']['metrics']))
display(Image(filename='reports/overview.png'))"""

BACKTEST = """\
for key, label in [('one_day', '1 dia'), ('seven_day', '7 dias')]:
    bt = result['backtest'][key]
    folds = pd.DataFrame({f['origin']: f['mae_percentage_points'] for f in bt['folds']}).T
    print(f'Backtest {label}: MAE (p.p.) por janela de 3 meses')
    display(folds.round(3))
    print('Janelas em que o modelo venceu a persistência:', bt['folds_beating_persistence'])"""


def cells() -> list:
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    return [
        md(
            "# GS 2026.2 — Data Science and Analytics\n"
            "## Cantareira: volume útil em 1 e 7 dias\n\n"
            "**Integrantes:** substituir pelos nomes e RMs antes da entrega.\n\n"
            "Fonte: [Portal dos Mananciais Sabesp](https://mananciais.sabesp.com.br/base-dados). "
            "Extração e limites documentados em `docs/DATA_SOURCE.md`. O endpoint não está confirmado como API pública estável. "
            "Os resultados não são alertas de escassez nem decisões de racionamento."
        ),
        md(
            "## Pergunta e método\n\n"
            "Pergunta técnica: **com que erro se estima o volume útil (%) do Cantareira em 1 e 7 dias?** "
            "Usamos o registro do dia `t` depois de publicado para estimar `t+1` ou `t+7`. "
            "A divisão é temporal pelo dia do alvo, sem embaralhamento. "
            "Persistência (amanhã igual a hoje) é o baseline; **Ridge** e **Random Forest** são os dois modelos de ML. "
            "Os modelos aprendem a **variação** do volume (p.p.) e somam ao volume atual: uma floresta que previsse o nível "
            "não conseguiria extrapolar, porque o volume do período de teste ficou abaixo de tudo o que existia no treino."
        ),
        code(SETUP),
        md("## Qualidade da série\n\nVerificamos sistema, intervalo, valores, duplicatas e lacunas. O SHA-256 permite detectar revisões no JSON da fonte."),
        code(QUALITY),
        md(
            "## Análise exploratória\n\n"
            "Estatísticas descritivas, resumo mensal e gráfico de volume médio com chuva mensal. "
            "Leitura esperada: o volume cai na estação seca (abril–setembro) e a recuperação depende da chuva do verão; "
            "em 2025 a recuperação não ocorreu e o volume terminou o ano perto de 20%."
        ),
        code(EDA),
        md(
            "## Indicadores hídricos\n\n"
            "Cada indicador tem fórmula, unidade, periodicidade e interpretação (tabela abaixo). "
            "Não usamos limiares oficiais de estágio; as variações servem para apoiar revisão humana, não para classificar risco."
        ),
        code(INDICATORS_CELL),
        md("## Modelos e avaliação\n\nMétricas em **pontos percentuais**: MAE, RMSE, viés (positivo = otimista, prevê mais água que a real) e maior erro absoluto."),
        code(MODELS),
        md("## Validação em várias janelas\n\nBacktest com origem móvel: cada janela treina com tudo antes da origem e testa os três meses seguintes."),
        code(BACKTEST),
        md(
            "## Interpretação, consequências dos erros e alertas\n\n"
            "- A persistência já é forte porque o volume muda devagar; um modelo só é útil se vencê-la de forma consistente. "
            "Ridge venceu em todas as janelas nos dois horizontes; a Random Forest venceu em 1 dia e foi mais instável em 7 dias.\n"
            "- **Consequência dos erros:** superestimar o volume durante uma queda (viés positivo) é o erro mais grave, "
            "pois transmite falsa tranquilidade. Em 7 dias os modelos foram otimistas no período de queda; por isso o viés é reportado junto do MAE.\n"
            "- **Alertas:** este trabalho **não emite alertas**. Para emiti-los seria preciso limiares fundamentados em fonte oficial, "
            "intervalos de incerteza e revisão humana. Os indicadores de variação apenas sinalizam períodos que merecem análise.\n"
            "- Um sistema não representa toda a RMSP e não há dados por bairro; não inferimos interrupção de abastecimento."
        ),
        md(
            "## Recomendações e próximos passos\n\n"
            "Confirmar licença de redistribuição e prazo no Portal do Aluno; incorporar outros sistemas produtores; "
            "estimar intervalos de incerteza; validar a interpretação com quem comunica indicadores hídricos."
        ),
    ]


def build(execute: bool = True) -> None:
    notebook = nbf.v4.new_notebook(
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        }
    )
    notebook.cells = cells()
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, SOURCE)
    print(SOURCE)
    if execute:
        from nbclient import NotebookClient

        EXECUTED.parent.mkdir(parents=True, exist_ok=True)
        client = NotebookClient(notebook, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})
        client.execute()
        nbf.write(notebook, EXECUTED)
        print(EXECUTED)


if __name__ == "__main__":
    build(execute="--no-execute" not in sys.argv)
