# PREVIA

## O que é o sistema

PREVIA é uma plataforma de forecast financeiro para MSP que compara valores orçados com prévias por Cost Center (CR). O objetivo é apresentar dados de forecast, oportunidades comerciais e análise de DRE em um dashboard leve, usando dados extraídos de planilhas Excel.

## O que o sistema faz

- Carrega planilha Excel semanal de forecast e orçado
- Constrói um catálogo de CRs (`dim_cr`)
- Alimenta tabelas de oportunidades, valores e previsões
- Suporta filtros por gerente, diretor, país, cliente, prática, produto, CR e mês
- Exibe resumos por CR e permite drill-down em lançamentos detalhados
- Mantém histórico de orçado, prévia e ajustes gerenciais

## Pré-requisitos

- Docker
- Python 3.12

## Como subir o projeto em 3 comandos

```bash
git clone https://github.com/lscleriston/previa.git
cd previa
# Coloque o arquivo Excel em data/raw/
# Exemplo: data/raw/Forecast Semanal 2026 - Abril.xlsx
docker compose up --build
```

## Como rodar os ETLs após subir

### Via API

```bash
curl -X POST http://localhost:8000/api/etl/executar
```

### Manualmente

```bash
python backend/etl/etl_forecast.py
python backend/etl/etl_dim_cr.py
python backend/etl/etl_gerencias.py
python backend/etl/etl_orcado_previa.py
python backend/etl/etl_previa_folha.py
```

### Ordem recomendada de execução

1. `backend/etl/etl_dim_cr.py`
2. `backend/etl/etl_forecast.py`
3. `backend/etl/etl_gerencias.py`
4. `backend/etl/etl_orcado_previa.py`
5. `backend/etl/etl_previa_folha.py`

## Estrutura de pastas resumida

- `backend/`
  - `api/` - FastAPI app e roteamento de endpoints
  - `etl/` - scripts de ingestão e transformação de planilhas
  - `db/` - inicialização de banco e acesso a dados
  - `utils/` - helpers e utilitários de análise
  - `reports/` - scripts auxiliares de relatórios e extração
- `frontend/`
  - `pages/` - páginas HTML principais
  - `css/` - estilos de layout e temas
  - `js/` - lógica de frontend e consumo da API
- `data/`
  - `raw/` - arquivos Excel de origem
  - `db/` - banco SQLite gerado (`previadb.db`)
  - `reports/` - JSONs exportados para análise
- `docs/` - documentação do projeto
- `scripts/` - atalhos de execução
- `buildPlan/` - plano do projeto
- `docker-compose.yml` e `Dockerfile` - configuração dos containers

## Onde está a DRE

A análise DRE é construída a partir de:

- `orcamento_previa` para valores orçados por categoria
- `forecast_valores` e `forecast_oportunidades` para receita prevista
- `ajustamentos_gerencia` para lançamentos de ajustes de crédito e débito
- `previa_folha_th` para provisão de folha prévia de pessoal

A combinação dessas tabelas gera os cálculos de margem de contribuição, desvios e atingimento por CR.

## Documentação adicional

- `docs/etl.md` - descrição detalhada de cada script ETL
- `docs/api.md` - contrato das rotas FastAPI
- `docs/arquitetura.md` - visão geral do fluxo e dependências
- `docs/dre.md` - como a DRE é montada e quais registros são usados
