# DRE no PREVIA

## Objetivo

A DRE do PREVIA visa comparar o orçado com a prévia por CR (Cost Center), levando em conta receita, despesas, ajustes gerenciais e folha.

## Tabelas envolvidas

- `orcamento_previa`
  - Contém valores planejados por `categoria_despesa` para cada `cr`
  - Usada como base do orçamento da DRE
- `forecast_valores`
  - Contém valores de forecast por `chave_ek`, `cenario` e `mes_ref`
  - Serve como fonte de receita prevista
- `forecast_oportunidades`
  - Relaciona oportunidades ao CR e fornece metadados como prática, produto e cliente
- `ajustamentos_gerencia`
  - Registra ajustes de crédito e débito por `CR` e `resultado`
  - Usada para ajustar valores de previsão e alimentar categorias adicionais de DRE
- `previa_folha_th`
  - Contém valores de folha previstos por `cr` e `mes_ref`
  - Usada como previsão de custo de pessoal na DRE

## Como a DRE é montada hoje

1. Os valores de receita orçada vêm de `orcamento_previa`.
2. Os valores de receita de prévia são derivados de `forecast_valores` e de lançamentos de ajuste em `ajustamentos_gerencia`.
3. A prévia de folha (`previa_folha_th`) é somada como custo de pessoal ou provisão de folha.
4. No frontend, esses dados são combinados por CR para calcular:
   - `MC Orçado`
   - `MC Prévia`
   - `Desvio pp`
   - `% de Atingimento`

## Regras de registro implantadas

- `ajustamentos_gerencia` guarda lançamentos de crédito e débito separados por `cr_credito` e `cr_debito`.
- Para cada CR, os ajustes são agregados em `resumo/cr` e expostos como `ajustes` e `previas` no JSON da API.
- `orcamento_previa` é carregado por categoria de despesa e recuperado por CR para alimentar o orçamento de DRE.
- `previa_folha_th` é consultado por CR para compor o custo de pessoal e ajustar `MC Prévia`.

## Importante

- A geração final de DRE no frontend ainda depende das categorias disponíveis em `orcamento_previa` e `ajustamentos_gerencia`.
- Se existir uma categoria sem correspondência exata, o frontend tenta agrupar por nome e fallback de valor.
- O endpoint `/api/resumo/cr` é o principal ponto de integração entre as tabelas e a visualização da DRE.
