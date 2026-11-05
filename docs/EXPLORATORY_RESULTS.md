# Experimento exploratório — volume útil do Cantareira

Executado em 05/11/2026 com a série descrita em `DATA_SOURCE.md`. Pergunta técnica inicial: **quão bem se estima a porcentagem de volume útil do Cantareira no dia seguinte?** Ela ainda não equivale à pergunta final sobre risco hídrico da prova.

Treino: 539 exemplos cujo alvo antecede 01/07/2025. Teste: 184 exemplos com alvo de 01/07/2025 a 31/12/2025. As entradas usam volume atual, média de sete dias, variação de sete dias, chuva atual e chuva acumulada de sete dias; o alvo é sempre o dia seguinte. Métricas em pontos percentuais:

| Método | MAE | RMSE | Interpretação |
|---|---:|---:|---|
| Persistência (volume amanhã = hoje) | 0,169 | 0,183 | Baseline simples e forte num horizonte curto. |
| Ridge | 0,066 | 0,096 | Melhor neste corte temporal; precisa validação em outras janelas. |
| Random Forest | 14,907 | 17,161 | Falha grave neste teste: o volume caiu abaixo do intervalo observado no treino, e árvores não extrapolam bem. Não usar em alertas. |

EDA: 731 dias sem lacunas de data; volume útil observado entre 19,68% e 78,12%, mediana 54,39%; chuva total somada 2.489,9 mm, com 400 dias de valor zero no campo da fonte. Esses números descrevem somente o arquivo extraído e não foram verificados contra boletins independentes.

**Conclusão limitada:** o recorte de teste inclui queda acentuada do volume em 2025. Uma regressão linear acompanhou a tendência de um dia para o outro, enquanto a floresta ficou quase constante. Ainda não há validação por múltiplos cortes, comparação com horizonte operacional de interesse, limiares documentados de risco, estimativa de incerteza nem recomendação acionável para gestores. Os resultados não autorizam comunicação de crise ou racionamento.

Saídas locais reproduzíveis: `reports/results.json` e `reports/overview.png`.
