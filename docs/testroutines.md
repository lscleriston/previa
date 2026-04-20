# Rotina de Testes — Forecast Pro

> Execute este checklist após **qualquer alteração** no frontend ou backend.  
> Marque cada item com `✓` (passou), `✗` (falhou) ou `—` (não aplicável).

---

## 1. Pré-requisitos

Antes de iniciar os testes, confirme:

- [ ] Container está rodando: `docker compose up` sem erros no terminal
- [ ] Backend respondendo: acesse `http://localhost:8000/api/health` — deve retornar `{ "status": "ok" }`
- [ ] Frontend acessível: `http://localhost:3000/pages/cr_analysis.html` carrega sem erros no console (F12)

---

## 2. Página — Resultado por CR

### 2.1 Carregamento inicial

| # | Teste | Resultado |
|---|-------|-----------|
| T01 | Página carrega sem erros no console do browser | |
| T02 | Filtros (Mês, País, Diretor, Gerente, Cliente) são populados via API | |
| T03 | Tabela exibe pelo menos uma linha de CR | |
| T04 | KPI cards mostram valores numéricos (não `—` ou `undefined`) | |
| T05 | "Última carga" exibe data/hora no header | |

### 2.2 Filtros

| # | Teste | Resultado |
|---|-------|-----------|
| T06 | Selecionar um Gerente filtra a tabela corretamente | |
| T07 | Selecionar "Todos" restaura todos os CRs | |
| T08 | KPI cards atualizam ao mudar filtro | |
| T09 | Combinação de dois filtros simultâneos funciona | |

### 2.3 Tabela de CRs

| # | Teste | Resultado |
|---|-------|-----------|
| T10 | Colunas exibidas: CR/Código, Descrição, MC Orçado, MC Prévia, Desvio PP, Δ%, Atingimento | |
| T11 | Quando RL Orçado = 0, coluna Δ% exibe `—` (não `0.0%`) | |
| T12 | Atingimento negativo exibe só o número, sem barra visual | |
| T13 | Atingimento > 100% exibe barra verde completa + número acima de 100% | |
| T14 | Atingimento entre 80–99% exibe barra amarela | |
| T15 | Atingimento < 80% exibe barra vermelha | |

---

## 3. DRE Expandida — Crítico

> Esta seção cobre os elementos que quebram com mais frequência.

### 3.1 Expansão e colapso

| # | Teste | Resultado |
|---|-------|-----------|
| T16 | Clicar em uma linha de CR expande o painel DRE abaixo dela | |
| T17 | Ícone muda de `▶` para `▼` ao expandir | |
| T18 | Clicar novamente fecha o painel e restaura `▶` | |
| T19 | Abrir um segundo CR fecha o primeiro automaticamente | |

### 3.2 Linhas da DRE — estrutura

| # | Teste | Resultado |
|---|-------|-----------|
| T20 | Linha "Receita Bruta" aparece como primeira linha | |
| T21 | Linha "(-) Deduções" aparece logo abaixo de Receita Bruta | |
| T22 | Linha `= Receita Líquida` aparece em negrito e cor azul | |
| T23 | Todas as linhas de custo aparecem com prefixo `(-)` | |
| T24 | Linha `= Custo Total` aparece após a última linha de custo | |
| T25 | Linha `= Margem Contribuição` aparece ao final em verde ou vermelho conforme valor | |
| T26 | Linha `MC %` aparece como última linha | |

### 3.3 Indentação visual

| # | Teste | Resultado |
|---|-------|-----------|
| T27 | Linhas de custo `(-)` estão visualmente indentadas em relação a Receita Bruta | |
| T28 | Linhas `(+) Rec.` estão indentadas igual às de custo | |
| T29 | Linhas de subtotal (`= RL`, `= Custo Total`, `= MC`) não estão indentadas | |

### 3.4 Recuperação de Custos — **área crítica**

> Este elemento quebra com frequência. Teste com atenção redobrada.

| # | Teste | Resultado |
|---|-------|-----------|
| T30 | Linha `(+) Rec. Outros Gastos` aparece na DRE | |
| T31 | Linha `(+) Rec. Pessoal` aparece na DRE | |
| T32 | Valores de recuperação aparecem como **positivos** na coluna Prévia | |
| T33 | Δ R$ de recuperação: quando Prévia > Orçado a cor é **verde** | |
| T34 | Δ R$ de recuperação: quando Prévia < Orçado a cor é **vermelho** | |
| T35 | Recuperação é somada corretamente no `= Custo Total` (reduz o custo) | |
| T36 | Recuperação impacta corretamente o `= Margem Contribuição` | |
| T37 | Clicar no ícone `⊕` da linha Rec. Pessoal com valor ≠ 0 abre drill-down | |
| T38 | Drill-down de Rec. Pessoal exibe colunas: Descrição, CR Origem, Aba de Origem, Valor | |
| T39 | Fechar drill-down com segundo clique funciona | |

**Como verificar T35 e T36 manualmente:**

```
MC = RL - Pessoal - CustoDireto - Rateios + RecOutros + RecPessoal
```

Pegue um CR com Rec. Pessoal ≠ 0, some manualmente e confira se o `= MC` exibido bate.

---

## 4. Drill-down de Lançamentos

| # | Teste | Resultado |
|---|-------|-----------|
| T40 | Linhas com Prévia = 0 **não** exibem ícone `⊕` | |
| T41 | Linhas com Prévia ≠ 0 exibem ícone `⊕` antes do valor | |
| T42 | Clicar em `⊕` faz requisição a `/api/cr/{cr}/lancamentos?categoria=...` | |
| T43 | Sub-tabela aparece abaixo da linha clicada com fundo levemente diferente | |
| T44 | Ícone muda para `⊖` enquanto drill-down está aberto | |
| T45 | Abrir drill-down em outra linha fecha o anterior | |
| T46 | Quando API retorna array vazio, exibe mensagem: "Sem lançamentos detalhados..." | |
| T47 | Quando API retorna 404, exibe mensagem de erro inline sem quebrar a página | |

---

## 5. Página — Importar Prévia

### 5.1 Upload de arquivo — **área crítica**

> O botão "Iniciar carga" é o segundo elemento que quebra com frequência.

| # | Teste | Resultado |
|---|-------|-----------|
| T48 | Página `atualizar.html` carrega sem erros | |
| T49 | Zona de upload aceita arrastar e soltar um `.xlsx` | |
| T50 | Botão "clique para selecionar" abre o seletor de arquivos do SO | |
| T51 | Após selecionar arquivo, nome do arquivo aparece na tela | |
| T52 | Botão **"Iniciar carga"** aparece após seleção do arquivo | |
| T53 | Botão "Iniciar carga" está **habilitado** (não cinza/disabled) antes de clicar | |
| T54 | Clicar em "Iniciar carga" faz POST para `/etl/upload` | |
| T55 | Botão fica desabilitado durante o processamento | |
| T56 | Tentar enviar arquivo `.csv` ou `.pdf` é bloqueado (só aceita `.xlsx`) | |

### 5.2 Progresso da carga

| # | Teste | Resultado |
|---|-------|-----------|
| T57 | Área de progresso aparece imediatamente após clicar em "Iniciar carga" | |
| T58 | Etapas aparecem em sequência: Validando → Limpando → Recriando → ETLs → Concluído | |
| T59 | Barra de cada etapa avança conforme o percentual recebido | |
| T60 | Log de texto é atualizado em tempo real (não só no final) | |
| T61 | Última etapa exibe "Concluído" com ícone `✓` verde | |
| T62 | Botão "Iniciar carga" é reabilitado após conclusão | |
| T63 | Em caso de erro em uma etapa, a etapa exibe ícone `✗` vermelho | |
| T64 | Erro em uma etapa não trava a interface — botão volta a ficar habilitado | |
| T65 | Após carga concluída, acessar Resultado por CR mostra os dados novos | |

---

## 6. Temas

| # | Teste | Resultado |
|---|-------|-----------|
| T66 | Ícone de tema aparece no header | |
| T67 | Menu de temas abre ao clicar no ícone | |
| T68 | Menu fecha ao clicar fora | |
| T69 | Tema "Claro Executivo" aplica fundo claro em toda a página | |
| T70 | Tema "Claro Executivo" mantém legibilidade na DRE expandida (sem texto invisível) | |
| T71 | Troca de tema persiste após recarregar a página (localStorage) | |
| T72 | Tema ativo exibe `✓` no menu | |

---

## 7. Regressão rápida após alteração de CSS

Execute quando alterar apenas estilos:

| # | Teste | Resultado |
|---|-------|-----------|
| T73 | DRE expande sem sobreposição de elementos | |
| T74 | Drill-down de lançamentos não deforma o layout da tabela | |
| T75 | Tabela principal não tem scroll horizontal desnecessário | |
| T76 | Filtros não quebram linha em telas ≥ 1280px | |

---

## 8. Registro de falhas

Use esta tabela para registrar falhas encontradas durante os testes:

| Data | Teste | Descrição do problema | Arquivo afetado | Resolvido |
|------|-------|-----------------------|-----------------|-----------|
| | | | | |
| | | | | |

---

## 9. Ordem de execução recomendada

```
1. Seção 1  — Pré-requisitos (sempre primeiro)
2. Seção 5  — Importar Prévia (garante que o banco tem dados frescos)
3. Seção 2  — Resultado por CR (carregamento e filtros)
4. Seção 3  — DRE Expandida (especialmente T30–T39 — recuperação)
5. Seção 4  — Drill-down de lançamentos
6. Seção 6  — Temas (somente se alterou CSS)
7. Seção 7  — Regressão CSS (somente se alterou CSS)
```

---

## 10. Verificação automatizada

Use os testes automatizados para validar regras de negócio de DRE, recuperação e upload.

- [ ] Executar os testes de DRE e resumo CR:
  - `python -m pytest tests/api/test_dre_calculations.py tests/api/test_cr_resumo.py -q`
- [ ] Confirmar que as linhas de recuperação `(+) Rec. Pessoal` e `(+) Rec. Outros Gastos` aparecem como valores positivos na DRE expansível.
- [ ] Verificar que `= Custo Total` inclui as recuperações e que `= Margem Contribuição` (MC) é calculada como:
  - `MC = RL - Custos - Rateios + RecOutros + RecPessoal`
- [ ] Se alterar a ingestão ou ETL, executar também o conjunto de testes de API relacionados ao upload e ingestão.

---

*Documento mantido em `docs/testroutines.md` — atualizar sempre que novas funcionalidades forem adicionadas.*