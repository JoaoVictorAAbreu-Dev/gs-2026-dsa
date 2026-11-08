# Fonte dos dados — Sistema Cantareira

| Propriedade | Descrição |
|---|---|
| Fonte | Sabesp — Portal dos Mananciais ([base de dados](https://mananciais.sabesp.com.br/base-dados)) |
| Endpoint | `https://mananciais.sabesp.com.br/api/v4/sistemas/64/dados/diario/{início}/{fim}` — usado pelo JavaScript do próprio portal; **não é API documentada** e pode mudar sem aviso |
| Sistema | Cantareira (ID 64 no cadastro `/api/v4/sistemas`) |
| Período | 01/01/2024 a 07/11/2026 (1.042 dias, sem lacunas). 08/11/2026 excluído por ser dado provisório do dia da extração |
| Frequência | Diária |
| Extração | Mês a mês em 08/11/2026 (`data/raw/monthly/AAAA-MM.csv`); consolidado em `data/cantareira_diario_2024_2026.csv` |
| SHA-256 do consolidado | `26e757200fd89261a807db1afe79ce50a1c6bc893970ac20697eb800e93c600a` |

## Variáveis

| Coluna | Campo no portal | Unidade | Observação |
|---|---|---|---|
| `storage_pct` | `volumeUtilArmazenadoPorcentagem` | % do volume útil | ≈ 982 hm³ de volume útil total (204,59 hm³ = 20,83 % em 01/12/2025) |
| `rain_mm` | `chuva` | mm/dia | média dos postos pluviométricos do sistema |
| `natural_inflow_m3s` | `vazaoNatural` | m³/s | afluência natural aos reservatórios |
| `produced_flow_m3s` | `vazaoProduzida` | m³/s | água produzida para abastecimento da RMSP |

## Verificação

O trecho 2024–2025 foi comparado com uma extração anterior feita em 05/11/2026 (JSON bruto com SHA-256 `5c39d83a66445ba1b9350e2df540af84b60382930d06588de70ca2fc1129be2e`). As seis estatísticas de controle coincidiram: 731 linhas, mínimo 19,68 %, máximo 78,12 %, mediana 54,39 %, chuva total 2.489,9 mm e 400 dias sem chuva. A variação diária do estoque tem correlação de 0,99 com o balanço afluência − produção.

## Limitações

- Um único sistema produtor; a RMSP é abastecida por sistemas integrados.
- A série não traz a vazão liberada a jusante (bacia PCJ), a evaporação nem transferências entre sistemas; o balanço calculado é **parcial**.
- A chuva é uma média de postos e não descreve a distribuição espacial.
- Termos explícitos de redistribuição não foram localizados; os dados são usados para fins acadêmicos, com atribuição à Sabesp.
- Não há dados pessoais.

## Referência regulatória

As faixas de operação (Normal ≥ 60 %, Atenção 40–60 %, Alerta 30–40 %, Restrição 20–30 %, Especial < 20 %) seguem a Resolução Conjunta ANA/DAEE nº 925/2017, citada nos boletins da [Sala de Situação do Cantareira (ANA)](https://www.gov.br/ana/pt-br/sala-de-situacao/sistema-cantareira). Pela regra oficial, a faixa de cada mês é definida pelo volume do último dia do mês anterior.
