# Síntese executiva — Cantareira (rascunho)

**Global Solution 2026.2 — Data Science and Analytics**  
**Integrantes:** inserir nomes e RMs antes da entrega  
**Estado:** experimento exploratório; ainda não é alerta operacional

## Problema e pergunta

A gestão hídrica da RMSP precisa acompanhar a evolução dos sistemas produtores sem transformar uma previsão isolada em anúncio de crise. Investigamos: **com que erro se pode estimar o volume útil (%) do Sistema Cantareira em 1 e 7 dias, usando dados já publicados?** Esta pergunta técnica é um primeiro passo; não estima falta de água em bairros.

## Dados e indicador

Usamos 731 registros diários de 01/01/2024 a 31/12/2025 obtidos do Portal dos Mananciais Sabesp. A série contém volume útil (%) e chuva (mm); não houve datas ausentes no intervalo. O indicador central é o volume útil armazenado em porcentagem. Fonte, URL, hash, transformação e limites constam em DATA_SOURCE.md. A licença de redistribuição e a estabilidade do endpoint precisam de confirmação; os dados ficam locais.

## Método e resultados

Treinamos com alvos anteriores a 01/07/2025 e testamos em 184 alvos de julho a dezembro de 2025, sem embaralhar datas. Comparamos persistência (amanhã igual a hoje), Ridge e Random Forest. As entradas são conhecidas até o dia da previsão, depois que seu registro é publicado. MAE em pontos percentuais:

| Horizonte | Persistência | Ridge | Random Forest |
|---|---:|---:|---:|
| 1 dia | 0,169 | **0,066** | 14,907 |
| 7 dias | 1,135 | **0,542** | 16,377 |

Ridge foi melhor neste único corte. A floresta falhou quando o volume do teste caiu abaixo do observado no treino; suas previsões quase não acompanharam o declínio. O erro baixo de 1 dia pode refletir a mudança lenta do reservatório, não antecipação de risco raro.

## Riscos e recomendação

**Não usar estes modelos para emitir alertas ao público ou orientar racionamento.** Antes disso, validar várias janelas temporais, esclarecer data/horário e qualidade das medições, incorporar outros sistemas e variáveis, definir limiares e incerteza com base oficial e submeter recomendações à revisão humana. Como próximo passo acadêmico, ampliar a pergunta para condições de vulnerabilidade hídrica e entregar análise reproduzível com interpretação dos erros.
