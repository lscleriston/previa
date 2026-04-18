# Arquitetura do PREVIA

```mermaid
flowchart LR
  XLSX["Excel: data/raw/Forecast Semanal 2026 - Abril.xlsx"]

  subgraph ETL[ETL]
    dim_cr["etl_dim_cr.py"]
    forecast["etl_forecast.py"]
    gerencias["etl_gerencias.py"]
    orcamento["etl_orcado_previa.py"]
    folha["etl_previa_folha.py"]
  end

  subgraph SQLite[SQLite]
    dim_cr_t["dim_cr"]
    opp["forecast_oportunidades"]
    valores["forecast_valores"]
    ajustes["ajustamentos_gerencia"]
    orcamento_t["orcamento_previa"]
    folha_t["previa_folha_th"]
  end

  subgraph API[FastAPI]
    filtros["GET /api/filtros"]
    oportunidades["GET /api/oportunidades"]
    resumo["GET /api/resumo"]
    resumo_cr["GET /api/resumo/cr"]
    lancamentos["GET /api/cr/{cr}/lancamentos"]
    etl_exec["POST /api/etl/executar"]
  end

  subgraph Frontend[Frontend]
    pages["frontend/pages/*.html"]
  end

  XLSX --> dim_cr
  XLSX --> forecast
  XLSX --> gerencias
  XLSX --> orcamento
  XLSX --> folha

  dim_cr --> dim_cr_t
  forecast --> dim_cr_t
  forecast --> opp
  forecast --> valores
  gerencias --> ajustes
  orcamento --> orcamento_t
  folha --> folha_t

  dim_cr_t --> oportunidades
  opp --> oportunidades
  valores --> oportunidades

  opp --> resumo
  valores --> resumo

  opp --> resumo_cr
  valores --> resumo_cr
  orcamento_t --> resumo_cr
  folha_t --> resumo_cr
  ajustes --> resumo_cr

  ajustes --> lancamentos

  oportunidades --> pages
  resumo --> pages
  resumo_cr --> pages
  lancamentos --> pages
  etl_exec --> pages
```

## Fluxo geral

1. O Excel é colocado em `data/raw/`.
2. Os scripts em `backend/etl/` extraem e transformam os dados para o SQLite em `data/db/previadb.db`.
3. A API FastAPI (`backend/api/app.py`) consulta o banco e expõe os endpoints REST.
4. O frontend (`frontend/pages/`) consome a API para exibir as páginas de análise.

## DRE e registros implantados

A DRE atual é construída a partir de múltiplos conjuntos de dados:

- `orcamento_previa` traz as categorias orçadas de despesas por CR
- `forecast_valores` e `forecast_oportunidades` trazem a receita prevista
- `ajustamentos_gerencia` guarda ajustes de crédito e débito lançados por gerência
- `previa_folha_th` contém os valores de folha previstos por CR

Esses registros alimentam a geração da DRE no frontend, permitindo:

- calcular `MC Orçado` e `MC Prévia`
- comparar valores orçados com valores de prévia
- exibir desvios em pontos percentuais
- mostrar o atingimento esperado de margem

## Quais ETLs alimentam quais tabelas

- `backend/etl/etl_dim_cr.py` → `dim_cr`
- `backend/etl/etl_forecast.py` → `dim_cr`, `forecast_oportunidades`, `forecast_valores`
- `backend/etl/etl_gerencias.py` → `ajustamentos_gerencia`
- `backend/etl/etl_orcado_previa.py` → `orcamento_previa`
- `backend/etl/etl_previa_folha.py` → `previa_folha_th`

## Quais rotas consomem quais tabelas

- `/api/filtros` → `dim_cr`, `forecast_oportunidades`, `forecast_valores`
- `/api/oportunidades` → `forecast_oportunidades`, `forecast_valores`, `dim_cr`
- `/api/resumo` → `forecast_oportunidades`, `forecast_valores`, `dim_cr`
- `/api/resumo/cr` → `forecast_oportunidades`, `forecast_valores`, `dim_cr`, `orcamento_previa`, `previa_folha_th`, `ajustamentos_gerencia`
- `/api/cr/{cr}/lancamentos` → `ajustamentos_gerencia`
