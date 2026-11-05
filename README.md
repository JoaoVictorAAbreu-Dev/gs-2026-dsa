# GS 2026.2 — Data Science and Analytics

Projeto de monitoramento e análise de riscos hídricos na RMSP. **Estado:** experimento exploratório com uma série real do Cantareira e dois modelos de regressão para horizontes de 1 e 7 dias. Ainda não há alerta de risco validado nem entrega final.

## Reproduzir localmente

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m src.fetch_sabesp
.venv/bin/python -m src.quality data/processed/cantareira_daily.csv --source "Sabesp Portal dos Mananciais"
.venv/bin/python -m src.analyze
.venv/bin/python scripts/build_notebook.py
.venv/bin/python -m unittest discover -s tests -v
```

Os arquivos brutos, processados e relatórios gerados ficam locais e ignorados pelo Git até confirmar os termos de reutilização da Sabesp. A extração usa um endpoint observado no site, **sem garantia de API pública estável**. Consulte [docs/DATA_SOURCE.md](docs/DATA_SOURCE.md) para proveniência e limitações.

O script de normalização gera `date,system,storage_pct,rain_mm`. A hipótese de 0 a 100% vale para este recorte do Cantareira, não para todos os sistemas. Consulte `docs/REQUIREMENTS.md` antes de ampliar o projeto.

O notebook-fonte fica em `notebooks/analysis.ipynb`. A cópia executada em `deliverables/` e a síntese em `docs/EXECUTIVE_SUMMARY.md` são **candidatas à entrega**, ainda sujeitas à revisão acadêmica e de licença.
