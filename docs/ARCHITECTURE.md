# Arquitetura inicial

Pipeline em Python: JSON da Sabesp com proveniência → normalização explícita (`src.fetch_sabesp`) → checagem de qualidade (`src.quality`) → EDA e indicador de volume útil (%) → separação temporal → persistência, Ridge e Random Forest → MAE/RMSE e gráfico (`src.analyze`). O período de teste começa em 01/07/2025; cada linha usa somente valores conhecidos no dia `t` para estimar o volume de `t+1` ou `t+7`, após a publicação dos dados de `t`. A semântica exata da data da chuva e o horário operacional precisam de confirmação.

Os dados locais e resultados são ignorados no Git até confirmar licença. Ainda faltam múltiplos sistemas/variáveis, análise de risco/alerta, avaliação mais robusta e os entregáveis da prova. O modelo não estima interrupção de abastecimento ou decisão de racionamento.
