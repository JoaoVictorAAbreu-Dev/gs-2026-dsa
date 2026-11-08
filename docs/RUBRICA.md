# Critérios de avaliação × evidências

| Critério (PDF, seção 9) | Onde está | Destaques |
|---|---|---|
| Definição do problema e qualidade dos dados | Notebook §1–2 · `DATA_SOURCE.md` | Pergunta investigável ligada às faixas oficiais; fonte real, período, frequência, variáveis, limitações e verificação cruzada |
| Preparação e tratamento | Notebook §2 · `src/hydro.load_series` · `src/fetch_sabesp.py` | Checagem de lacunas, duplicidades, ausentes e faixas físicas; checagem física do balanço; dados brutos mensais rastreáveis |
| Análise exploratória e estatística | Notebook §3 | Série com faixas, sazonalidade mensal, correlação de Spearman, balanço × variação do volume, panorama dos 7 sistemas da RMSP |
| Indicadores hídricos | Notebook §4 · `src/hydro.add_indicators` | 5 indicadores com fórmula, unidade, periodicidade e interpretação; indicador combinado de autonomia |
| Modelagem e avaliação | Notebook §5 | 2 tarefas (regressão e classificação), 4 modelos de ML, referências simples, validação *walk-forward* em 7 janelas, validação histórica mensal 2010–2026 (17 pioras de faixa), métricas escolhidas pelo custo do erro, análise dos erros |
| Riscos e alertas | Notebook §6 | Critérios documentados (faixa oficial + sinal de piora), histórico dos níveis, situação atual com intervalo de incerteza |
| Visualizações | Notebook (7 figuras) · síntese | Cores consistentes por faixa e nível, títulos e unidades em todos os gráficos |
| Comunicação e recomendações | Notebook §7 · `Sintese_Executiva_Cantareira.pdf` | Resposta direta à pergunta, 4 recomendações acionáveis, síntese de 1 página |
| Reprodutibilidade e responsabilidade | README · `tests/` · Notebook §8 | Dados versionados, semente fixa, 15 testes (incluindo vazamento temporal), limites, vieses, privacidade e supervisão humana |

**Além do pedido:** validação em 16 anos de história (incluindo a crise de 2014–2015), panorama de todos os sistemas da RMSP, extensão da série até 07/11/2026 (situação atual real), validação em várias janelas temporais em vez de um corte único, alinhamento dos níveis de alerta à regra regulatória oficial, checagem física do balanço hídrico e documentação de um resultado negativo (ML × tendência em 30 dias).
