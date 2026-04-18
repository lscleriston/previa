# Documentação da API

## GET /api/health
- Descrição: verifica se a API está ativa
- Parâmetros: nenhum
- Resposta JSON:
  ```json
  {
    "status": "ok",
    "message": "API está rodando"
  }
  ```
- Consulta: nenhum banco específico

## GET /api/filtros
- Descrição: retorna valores usados pelos filtros do frontend
- Parâmetros: nenhum
- Resposta JSON:
  ```json
  {
    "gerentes": ["ANTONIO", "Ana Carolina de Oliveira", "Cleriston Lopes Silva"],
    "diretores": ["Diretor A", "Diretor B"],
    "paises": ["BR"],
    "clientes": ["Cliente X", "Cliente Y"],
    "praticas": ["Prática A", "Prática B"],
    "produtos": ["Produto A", "Produto B"],
    "crs": ["341020270", "341020258"],
    "meses": ["2026-04"]
  }
  ```
- Consulta: `dim_cr`, `forecast_oportunidades`, `forecast_valores`

## GET /api/oportunidades
- Descrição: lista oportunidades com filtros e valores agregados por previsão
- Parâmetros:
  - `gerente` (query)
  - `diretor` (query)
  - `pais` (query)
  - `cliente` (query)
  - `pratica` (query)
  - `produto` (query)
  - `cr` (query)
  - `mes` (query)
  - `page` (query, padrão `1`)
- Resposta JSON: lista de objetos com campos como `ger_comercial`, `pais`, `cliente`, `pratica`, `produto`, `vl_total_forecast_rl`, `vl_total_forecast_rb`
- Consulta: `forecast_oportunidades`, `forecast_valores`, `dim_cr`

## GET /api/oportunidades/{chave_ek}
- Descrição: detalhe de oportunidade (placeholder atual)
- Parâmetros:
  - `chave_ek` (path)
- Resposta JSON:
  ```json
  {
    "chave_ek": "1234",
    "detalhes": "Em construção"
  }
  ```
- Consulta: nenhuma implementação de consulta atual

## GET /api/resumo
- Descrição: resumo de oportunidades e agregados financeiros
- Parâmetros: mesmos de `/api/oportunidades` menos `page`
- Resposta JSON:
  ```json
  {
    "total_opp": 123,
    "rl_total": 456789.0,
    "rb_total": 512345.0
  }
  ```
- Consulta: `forecast_oportunidades`, `forecast_valores`, `dim_cr`

## GET /api/resumo/cr
- Descrição: resumo por CR com valores de forecast e metadados de CR
- Parâmetros:
  - `gerente` (query)
  - `diretor` (query)
  - `pais` (query)
  - `cliente` (query)
  - `pratica` (query)
  - `produto` (query)
  - `cr` (query)
  - `mes` (query)
- Resposta JSON: lista de objetos com campos como:
  - `cr`
  - `cr_sap`
  - `des_cr`
  - `qtd_opp`
  - `total_rl`
  - `total_rb`
  - `orcamento` (categorias de orçamento)
  - `previas` (ajustes/pontos de prévia)
  - `ajustes` (detalhes de ajustes gerenciais)
  - `pessoal_previa`
- Consulta: `forecast_oportunidades`, `forecast_valores`, `dim_cr`, `orcamento_previa`, `previa_folha_th`, `ajustamentos_gerencia`

## GET /api/cr/{cr}/lancamentos
- Descrição: obtém lançamentos detalhados por CR e categoria
- Parâmetros:
  - `cr` (path)
  - `categoria` (query)
  - `mes` (query opcional)
- Resposta JSON: lista de registros de `ajustamentos_gerencia`
- Consulta: `ajustamentos_gerencia`

## POST /api/etl/executar
- Descrição: dispara o ETL principal de forecast (`etl_forecast.py`)
- Parâmetros: nenhum
- Resposta JSON:
  ```json
  {
    "status": "sucesso",
    "mensagem": "ETL executado com sucesso!"
  }
  ```
- Observação: esse endpoint executa apenas o ETL de forecast do arquivo padrão.

## GET /api/etl/status
- Descrição: retorna o status atual de ETL
- Parâmetros: nenhum
- Resposta JSON:
  ```json
  {
    "status": "sucesso",
    "ultima_carga": "2026-04-17 10:00:00"
  }
  ```
