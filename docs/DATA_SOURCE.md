# Fonte da série real — Cantareira

Consulta feita em **05/11/2026** ao [Portal dos Mananciais da Sabesp](https://mananciais.sabesp.com.br/base-dados). O JavaScript servido pelo próprio portal usa o caminho `/api/v4/sistemas/{id}/dados/{periodicidade}/{inicio}/{fim}`; o cadastro `/api/v4/sistemas` identifica Cantareira com ID 64. O arquivo usado foi obtido em:

`https://mananciais.sabesp.com.br/api/v4/sistemas/64/dados/diario/2024-01-01/2025-12-31`

**Status:** endpoint observado em funcionamento, **não confirmado como API pública documentada ou estável**. O script `src/fetch_sabesp.py` reproduz a extração e salva o corpo JSON original e um CSV normalizado localmente.

| Propriedade | Observação verificada |
|---|---|
| Sistema | Cantareira, ID 64 no retorno do portal |
| Período | 01/01/2024 a 31/12/2025 |
| Frequência | Diária |
| Linhas | 731, sem datas faltantes ou duplicadas nesse intervalo |
| Variável principal | `volumeUtilArmazenadoPorcentagem`, porcentagem do volume útil armazenado |
| Variável adicional | `chuva`, milímetros, exibida como chuva diária no portal |
| SHA-256 do JSON bruto baixado | `5c39d83a66445ba1b9350e2df540af84b60382930d06588de70ca2fc1129be2e` |
| Horário da extração | 2026-11-05T14:15:30Z |

**Licença:** não localizamos termos explícitos de redistribuição para esta série. Os arquivos brutos/normalizados e gráficos derivados permanecem locais e ignorados pelo Git. Confirmar a licença ou obter permissão antes de publicar dados ou artefatos derivados. O endpoint e os valores podem mudar; a hash permite perceber alteração na resposta.

**Limites:** um único sistema não representa toda a RMSP. A série não permite inferir falta de água por bairro. O dado de chuva e o volume precisam de checagem conceitual com o glossário do portal antes de conclusões hidrológicas fortes. A faixa 0–100% é usada só para este recorte; outros sistemas do portal podem exibir valores acima de 100%. Não há dados pessoais.
