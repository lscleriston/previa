const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8001/api'
    : 'http://backend:8000/api';
let tableData = [];
const expandedCRs = new Set();

const categorySlugs = {
    'Receita Bruta': 'receita_bruta',
    'Deduções': 'deducoes',
    'Receita Líquida': 'receita_liquida',
    'Pessoal': 'pessoal',
    'Aluguéis': 'aluguéis',
    'Despesas Gerais': 'despesas_gerais',
    'Frota': 'frota',
    'Impostos, Taxas e Multas': 'impostos_taxas_multas',
    'Manutenção da Operação': 'manutencao_operacao',
    'Manutenção de Máquinas': 'manutencao_maquinas',
    'Manutenção Predial': 'manutencao_predial',
    'Marketing': 'marketing',
    'Outros': 'outros',
    'Pontuais': 'pontuais',
    'Seguros': 'seguros',
    'Serviços de Terceiros': 'servicos_de_terceiros',
    'Telecomunicações': 'telecomunicacoes',
    'TI': 'ti',
    'Treinamentos': 'treinamentos',
    'Utilidades': 'utilidades',
    'Viagens': 'viagens',
    'Rateio': 'rateio',
    'Recuperação Outros Gastos': 'recuperacao_outros_gastos',
    'Recuperação Pessoal': 'recuperacao_pessoal',
    'Custo Total': 'custo_total',
    'Margem Contribuição': 'margem_contribuicao',
    'MC %': 'mc_percent'
};

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

function formatMillions(val) {
    if (Math.abs(val) >= 1e6) return 'R$ ' + (val / 1e6).toFixed(1) + 'M';
    if (Math.abs(val) >= 1e3) return 'R$ ' + (val / 1e3).toFixed(0) + 'K';
    return formatCurrency(val);
}

async function fetchFiltros() {
    try {
        const response = await window.authHelpers.fetchWithAuth(`${API_BASE}/filtros`);
        const data = await response.json();
        
        const populateSelect = (id, items) => {
            const select = document.getElementById(id);
            if(select) {
                select.innerHTML = '<option value="">Todos</option>';
                items.forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item;
                    opt.textContent = item;
                    select.appendChild(opt);
                });
            }
        };

        if (data.paises) populateSelect('filter-pais', data.paises);
        if (data.diretores) populateSelect('filter-diretor', data.diretores);
        if (data.gerentes) populateSelect('filter-gerente', data.gerentes);
        if (data.clientes) populateSelect('filter-cliente', data.clientes);        
        if (data.meses) populateSelect('filter-mes', data.meses);    
    } catch (e) {
        console.error('Erro ao carregar filtros:', e);
    }
}

// Translate raw API data into flat struct
function processItem(item) {
    const flat = { ...item };
    
    // Extract orcado info
    const getOrc = (cat) => {
        if (!item.orcamento) return 0;
        const c = item.orcamento.find(o => o.categoria === cat);
        return c ? c.valor : 0;
    };

    flat.rl_orcado = getOrc('Receita Líquida');
    flat.rb_orcado = getOrc('Receita Bruta');
    flat.pessoal_orcado = getOrc('Pessoal');
    flat.custo_direto_orcado = getOrc('Custo Direto + Rateios + Recuperação de Custos') || 0;
    flat.rateio_orcado = getOrc('Rateio');
    flat.recuperacao_orcado = Math.abs(getOrc('Recuperação Outros Gastos')) + Math.abs(getOrc('Recuperação Pessoal'));
    flat.mc_orcado = getOrc('Margem de Contribuição');
    flat.mc_pct_orcado = getOrc('MC %') * 100;

    // For previa, preserve backend values if present; otherwise leave undefined so fallbacks can apply.
    flat.pessoal_previa = item.pessoal_previa;
    flat.custo_direto_previa = item.custo_direto_previa;
    flat.rateio_previa = item.rateio_previa;
    flat.recuperacao_previa = item.recuperacao_previa;
    flat.mc_previa = item.mc_previa;
    flat.mc_pct_previa = item.mc_pct_previa;

    return flat;
}

async function carregarCRs() {
    const tbody = document.getElementById('cr-table-body');
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">Carregando dados...</td></tr>';
    
    const pais = document.getElementById('filter-pais')?.value;
    const diretor = document.getElementById('filter-diretor')?.value;
    const gerente = document.getElementById('filter-gerente')?.value;
    const cliente = document.getElementById('filter-cliente')?.value;
    const mes = document.getElementById('filter-mes')?.value;

    let url = new URL(`${API_BASE}/resumo/cr`);
    if (pais) url.searchParams.append('pais', pais);
    if (diretor) url.searchParams.append('diretor', diretor);
    if (gerente) url.searchParams.append('gerente', gerente);
    if (cliente) url.searchParams.append('cliente', cliente);
    if (mes) url.searchParams.append('mes', mes);

    try {
        const response = await window.authHelpers.fetchWithAuth(url);
        const data = await response.json();

        if(!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color: var(--text-secondary);">Nenhum CR encontrado para estes filtros.</td></tr>';
            atualizarKPIs([]);
            return;
        }

        tableData = data.map(processItem);
        atualizarKPIs(tableData);
        renderTable();

    } catch (err) {
        console.error('Erro ao carregar analise de CR:', err);
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color: var(--accent-red);">Erro ao carregar os dados.</td></tr>';
    }
}

function atualizarKPIs(data) {
    const totalRL_orcado = data.reduce((s, i) => s + (i.rl_orcado ?? 0), 0);
    const totalRL_previa = data.reduce((s, i) => s + (i.total_rl ?? 0), 0);
    const desvio = totalRL_previa - totalRL_orcado;
    const pct = totalRL_orcado > 0 ? (desvio / totalRL_orcado) * 100 : 0;

    document.getElementById('kpi-total-crs').textContent = data.length;
    document.getElementById('kpi-rl-orcado').textContent = formatMillions(totalRL_orcado);
    document.getElementById('kpi-rl-previa').textContent = formatMillions(totalRL_previa);
    
    const kpiDesvio = document.getElementById('kpi-desvio');
    kpiDesvio.textContent = (pct > 0 ? '+' : '') + pct.toFixed(1) + '%';
    kpiDesvio.className = 'kpi-value ' + (pct >= 0 ? 'green' : 'red');
    
    document.getElementById('kpi-desvio-label').textContent = pct >= 0 ? 'Prévia acima do orçado' : 'Prévia abaixo do orçado';
}

function deriveMcPercent(item) {
    const getOrc = (cat) => {
        if (!item.orcamento) return 0;
        const record = item.orcamento.find(o => o.categoria === cat);
        return record ? record.valor : 0;
    };

    const getPrevia = (cat) => {
        if (!item.previas) return 0;
        const lowerCat = cat?.toString().trim().toLowerCase();
        const record = item.previas.find(o => o.categoria?.toString().trim().toLowerCase() === lowerCat);
        return record ? record.valor : 0;
    };

    const rl_orcado = item.rl_orcado ?? getOrc('Receita Líquida');
    const rl_previa = item.total_rl ?? getPrevia('Receita Líquida');

    const lineValues = [
        { label: '(-) Pessoal', orc: item.pessoal_orcado ?? getOrc('Pessoal'), pre: item.pessoal_previa ?? getPrevia('Pessoal') },
        { label: '(-) Aluguéis', orc: getOrc('Aluguéis'), pre: getPrevia('Aluguéis') },
        { label: '(-) Despesas Gerais', orc: getOrc('Despesas Gerais'), pre: getPrevia('Despesas Gerais') },
        { label: '(-) Frota', orc: getOrc('Frota'), pre: getPrevia('Frota') },
        { label: '(-) Impostos, Taxas e Multas', orc: getOrc('Impostos, Taxas e Multas'), pre: getPrevia('Impostos, Taxas e Multas') },
        { label: '(-) Manutenção da Operação', orc: getOrc('Manutenção da Operação'), pre: getPrevia('Manutenção da Operação') },
        { label: '(-) Manutenção de Máquinas', orc: getOrc('Manutenção de Máquinas'), pre: getPrevia('Manutenção de Máquinas') },
        { label: '(-) Manutenção Predial', orc: getOrc('Manutenção Predial'), pre: getPrevia('Manutenção Predial') },
        { label: '(-) Marketing', orc: getOrc('Marketing'), pre: getPrevia('Marketing') },
        { label: '(-) Outros', orc: getOrc('Outros'), pre: getPrevia('Outros') },
        { label: '(-) Pontuais', orc: getOrc('Pontuais'), pre: getPrevia('Pontuais') },
        { label: '(-) Seguros', orc: getOrc('Seguros'), pre: getPrevia('Seguros') },
        { label: '(-) Serviços de Terceiros', orc: getOrc('Serviços de Terceiros'), pre: getPrevia('Serviços de Terceiros') },
        { label: '(-) Telecomunicações', orc: getOrc('Telecomunicações'), pre: getPrevia('Telecomunicações') },
        { label: '(-) TI', orc: getOrc('TI'), pre: getPrevia('TI') },
        { label: '(-) Treinamentos', orc: getOrc('Treinamentos'), pre: getPrevia('Treinamentos') },
        { label: '(-) Utilidades', orc: getOrc('Utilidades'), pre: getPrevia('Utilidades') },
        { label: '(-) Viagens', orc: getOrc('Viagens'), pre: getPrevia('Viagens') },
        { label: '(-) Rateios', orc: item.rateio_orcado ?? getOrc('Rateio'), pre: item.rateio_previa ?? getPrevia('Rateio') },
        { label: '(+) Rec. Outros Gastos', orc: Math.abs(item.recuperacao_orcado ?? getOrc('Recuperação Outros Gastos')), pre: Math.abs(item.recuperacao_previa ?? getPrevia('Recuperação Outros Gastos')) },
        { label: '(+) Rec. Pessoal', orc: Math.abs(getOrc('Recuperação Pessoal')), pre: Math.abs(getPrevia('Recuperação Pessoal')) }
    ];

    const costTotalOrcado = lineValues.reduce((sum, line) => sum + line.orc, 0);
    const costTotalPrevia = lineValues.reduce((sum, line) => sum + line.pre, 0);

    const mc_orcado = item.mc_orcado ?? (rl_orcado + costTotalOrcado);
    const mc_previa = item.mc_previa ?? (rl_previa + costTotalPrevia);

    const mc_pct_orcado = item.mc_pct_orcado ?? (rl_orcado ? (mc_orcado / rl_orcado) * 100 : 0);
    const mc_pct_previa = item.mc_pct_previa ?? (rl_previa ? (mc_previa / rl_previa) * 100 : 0);

    return { mc_pct_orcado, mc_pct_previa };
}

function renderTable() {
    const tbody = document.getElementById('cr-table-body');
    tbody.innerHTML = '';
    
    tableData.forEach(item => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.id = `row-${item.cr}`;
        tr.onclick = () => toggleDRE(item.cr);

        const { mc_pct_orcado, mc_pct_previa } = deriveMcPercent(item);
        const desvio = mc_pct_previa - mc_pct_orcado;
        const pct = mc_pct_orcado > 0
            ? ((desvio / mc_pct_orcado) * 100)
            : null;
        const pctDisplay = pct !== null ? (pct > 0 ? '+' : '') + pct.toFixed(1) + '%' : '—';

        const atingimento = mc_pct_orcado > 0
            ? ((mc_pct_previa / mc_pct_orcado) * 100)
            : null;
        const barWidth = atingimento !== null ? Math.min(Math.max(atingimento, 0), 100) : 0;
        const barColor = atingimento >= 100 ? '#15803D' : atingimento >= 80 ? '#B45309' : '#BE123C';
        const atingDisplay = atingimento !== null ? atingimento.toFixed(0) + '%' : '—';

        let desvioClass = '';
        if (desvio > 0) desvioClass = 'val-pos';
        else if (desvio < 0) desvioClass = 'val-neg';

        const mcPrevColorClass = mc_pct_previa < mc_pct_orcado ? 'val-neg' : '';

        let pctHtml = pctDisplay;
        if (pct !== null && Math.abs(pct) < 5 && mc_pct_orcado > 0) {
            pctHtml = `<span class="badge-warning">${pctHtml}</span>`;
        }

        const isExpanded = expandedCRs.has(item.cr);
        const icon = isExpanded ? '▼' : '▶';

        tr.innerHTML = `
            <td style="font-weight: 500;">
                <span id="icon-${item.cr}" style="display:inline-block; width:20px; color: var(--text-secondary);">${icon}</span> 
                ${item.cr || 'N/A'}
            </td>
            <td style="color: var(--text-secondary);">${item.des_cr || '-'}</td>
            <td class="col-num">${mc_pct_orcado.toFixed(1)}%</td>
            <td class="col-num ${mcPrevColorClass}" style="font-weight: 500;">${mc_pct_previa.toFixed(1)}%</td>
            <td class="col-num ${desvioClass}">${desvio > 0 ? '+' : ''}${desvio.toFixed(1)}pp</td>
            <td class="col-num">${pctHtml}</td>
            <td class="col-num">
                <div style="display:flex; flex-direction:column; align-items:flex-end;">
                    <span style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 2px;">${atingDisplay}</span>
                    ${atingimento !== null && atingimento >= 0 ? `
                    <div class="bar-container" style="width: 60px;">
                        <div class="bar-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
                    </div>` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(tr);

        if (isExpanded) {
            const dreTr = renderDRE(item);
            tbody.appendChild(dreTr);
        }
    });
}

function toggleDRE(cr) {
    const icon = document.getElementById(`icon-${cr}`);
    const existing = document.getElementById(`dre-row-${cr}`);
    if (existing) {
        existing.remove();
        expandedCRs.delete(cr);
        if (icon) icon.textContent = '▶';
        return;
    }

    expandedCRs.add(cr);
    if (icon) icon.textContent = '▼';

    const item = tableData.find(i => i.cr === cr);
    if (item) {
        const dreTr = renderDRE(item);
        const tr = document.getElementById(`row-${cr}`);
        tr.parentNode.insertBefore(dreTr, tr.nextSibling);
    }
}

function renderDRE(item) {
    const dreTr = document.createElement('tr');
    dreTr.id = `dre-row-${item.cr}`;

    const td = document.createElement('td');
    td.colSpan = 8;
    td.style.padding = '0';
    td.style.border = 'none';

    const container = document.createElement('div');
    container.className = 'dre-container';

    const header = document.createElement('div');
    header.className = 'dre-header';
    header.textContent = `DRE — CR ${item.cr} · ${item.des_cr || ''}`;
    container.appendChild(header);

    const table = document.createElement('table');
    table.className = 'comparativo-table';

    table.innerHTML = `
        <thead>
            <tr>
                <th>Linha</th>
                <th>Orçado</th>
                <th>Prévia</th>
                <th>Δ R$</th>
                <th></th>
            </tr>
        </thead>
    `;

    const tbody = document.createElement('tbody');

    const getOrcado = (cat) => {
        if (!item.orcamento) return 0;
        const record = item.orcamento.find(o => o.categoria === cat);
        return record ? record.valor : 0;
    };

    const getPrevia = (cat) => {
        if (!item.previas) return 0;
        const lowerCat = cat?.toString().trim().toLowerCase();
        const record = item.previas.find(o => o.categoria?.toString().trim().toLowerCase() === lowerCat);
        return record ? record.valor : 0;
    };

    const rb_orcado = item.rb_orcado ?? getOrcado('Receita Bruta');
    const rb_previa = item.total_rb ?? getPrevia('Receita Bruta');
    const rl_orcado = item.rl_orcado ?? getOrcado('Receita Líquida');
    const rl_previa = item.total_rl ?? getPrevia('Receita Líquida');

    const ded_orcado = rb_orcado - rl_orcado;
    const ded_previa = rb_previa - rl_previa;

    const lineValues = [
        { label: 'Receita Bruta', orc: rb_orcado, pre: rb_previa, slug: categorySlugs['Receita Bruta'], apiKey: 'Receita Bruta', isPos: true, type: 'receita', clickable: rb_previa !== 0 },
        { label: '(-) Deduções', orc: ded_orcado, pre: ded_previa, slug: categorySlugs['Deduções'], apiKey: 'Deduções', isPos: false, type: 'receita', clickable: ded_previa !== 0 },
        { label: '= Receita Líquida', orc: rl_orcado, pre: rl_previa, subtotal: 'rl', slug: categorySlugs['Receita Líquida'], isPos: true, type: 'receita' },
        { label: '(-) Pessoal', orc: item.pessoal_orcado ?? getOrcado('Pessoal'), pre: item.pessoal_previa ?? getPrevia('Pessoal'), slug: categorySlugs['Pessoal'], apiKey: 'Pessoal', isPos: false, type: 'custo', clickable: (item.pessoal_previa ?? getPrevia('Pessoal')) !== 0 },
        { label: '(-) Aluguéis', orc: getOrcado('Aluguéis'), pre: getPrevia('Aluguéis'), slug: categorySlugs['Aluguéis'], apiKey: 'Aluguéis', isPos: false, type: 'custo', clickable: getPrevia('Aluguéis') !== 0 },
        { label: '(-) Despesas Gerais', orc: getOrcado('Despesas Gerais'), pre: getPrevia('Despesas Gerais'), slug: categorySlugs['Despesas Gerais'], apiKey: 'Despesas Gerais', isPos: false, type: 'custo', clickable: getPrevia('Despesas Gerais') !== 0 },
        { label: '(-) Frota', orc: getOrcado('Frota'), pre: getPrevia('Frota'), slug: categorySlugs['Frota'], apiKey: 'Frota', isPos: false, type: 'custo', clickable: getPrevia('Frota') !== 0 },
        { label: '(-) Impostos, Taxas e Multas', orc: getOrcado('Impostos, Taxas e Multas'), pre: getPrevia('Impostos, Taxas e Multas'), slug: categorySlugs['Impostos, Taxas e Multas'], apiKey: 'Impostos, Taxas e Multas', isPos: false, type: 'custo', clickable: getPrevia('Impostos, Taxas e Multas') !== 0 },
        { label: '(-) Manutenção da Operação', orc: getOrcado('Manutenção da Operação'), pre: getPrevia('Manutenção da Operação'), slug: categorySlugs['Manutenção da Operação'], apiKey: 'Manutenção da Operação', isPos: false, type: 'custo', clickable: getPrevia('Manutenção da Operação') !== 0 },
        { label: '(-) Manutenção de Máquinas', orc: getOrcado('Manutenção de Máquinas'), pre: getPrevia('Manutenção de Máquinas'), slug: categorySlugs['Manutenção de Máquinas'], apiKey: 'Manutenção de Máquinas', isPos: false, type: 'custo', clickable: getPrevia('Manutenção de Máquinas') !== 0 },
        { label: '(-) Manutenção Predial', orc: getOrcado('Manutenção Predial'), pre: getPrevia('Manutenção Predial'), slug: categorySlugs['Manutenção Predial'], apiKey: 'Manutenção Predial', isPos: false, type: 'custo', clickable: getPrevia('Manutenção Predial') !== 0 },
        { label: '(-) Marketing', orc: getOrcado('Marketing'), pre: getPrevia('Marketing'), slug: categorySlugs['Marketing'], apiKey: 'Marketing', isPos: false, type: 'custo', clickable: getPrevia('Marketing') !== 0 },
        { label: '(-) Outros', orc: getOrcado('Outros'), pre: getPrevia('Outros'), slug: categorySlugs['Outros'], apiKey: 'Outros', isPos: false, type: 'custo', clickable: getPrevia('Outros') !== 0 },
        { label: '(-) Pontuais', orc: getOrcado('Pontuais'), pre: getPrevia('Pontuais'), slug: categorySlugs['Pontuais'], apiKey: 'Pontuais', isPos: false, type: 'custo', clickable: getPrevia('Pontuais') !== 0 },
        { label: '(-) Seguros', orc: getOrcado('Seguros'), pre: getPrevia('Seguros'), slug: categorySlugs['Seguros'], apiKey: 'Seguros', isPos: false, type: 'custo', clickable: getPrevia('Seguros') !== 0 },
        { label: '(-) Serviços de Terceiros', orc: getOrcado('Serviços de Terceiros'), pre: getPrevia('Serviços de Terceiros'), slug: categorySlugs['Serviços de Terceiros'], apiKey: 'Serviços de Terceiros', isPos: false, type: 'custo', clickable: getPrevia('Serviços de Terceiros') !== 0 },
        { label: '(-) Telecomunicações', orc: getOrcado('Telecomunicações'), pre: getPrevia('Telecomunicações'), slug: categorySlugs['Telecomunicações'], apiKey: 'Telecomunicações', isPos: false, type: 'custo', clickable: getPrevia('Telecomunicações') !== 0 },
        { label: '(-) TI', orc: getOrcado('TI'), pre: getPrevia('TI'), slug: categorySlugs['TI'], apiKey: 'TI', isPos: false, type: 'custo', clickable: getPrevia('TI') !== 0 },
        { label: '(-) Treinamentos', orc: getOrcado('Treinamentos'), pre: getPrevia('Treinamentos'), slug: categorySlugs['Treinamentos'], apiKey: 'Treinamentos', isPos: false, type: 'custo', clickable: getPrevia('Treinamentos') !== 0 },
        { label: '(-) Utilidades', orc: getOrcado('Utilidades'), pre: getPrevia('Utilidades'), slug: categorySlugs['Utilidades'], apiKey: 'Utilidades', isPos: false, type: 'custo', clickable: getPrevia('Utilidades') !== 0 },
        { label: '(-) Viagens', orc: getOrcado('Viagens'), pre: getPrevia('Viagens'), slug: categorySlugs['Viagens'], apiKey: 'Viagens', isPos: false, type: 'custo', clickable: getPrevia('Viagens') !== 0 },
        { label: '(-) Rateios', orc: item.rateio_orcado ?? getOrcado('Rateio'), pre: item.rateio_previa ?? getPrevia('Rateio'), slug: categorySlugs['Rateio'], apiKey: 'Rateio', isPos: false, type: 'custo', clickable: (item.rateio_previa ?? getPrevia('Rateio')) !== 0 },
        { label: '(+) Rec. Outros Gastos', orc: Math.abs(item.recuperacao_orcado ?? getOrcado('Recuperação Outros Gastos')), pre: Math.abs(item.recuperacao_previa ?? getPrevia('Recuperação Outros Gastos')), slug: categorySlugs['Recuperação Outros Gastos'], apiKey: 'Recuperação Outros Gastos', isPos: true, type: 'receita', clickable: (item.recuperacao_previa ?? getPrevia('Recuperação Outros Gastos')) !== 0 },
        { label: '(+) Rec. Pessoal', orc: Math.abs(getOrcado('Recuperação Pessoal')), pre: Math.abs(getPrevia('Recuperação Pessoal')), slug: categorySlugs['Recuperação Pessoal'], apiKey: 'Recuperação Pessoal', isPos: true, type: 'receita', clickable: getPrevia('Recuperação Pessoal') !== 0 }
    ];

    const corDelta = (valor, tipo) => {
        if (tipo === 'custo') return valor >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
        return valor >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    };

    const costLines = lineValues.filter(line => !line.subtotal && !['Receita Bruta', '(-) Deduções', '= Receita Líquida'].includes(line.label) && !line.label.startsWith('(+)'));
    const recoveryLines = lineValues.filter(line => !line.subtotal && line.label.startsWith('(+)'));

    const costTotalOrcado = costLines.reduce((sum, line) => sum + line.orc, 0) + recoveryLines.reduce((sum, line) => sum + line.orc, 0);
    const costTotalPrevia = costLines.reduce((sum, line) => sum + line.pre, 0) + recoveryLines.reduce((sum, line) => sum + line.pre, 0);

    const mc_orcado = item.mc_orcado ?? (rl_orcado + costTotalOrcado);
    const mc_previa = item.mc_previa ?? (rl_previa + costTotalPrevia);
    const mc_pct_orcado = item.mc_pct_orcado ?? 0;
    const mc_pct_previa = item.mc_pct_previa ?? (rl_previa ? (mc_previa / rl_previa) * 100 : 0);

    lineValues.push({ label: '= Custo Total', orc: costTotalOrcado, pre: costTotalPrevia, subtotal: 'cost', isPos: true, type: 'custo' });
    lineValues.push({ label: '= Margem Contribuição', orc: mc_orcado, pre: mc_previa, subtotal: 'mc', isPos: true, type: 'receita', clickable: false });
    lineValues.push({ label: 'MC %', orc: mc_pct_orcado, pre: mc_pct_previa, isPercent: true, isPos: true, type: 'receita' });

    const createLine = (line) => {
        const tr = document.createElement('tr');
        if (line.subtotal) {
            tr.classList.add('subtotal', line.subtotal);
            if (line.subtotal === 'mc' && Math.min(line.orc, line.pre) < 0) {
                tr.classList.add('negative');
            }
        }

        const tdLabel = document.createElement('td');
        tdLabel.textContent = line.label;
        tr.appendChild(tdLabel);

        const tdOrc = document.createElement('td');
        tdOrc.textContent = line.isPercent ? `${line.orc.toFixed(1)}%` : formatCurrency(line.orc);
        if (line.label === '= Margem Contribuição') {
            tdOrc.style.color = line.orc >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
        }
        tr.appendChild(tdOrc);

        const tdPre = document.createElement('td');
        if (line.clickable && line.pre !== 0) {
            const icon = document.createElement('span');
            icon.className = 'drill-icon';
            icon.textContent = '⊕';
            tdPre.appendChild(icon);
            tdPre.appendChild(document.createTextNode(line.isPercent ? `${line.pre.toFixed(1)}%` : formatCurrency(line.pre)));
            tr.classList.add('clickable');
            tr.classList.add('compare-row');
            tr.style.cursor = 'pointer';
            tr.addEventListener('click', async () => {
                const next = tr.nextElementSibling;
                if (next && next.classList.contains('comparativo-details-row')) {
                    next.remove();
                    icon.textContent = '⊕';
                    return;
                }

                icon.textContent = '⊖';

                const detailRow = document.createElement('tr');
                detailRow.className = 'comparativo-details-row dre-line';
                const detailCell = document.createElement('td');
                detailCell.colSpan = 5;
                detailCell.style.padding = '0';
                detailRow.appendChild(detailCell);

                const loading = document.createElement('div');
                loading.className = 'comparativo-details-box';
                loading.textContent = 'Carregando detalhes...';
                detailCell.appendChild(loading);
                tr.parentNode.insertBefore(detailRow, next || tr.nextSibling);

                const mes = item.mes_ref || document.getElementById('filter-mes')?.value || '';
                const slug = line.slug || categorySlugs[line.apiKey] || line.apiKey;
                const entries = await fetchLancamentos(item.cr, slug, mes);

                detailCell.innerHTML = '';
                const detailsContainer = document.createElement('div');
                detailsContainer.className = 'comparativo-details-box';

                if (!entries || entries.length === 0) {
                    const empty = document.createElement('div');
                    empty.className = 'comparativo-details-empty';
                    empty.textContent = 'Sem lançamentos detalhados para esta categoria.';
                    detailsContainer.appendChild(empty);
                } else {
                    const detailTable = document.createElement('table');
                    detailTable.className = 'comparativo-details-table';
                    detailTable.innerHTML = `
                        <thead>
                            <tr>
                                <th>Descrição</th>
                                <th>CR Origem</th>
                                <th>Descrição CR Origem</th>
                                <th>Responsável CR Envio</th>
                                <th>Valor</th>
                            </tr>
                        </thead>
                    `;
                    const detailBody = document.createElement('tbody');
                    entries.forEach(entry => {
                        const entryRow = document.createElement('tr');
                        const descTd = document.createElement('td');
                        descTd.textContent = entry.descricao || '-';
                        entryRow.appendChild(descTd);

                        const origemTd = document.createElement('td');
                        origemTd.textContent = entry.origem || '-';
                        entryRow.appendChild(origemTd);

                        const descOrigemTd = document.createElement('td');
                        descOrigemTd.textContent = entry.descricao_cr_envio || '-';
                        entryRow.appendChild(descOrigemTd);

                        const responsavelTd = document.createElement('td');
                        responsavelTd.textContent = entry.responsavel_cr_envio || '-';
                        entryRow.appendChild(responsavelTd);

                        const valorTd = document.createElement('td');
                        valorTd.textContent = formatCurrency(entry.valor ?? 0);
                        entryRow.appendChild(valorTd);
                        detailBody.appendChild(entryRow);
                    });
                    detailTable.appendChild(detailBody);
                    detailsContainer.appendChild(detailTable);
                }

                detailCell.appendChild(detailsContainer);
            });
        } else {
            tdPre.textContent = line.isPercent ? `${line.pre.toFixed(1)}%` : formatCurrency(line.pre);
        }
        tr.appendChild(tdPre);

        tr.classList.add('compare-row');
        const tdDiff = document.createElement('td');
        const tipo = line.type || 'receita';
        if (line.isPercent) {
            const diff = line.pre - line.orc;
            tdDiff.textContent = `${diff >= 0 ? '+' : ''}${diff.toFixed(1)}%`;
            tdDiff.style.color = corDelta(diff, tipo);
        } else {
            const diff = tipo === 'custo' ? line.orc - line.pre : line.pre - line.orc;
            tdDiff.textContent = `${diff > 0 ? '+' : ''}${formatCurrency(diff)}`;
            tdDiff.style.color = corDelta(diff, tipo);
        }
        tr.appendChild(tdDiff);

        const tdBar = document.createElement('td');
        tdBar.style.width = '100px';
        tdBar.style.paddingLeft = '16px';
        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';
        const barFill = document.createElement('div');
        barFill.className = 'bar-fill';
        const maxVal = Math.max(Math.abs(line.orc), Math.abs(line.pre));
        const barWidth = maxVal > 0 ? (Math.abs(line.pre) / maxVal) * 100 : 0;
        barFill.style.width = `${barWidth}%`;
        barFill.style.background = line.isPos ? 'var(--accent-green)' : 'var(--accent-red)';
        barContainer.appendChild(barFill);
        tdBar.appendChild(barContainer);
        tr.appendChild(tdBar);

        return tr;
    };

    lineValues.forEach(line => tbody.appendChild(createLine(line)));
    table.appendChild(tbody);
    container.appendChild(table);
    td.appendChild(container);
    dreTr.appendChild(td);
    return dreTr;
}

async function fetchLancamentos(cr, categoria, mes) {
    try {
        const url = new URL(`${API_BASE}/cr/${encodeURIComponent(cr)}/lancamentos`, window.location.origin);
        url.searchParams.append('categoria', categoria);
        if (mes) url.searchParams.append('mes', mes);

        const response = await window.authHelpers.fetchWithAuth(url.href);
        if (response.status === 404) {
            return null;
        }

        const data = await response.json();
        return Array.isArray(data) ? data : null;
    } catch (err) {
        console.error('Erro ao buscar lançamentos:', err);
        return null;
    }
}

// Initial Call
document.addEventListener('DOMContentLoaded', () => {
    fetchFiltros()
        .catch(err => {
            console.error('Falha ao carregar filtros:', err);
        })
        .finally(() => carregarCRs());
});
