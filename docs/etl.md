# Documentação de ETL

## Visão geral do ETL

O projeto centraliza a ingestão de dados em `backend/etl/` e mantém um banco SQLite em `data/db/previadb.db`. Cada script cobre uma área específica do processo:

- `etl_dim_cr.py` — trata a dimensão de CR e atributos de gerente/diretor/pais
- `etl_forecast.py` — importa forecast, oportunidades e agrega valores de receita
- `etl_gerencias.py` — importa ajustes gerenciais de crédito e débito por CR
- `etl_orcado_previa.py` — importa o orçamento prévia por categorias de despesa
- `etl_previa_folha.py` — importa a previsão de folha TH

## Ordem recomendada de execução

1. `backend/etl/etl_dim_cr.py`
2. `backend/etl/etl_forecast.py`
3. `backend/etl/etl_gerencias.py`
4. `backend/etl/etl_orcado_previa.py`
5. `backend/etl/etl_previa_folha.py`

Executar nessa ordem garante que a dimensão de CR esteja disponível antes das tabelas que dependem dela.

---

## backend/etl/etl_dim_cr.py
- Nome do arquivo: `backend/etl/etl_dim_cr.py`
- Abas lidas: primeira aba que começa com `Prévia` e contém `MSP`
- Tabela SQLite populada: `dim_cr`
- Fluxo: lê colunas de CR, cliente, descrição, país, diretor e gerente; grava em upsert via `INSERT OR REPLACE`
- Chave de integração: `CR_SAP` e `Cod_Cr`
- Exemplo:
  ```bash
  python backend/etl/etl_dim_cr.py
  ```

---

## backend/etl/etl_forecast.py
- Nome do arquivo: `backend/etl/etl_forecast.py`
- Abas lidas: `FORECAST` e a aba `Prévia*MSP` da planilha Excel
- Tabelas SQLite populadas: `dim_cr`, `forecast_oportunidades`, `forecast_valores`
- Regra de chave: `forecast_oportunidades.chave_ek` é única; valores são agregados por `chave_ek` e `cenario`
- Dependências: usa `dim_cr` para atribuir CR e metadados
- Exemplo:
  ```bash
  python backend/etl/etl_forecast.py
  ```

---

## backend/etl/etl_gerencias.py
- Nome do arquivo: `backend/etl/etl_gerencias.py`
- Abas lidas: `GERENCIA EDILSON`, `GERENCIA OCTAVIO`, `GERENCIA WESLEY`
- Tabela SQLite populada: `ajustamentos_gerencia`
- Estrutura: cada aba fornece ajustes de crédito e débito, com `resultado`, `mes_ref`, `cr_credito` e `cr_debito`
- Chave de integração: auto-incremento `id`
- Exemplo:
  ```bash
  python backend/etl/etl_gerencias.py
  ```

---

## backend/etl/etl_orcado_previa.py
- Nome do arquivo: `backend/etl/etl_orcado_previa.py`
- Aba lida: primeira aba que começa com `Prévia` e contém `MSP`
- Tabela SQLite populada: `orcamento_previa`
- Regra: apura categorias de despesas e valores planejados por CR
- Sincronização: limpa o mês alvo antes de inserir novos registros
- Exemplo:
  ```bash
  python backend/etl/etl_orcado_previa.py
  ```

---

## backend/etl/etl_previa_folha.py
- Nome do arquivo: `backend/etl/etl_previa_folha.py`
- Aba lida: `Prévia Folha TH Abr`
- Tabela SQLite populada: `previa_folha_th`
- Objetivo: adicionar provisão de folha por CR para a DRE
- Regra: deleta registros do mesmo `mes_ref` antes de recarregar
- Exemplo:
  ```bash
  python backend/etl/etl_previa_folha.py
  ```

---

## Notas de paths
- Planilha Excel de origem: `data/raw/Forecast Semanal 2026 - Abril.xlsx`
- Banco SQLite: `data/db/previadb.db`

## Observações operacionais
- O serviço backend também expõe `POST /api/etl/executar` para disparar o ETL principal.
- A pasta `data/reports/` armazena outputs JSON de análise e relatórios auxiliares.
