"""Build an unexecuted source notebook and a local executed submission candidate."""

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks/analysis.ipynb"
EXECUTED = ROOT / "deliverables/GS2026_DSA_Cantareira_executed.ipynb"


def build() -> None:
    notebook = nbf.v4.new_notebook(
        metadata={
            "kernelspec": {
                "display_name": "GS DSA (local)",
                "language": "python",
                "name": "gs-dsa",
            },
            "language_info": {"name": "python"},
        }
    )
    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# GS 2026.2 — Data Science and Analytics\n"
            "## Cantareira: volume útil em 1 e 7 dias\n\n"
            "Projeto acadêmico exploratório. Substituir esta linha pelos nomes/RMs dos integrantes antes da entrega. "
            "Fonte: [Portal dos Mananciais Sabesp](https://mananciais.sabesp.com.br/base-dados). "
            "Extração e limites documentados em `docs/DATA_SOURCE.md`. "
            "Este notebook baixa a série oficial observada no site e usa apenas dados locais para a análise. "
            "O endpoint não está confirmado como API pública estável. "
            "Os resultados não são alertas de escassez nem decisões de racionamento."
        ),
        nbf.v4.new_markdown_cell(
            "## Pergunta e método\n\n"
            "Pergunta técnica inicial: quão bem podemos estimar o volume útil (%) do Cantareira em 1 e 7 dias? "
            "No instante da previsão, usamos o registro do dia `t` **depois de ele ter sido publicado no portal**, "
            "para estimar `t+1` ou `t+7`. Não presumimos disponibilidade desses dados no início do dia `t`. "
            "Se o horário efetivo ou a semântica da data não forem confirmados, a aplicação em tempo real permanece pendente. "
            "A divisão temporal é pelo dia do alvo; não há embaralhamento. "
            "Persistência é o baseline; Ridge e Random Forest são os dois modelos de ML comparados."
        ),
        nbf.v4.new_code_cell(
            "from src.fetch_sabesp import main as fetch_data, CSV, METADATA\n"
            "from src.quality import inspect_csv\n"
            "from src.analyze import run\n"
            "from dataclasses import asdict\n"
            "from IPython.display import display, Image\n"
            "import json\n"
            "fetch_data()\n"
            "print(json.dumps(json.loads(METADATA.read_text()), ensure_ascii=False, indent=2))"
        ),
        nbf.v4.new_markdown_cell(
            "## Qualidade da série\n\n"
            "Verificamos sistema, intervalo, valores, duplicatas e lacunas entre datas diárias. "
            "A fonte pode revisar valores; o SHA-256 permite detectar alterações no JSON recuperado."
        ),
        nbf.v4.new_code_cell(
            "quality = inspect_csv(CSV, 'Sabesp Portal dos Mananciais')\n"
            "print(json.dumps({**asdict(quality), 'usable': quality.usable}, ensure_ascii=False, indent=2))\n"
            "assert quality.usable and not any(quality.date_gaps.values())"
        ),
        nbf.v4.new_markdown_cell(
            "## EDA, indicador e modelagem\n\n"
            "Indicador principal: volume útil armazenado (%), diário, conforme a série Sabesp. "
            "Média e variação em sete dias são atributos calculados para a previsão. "
            "Também usamos chuva diária e soma de sete dias como informação contextual. "
            "A variável alvo é o volume útil (%) 1 ou 7 dias depois. "
            "As métricas MAE e RMSE estão em **pontos percentuais**."
        ),
        nbf.v4.new_code_cell(
            "result = run()\n"
            "print(json.dumps(result, ensure_ascii=False, indent=2))\n"
            "display(Image(filename='reports/overview.png'))"
        ),
        nbf.v4.new_markdown_cell(
            "## Interpretação e limites\n\n"
            "O horizonte de um dia pode produzir erros pequenos pela forte continuidade do volume. "
            "Isso **não** demonstra previsão confiável de escassez, especialmente em horizontes maiores. "
            "A Random Forest pode falhar ao encontrar volumes fora da faixa do treino, pois árvores não extrapolam bem. "
            "Comparar sempre com persistência; não selecionar um modelo apenas por uma única divisão temporal. "
            "Uma decisão operacional exigiria validação em vários períodos, critérios de criticidade fundamentados, "
            "incerteza e supervisão humana. Não há dados de distribuição por bairro, portanto não inferimos interrupção de abastecimento."
        ),
        nbf.v4.new_markdown_cell(
            "## Próximos passos para a entrega\n\n"
            "Confirmar licença de redistribuição e prazo no Portal do Aluno; ampliar a investigação para pergunta de risco hídrico, "
            "validar em várias janelas temporais, definir critérios de alerta com fonte oficial e preparar a síntese executiva "
            "de uma página. Esta versão é um incremento verificável, ainda não a entrega final."
        ),
    ]
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    EXECUTED.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, SOURCE)
    client = NotebookClient(notebook, timeout=120, kernel_name="gs-dsa", resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    nbf.write(notebook, EXECUTED)
    print(SOURCE)
    print(EXECUTED)


if __name__ == "__main__":
    build()
