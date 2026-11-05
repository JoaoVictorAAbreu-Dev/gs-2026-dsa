# Experimento exploratório — volume útil do Cantareira

Executado em 05/11/2026 com a série descrita em DATA_SOURCE.md. Pergunta técnica inicial: **quão bem se estima a porcentagem de volume útil do Cantareira em 1 e 7 dias?** Ela ainda não equivale à pergunta final sobre risco hídrico da prova.

Treino: alvos anteriores a 01/07/2025 (539 exemplos para 1 dia; 533 para 7 dias). Teste: 184 alvos de 01/07/2025 a 31/12/2025 em cada horizonte. As entradas usam volume do dia t, média e variação dos últimos sete dias, chuva do dia t e chuva acumulada de sete dias. O alvo é o volume de t+1 ou t+7; os modelos aprendem a variação até lá e a somam ao volume de t. **Uma previsão só seria emitida depois da publicação dos dados de t.** A disponibilidade operacional e a semântica exata da data da chuva ainda precisam de confirmação. Nenhuma entrada usa valores futuros.

| Horizonte | Método | MAE (pontos percentuais) | RMSE (pontos percentuais) |
|---|---|---:|---:|
| 1 dia | Persistência | 0,169 | 0,183 |
| 1 dia | Ridge | 0,049 | 0,075 |
| 1 dia | Random Forest | 0,064 | 0,087 |
| 7 dias | Persistência | 1,135 | 1,220 |
| 7 dias | Ridge | 0,524 | 0,628 |
| 7 dias | Random Forest | 1,394 | 1,506 |

EDA: 731 dias sem lacunas; volume útil entre 19,68% e 78,12%, mediana 54,39%; soma de chuva 2.489,9 mm e 400 dias de valor zero. Esses números descrevem o arquivo extraído e não foram verificados contra boletins independentes.

**Correção metodológica (05/11/2026):** a primeira versão previa o nível e a Random Forest errava 14,9 p.p. em 1 dia, porque o teste (19,7–47,3%) ficou abaixo de toda a faixa de treino (44,7–78,1%) e árvores não extrapolam. Prevendo a variação, o erro caiu para 0,064 p.p.

**Backtest (origem móvel, 5 janelas de 3 meses, out/2024–dez/2025), MAE médio:** 1 dia — persistência 0,169, Ridge 0,075, Random Forest 0,084; 7 dias — persistência 1,066, Ridge 0,662, Random Forest 0,932. Ridge venceu a persistência em 5/5 janelas nos dois horizontes; a floresta em 5/5 e 4/5.

**Interpretação:** persistência é um baseline forte porque o volume muda gradualmente. O erro de Ridge em 1 dia é plausível nesse contexto, mas não prova antecipação de escassez. Em 7 dias, no período de queda, os modelos foram otimistas (viés Ridge +0,37 p.p.; floresta +1,38 p.p.): superestimar água é o erro mais grave porque gera falsa tranquilidade.

**Limites:** um único sistema; sem limiares de risco, intervalos de incerteza ou validação com especialistas. Os dados não permitem inferir interrupção por bairro nem justificar racionamento. Os resultados não são alertas operacionais.

Saídas locais: reports/results.json e reports/overview.png. Ambas são ignoradas no Git até confirmar licença de redistribuição.
