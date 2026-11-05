# Experimento exploratório — volume útil do Cantareira

Executado em 05/11/2026 com a série descrita em DATA_SOURCE.md. Pergunta técnica inicial: **quão bem se estima a porcentagem de volume útil do Cantareira em 1 e 7 dias?** Ela ainda não equivale à pergunta final sobre risco hídrico da prova.

Treino: alvos anteriores a 01/07/2025 (539 exemplos para 1 dia; 533 para 7 dias). Teste: 184 alvos de 01/07/2025 a 31/12/2025 em cada horizonte. As entradas usam volume do dia t, média e variação dos últimos sete dias, chuva do dia t e chuva acumulada de sete dias. O alvo é o volume de t+1 ou t+7. **Uma previsão só seria emitida depois da publicação dos dados de t.** A disponibilidade operacional e a semântica exata da data da chuva ainda precisam de confirmação. Nenhuma entrada usa valores futuros.

| Horizonte | Método | MAE (pontos percentuais) | RMSE (pontos percentuais) |
|---|---|---:|---:|
| 1 dia | Persistência | 0,169 | 0,183 |
| 1 dia | Ridge | 0,066 | 0,096 |
| 1 dia | Random Forest | 14,907 | 17,161 |
| 7 dias | Persistência | 1,135 | 1,220 |
| 7 dias | Ridge | 0,542 | 0,650 |
| 7 dias | Random Forest | 16,377 | 18,548 |

EDA: 731 dias sem lacunas; volume útil entre 19,68% e 78,12%, mediana 54,39%; soma de chuva 2.489,9 mm e 400 dias de valor zero. Esses números descrevem o arquivo extraído e não foram verificados contra boletins independentes.

**Interpretação:** persistência é um baseline forte porque o volume muda gradualmente. O erro de Ridge de 0,066 ponto percentual em 1 dia é plausível nesse contexto, mas não prova antecipação de escassez. A Random Forest falhou gravemente: o período de teste trouxe volumes abaixo da faixa do treino, e árvores não extrapolam esse declínio. O gráfico local mostra suas previsões quase constantes. Não usar essa floresta em alertas.

**Limites:** apenas um corte temporal e um sistema; sem backtesting por várias janelas, limiares de risco, intervalos de incerteza ou validação com especialistas. Os dados não permitem inferir interrupção por bairro nem justificar racionamento. Os resultados não são alertas operacionais.

Saídas locais: reports/results.json e reports/overview.png. Ambas são ignoradas no Git até confirmar licença de redistribuição.
