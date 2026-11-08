Integrantes: João Victor Alves de Abreu (RM 564946) e Rodrigo Kenshin Viana Matayoshi (RM 564026).

# Risco Hídrico no Sistema Cantareira — Data Science and Analytics

> Global Solution 2026.2 · FIAP · Monitoramento e previsão de riscos hídricos na Região Metropolitana de São Paulo

Análise de dados reais do **Sistema Cantareira** (Sabesp, 01/01/2024 a 07/11/2026) para antecipar a entrada do reservatório em **faixas de operação mais restritivas**, com indicadores hídricos, modelos de aprendizado de máquina validados no tempo e níveis de alerta para apoio à gestão.

| Entregável | Arquivo |
|---|---|
| Relatório (Opção 1: notebook executado do início ao fim) | [`notebooks/analise_risco_hidrico_cantareira.ipynb`](notebooks/analise_risco_hidrico_cantareira.ipynb) |
| Síntese executiva (1 página) | [`docs/Sintese_Executiva_Cantareira.pdf`](docs/Sintese_Executiva_Cantareira.pdf) |
| Dados reais e brutos mensais | [`data/`](data/) · proveniência em [`docs/DATA_SOURCE.md`](docs/DATA_SOURCE.md) |
| Rubrica × evidências | [`docs/RUBRICA.md`](docs/RUBRICA.md) |

## Pergunta de pesquisa

> Com dados publicados até o dia *t* (volume, chuva e vazões), é possível sinalizar com até **30 dias de antecedência** que o Cantareira vai entrar em uma faixa de operação mais restritiva?

As faixas são as da Resolução Conjunta ANA/DAEE nº 925/2017: **Normal** (≥ 60 % do volume útil), **Atenção** (40–60 %), **Alerta** (30–40 %), **Restrição** (20–30 %) e **Especial** (< 20 %). Cada mudança de faixa reduz a vazão que pode ser retirada, por isso o aviso antecipado tem valor prático para a gestão.

## Principais resultados

| Tarefa | Modelo | Resultado (validação *walk-forward*, jan/2025–set/2026) |
|---|---|---|
| Piora de faixa em 30 dias | **Regressão Logística** | recall 0,85 · precisão 0,61 · AUC 0,93 · F2 0,79 |
| | Random Forest | recall 0,38 · precisão 0,78 |
| | Regra de autonomia (referência) | recall 0,86 · precisão 0,59 |
| Variação do volume em 7 dias (MAE) | Ridge · Random Forest | 0,77 · 0,94 p.p. (tendência simples: 0,80) |
| Variação do volume em 30 dias (MAE) | Ridge · Random Forest | 3,94 · 3,91 p.p. (tendência simples: **3,22**) |

- **Antecipar piora de faixa é viável:** nas seis mudanças para faixa pior do período, o indicador de autonomia ficou abaixo de 30 dias entre 24 e 29 dias antes; a Regressão Logística identificou 85 % dos dias que antecederam pioras, com probabilidade interpretável.
- **Prever o volume exato em 30 dias não é:** nenhum modelo de ML superou a extrapolação da tendência nesse horizonte, porque o volume depende de chuvas ainda não observadas. O projeto documenta esse resultado negativo em vez de escondê-lo e usa a projeção apenas com intervalo de incerteza.
- **Situação em 07/11/2026:** 52,94 % (faixa 2), tendência +11,1 p.p. em 30 dias, sem sinal de piora → **nível ATENÇÃO**.

## Indicadores

| Indicador | Definição | Unidade |
|---|---|---|
| I1 · Volume útil e faixa | volume armazenado e faixa ANA/DAEE | % · faixa 1–5 |
| I2 · Tendência | `V(t) − V(t−30)` | p.p./30 dias |
| I3 · Balanço hídrico parcial | média 30 d da afluência − média 30 d da produção | m³/s |
| I4 · Chuva acumulada | soma de 30 dias | mm |
| I5 · Autonomia | dias até o limite da faixa se o ritmo de queda continuar | dias (máx. 365) |

## Metodologia

1. **Dados:** série diária do Portal dos Mananciais (volume útil, chuva, vazão natural e vazão produzida), extraída mês a mês e conferida com uma extração anterior independente (6 de 6 estatísticas idênticas).
2. **Qualidade:** sem lacunas, duplicidades ou valores fora da faixa física; checagem de coerência física (variação do estoque × balanço, correlação 0,99).
3. **EDA:** série com faixas, sazonalidade mensal, correlações e relação balanço × variação do volume.
4. **Modelagem:** atributos calculados só com dados até *t*; alvo em *t + h*; **7 janelas trimestrais de teste** com treino restrito a alvos anteriores a cada janela (sem vazamento temporal); comparação obrigatória com referências simples.
5. **Métricas orientadas ao custo do erro:** como deixar de avisar uma piora custa mais que um aviso preventivo, a classificação prioriza **recall** e **F2**.
6. **Alertas:** Normal / Atenção / Alerta / Crítico a partir da faixa oficial, subindo um nível quando há sinal de piora; sempre como recomendação para avaliação humana.

## Como reproduzir

Requisitos: Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m unittest discover -s tests -v          # 15 testes
jupyter notebook notebooks/analise_risco_hidrico_cantareira.ipynb   # Kernel > Restart & Run All
python scripts/build_executive_summary.py        # regenera a síntese em PDF
```

Os dados já estão em `data/`. Para baixá-los novamente da Sabesp: `python -m src.fetch_sabesp 2024-01-01 2026-11-07` (o endpoint não é documentado e pode mudar).

## Estrutura

```text
data/
  cantareira_diario_2024_2026.csv   série consolidada (1.042 dias)
  raw/monthly/AAAA-MM.csv           extração mensal bruta
docs/
  Sintese_Executiva_Cantareira.pdf  síntese executiva (1 página)
  DATA_SOURCE.md                    proveniência, variáveis e limitações
  RUBRICA.md                        critérios de avaliação × evidências
notebooks/
  analise_risco_hidrico_cantareira.ipynb   relatório executado
reports/results.json                métricas exportadas pelo notebook
scripts/
  build_notebook.py                 gera a estrutura do notebook
  build_executive_summary.py        gera a síntese em PDF
src/
  hydro.py                          faixas, indicadores, atributos e validação temporal
  fetch_sabesp.py                   extração e normalização dos dados da Sabesp
  quality.py                        checagem de qualidade de CSV
tests/                              testes unitários (faixas, indicadores, vazamento, extração)
```

## Limitações e uso responsável

- Um único sistema produtor, menos de três anos e seis mudanças de faixa: métricas com incerteza amostral relevante.
- Sem vazão de jusante, evaporação, transferências entre sistemas ou previsão de chuva.
- Endpoint da Sabesp não documentado; termos de redistribuição não localizados — uso acadêmico com atribuição à fonte.
- Os alertas organizam evidências para quem decide; **não** confirmam crise nem autorizam racionamento, que dependem da avaliação dos gestores competentes.
- Não há dados pessoais no projeto.

## Uso de IA generativa

Usamos IA generativa como ferramenta de apoio (dúvidas, sugestões de código, depuração e revisão de textos). Todas as métricas e interpretações foram conferidas pela dupla nos resultados executados do notebook.

## Fontes

- Sabesp — [Portal dos Mananciais, base de dados](https://mananciais.sabesp.com.br/base-dados)
- ANA — [Sala de Situação do Sistema Cantareira (boletins)](https://www.gov.br/ana/pt-br/sala-de-situacao/sistema-cantareira) · Resolução Conjunta ANA/DAEE nº 925/2017
