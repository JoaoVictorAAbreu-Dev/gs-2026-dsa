# Progresso

- 2026-11-05: PDF oficial lido; DSA confirmada como Data Science and Analytics.
- 2026-11-05: 731 observações diárias reais do Cantareira (2024–2025) obtidas do portal Sabesp e validadas; origem e hash em `docs/DATA_SOURCE.md`. Licença de redistribuição não encontrada; arquivos locais ignorados no Git.
- 2026-11-05: experimento temporal para volume útil (%) em 1 e 7 dias, com persistência, Ridge e Random Forest. Resultados e limitações em `docs/EXPLORATORY_RESULTS.md`. Oito testes unitários passaram.
- 2026-11-05 (revisão): modelos passam a prever a variação (RF de 14,9 para 0,064 p.p. em 1 dia); backtest em cinco janelas; indicadores com fórmula/unidade/interpretação; viés e erro máximo; notebook com kernel `python3`, execução offline e a partir de `notebooks/`; 13 testes passaram.
- 2026-11-05: a nota da prova exige níveis de risco e alertas fundamentados; a classificação diária usa limites de volume derivados da Resolução ANA/DAEE 925/2017 como regra exploratória, com avaliação de falso negativo/falso alerta fora da amostra; 15 testes passaram. Não equivale ao enquadramento operacional mensal da ANA/DAEE.
- Pendente: confirmar licença/termos e estabilidade do endpoint; intervalos de incerteza; alertas somente com critérios fundamentados; nomes/RMs; regenerar a cópia executada do notebook localmente.
