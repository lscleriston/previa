Você é um engenheiro de dados sênior e desenvolvedor full-stack. Sua tarefa é criar a estrutura inicial de uma aplicação modular de análise de forecast financeiro. A entrega desta sessão cobre três etapas em sequência: (1) análise e entendimento da aba FORECAST, (2) script ETL que carrega os dados em SQLite, e (3) scaffold da aplicação web com Docker.

Não pule etapas. Execute cada uma na ordem e apresente os resultados antes de avançar.

---

## CONTEXTO DO PROJETO

A planilha é um forecast semanal corporativo (MSP) com 31 abas. A aba FORECAST é a base comercial de oportunidades e projeções — ela lista cada oportunidade/quote com valores mensais projetados por CR (Centro de Resultado), gerente, cliente, país, prática e produto.

Características conhecidas da aba FORECAST:
- Faixa usada: A1:EM16345 (16.345 linhas, 143 colunas)
- Linha real de cabeçalho: linha 65 (as linhas 1-64 são metadados e totais)
- Dados começam na linha 66
- Chave única: coluna EK (concatenação de torre+cliente+país+descrição+data)
- Colunas de valores mensais estão em series de colunas adjacentes (jan-dez), repetidas para diferentes anos/cenários
- Contém: dimensões comerciais (gerente, owner, cliente, prática, produto, país, CR, moeda) + valores mensais + status de risco + faróis

---

## ETAPA 1 — Leia e documente a aba FORECAST

Abra o arquivo xlsx e leia a aba "FORECAST". Faça o seguinte:

### 1.1 Identifique o cabeçalho real
- A linha 65 deve conter os nomes das colunas. Confirme isso.
- Liste todas as colunas encontradas com: letra da coluna | nome do cabeçalho | tipo de dado inferido (texto, data, número, percentual, booleano).

### 1.2 Classifique as colunas em grupos
Agrupe as colunas nas seguintes categorias:
- **Dimensões identificadoras**: data criação, torre, banco, ano, país, tipo (hunter/farmer), gerente, owner, prática, produto, cliente, subcliente, ID empresa, CR, moeda
- **Identificadores de oportunidade**: ID opp, descrição, status comercial, metodologia, tipo OPP, CR-OI, ordem interna
- **Atributos de contrato**: vigência, data início, data fim, mês reajuste, dedução, % ponderação
- **Valores mensais (série temporal)**: colunas com valores numéricos mensais jan-dez para cada cenário (orçado, forecast, prévia etc.)
- **Indicadores de risco e governança**: risco, farol risco, farol cronograma, status DAF, status governança, classificação distrato
- **Campos calculados/chave**: chave EK, totais

### 1.3 Mostre 5 linhas de exemplo reais
Exiba as linhas 66-70 como tabela, com os nomes de coluna do cabeçalho.

### 1.4 Identifique os cenários de valor presentes
Quais são os distintos prefixos ou sufixos de cenário presentes nas colunas de valor? (ex: "Orçado", "Forecast", "Prévia", "1ª Revisão") — esses virarão colunas separadas no banco.

---

## ETAPA 2 — Script ETL Python

Com base no mapeamento da Etapa 1, crie um script Python chamado `etl_forecast.py` que:

### 2.1 Lê o xlsx
```python
# Use openpyxl para leitura (não pandas na leitura direta — o xlsx tem células mescladas e linhas ocultas)
# Parâmetros:
#   - arquivo: path configurável via variável de ambiente ou argumento
#   - aba: "FORECAST"
#   - linha do cabeçalho: 65 (índice 1-based)
#   - início dos dados: linha 66
#   - ignorar linhas ocultas: sim (row.hidden == True)
#   - ignorar linhas onde a coluna EK esteja vazia (são totais/separadores)
```

### 2.2 Normaliza os dados
- Converta datas do formato serial Excel (número) para ISO 8601 (YYYY-MM-DD)
- Limpe strings: strip(), title case onde aplicável, None para células vazias
- Valores monetários: converta para float, trate células vazias como 0.0
- Crie coluna `semana_carga` com a data/hora atual do ETL
- Crie coluna `arquivo_origem` com o nome do arquivo processado

### 2.3 Cria o banco SQLite
Crie as seguintes tabelas no arquivo `forecast.db`:

```sql
-- Tabela principal de oportunidades
CREATE TABLE IF NOT EXISTS forecast_oportunidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave_ek TEXT UNIQUE,           -- coluna EK: chave de negócio
    data_criacao DATE,
    banco TEXT,                     -- torre/banco
    ano INTEGER,
    pais TEXT,
    tipo_papel TEXT,                -- Hunter / Farmer
    gerente TEXT,
    owner TEXT,
    ger_comercial TEXT,
    operacao TEXT,
    ger_operacao TEXT,
    pre_vendas TEXT,
    pratica TEXT,
    produto TEXT,
    id_empresa TEXT,
    cliente TEXT,
    cliente_ge TEXT,
    subcliente TEXT,
    novo_cliente BOOLEAN,
    industria TEXT,
    id_oportunidade TEXT,
    descricao_oportunidade TEXT,
    status_comercial TEXT,
    status_comercial_det TEXT,
    metodologia TEXT,
    tipo_opp TEXT,
    cr TEXT,                        -- CR SAP
    semana_fechamento TEXT,
    cr_oi TEXT,
    ordem_interna TEXT,
    moeda TEXT,
    consideracao TEXT,
    vigencia TEXT,
    contrato TEXT,
    data_inicio_contrato DATE,
    data_fim_contrato DATE,
    mes_reajuste TEXT,
    risco TEXT,
    deducao REAL,
    pct_ponderacao REAL,
    semana_carga DATETIME,
    arquivo_origem TEXT
);

-- Tabela de valores mensais (formato longo — uma linha por oportunidade/mês/cenário)
CREATE TABLE IF NOT EXISTS forecast_valores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave_ek TEXT,
    cenario TEXT,           -- 'orcado', 'forecast', 'previa', 'reajuste' etc.
    mes_ref TEXT,           -- formato 'YYYY-MM'
    valor_rl REAL,          -- receita líquida
    valor_rb REAL,          -- receita bruta (quando disponível)
    semana_carga DATETIME,
    FOREIGN KEY (chave_ek) REFERENCES forecast_oportunidades(chave_ek)
);

-- Log de carga
CREATE TABLE IF NOT EXISTS etl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo TEXT,
    aba TEXT,
    linhas_lidas INTEGER,
    linhas_carregadas INTEGER,
    linhas_ignoradas INTEGER,
    status TEXT,
    mensagem TEXT,
    executado_em DATETIME
);
```

### 2.4 Carrega com upsert
- Use INSERT OR REPLACE para `forecast_oportunidades` (chave: `chave_ek`)
- Apague e reinsira os valores de `forecast_valores` para cada `chave_ek` reprocessada
- Registre início e fim no `etl_log`
- Ao final, imprima um resumo: linhas lidas / carregadas / ignoradas / erros

### 2.5 Tratamento de erros
- Se uma linha tiver erro de parsing, registre no log e continue (não aborte)
- Ao final, se houver erros > 5% do total, imprima aviso visível

---

