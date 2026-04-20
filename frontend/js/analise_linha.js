const expandedLinhas = new Set();
const expandedOrigens = new Set();
let analiseData = [];

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
}

function formatDelta(value) {
    const formatted = formatCurrency(value);
    const span = document.createElement('span');
    span.textContent = formatted;
    span.className = value >= 0 ? 'text-green' : 'text-red';
    return span;
}

async function carregarFiltros() {
    try {
        const response = await window.authHelpers.fetchWithAuth('/api/filtros');
        const filtros = await response.json();

        const preencher = (id, items) => {
            const select = document.getElementById(id);
            if (!select || !Array.isArray(items)) return;
            select.innerHTML = '<option value="">Todos</option>';
            items.forEach(item => {
                if (item === undefined || item === null) return;
                const option = document.createElement('option');
                option.value = item;
                option.textContent = item;
                select.appendChild(option);
            });
        };

        preencher('filter-mes', filtros?.meses);
        preencher('filter-diretor', filtros?.diretores);
        preencher('filter-gerente', filtros?.gerentes);
    } catch (error) {
        console.error('Erro ao carregar filtros:', error);
    }
}

function buildQueryString() {
    const params = new URLSearchParams();
    const mes = document.getElementById('filter-mes')?.value;
    const diretor = document.getElementById('filter-diretor')?.value;
    const gerente = document.getElementById('filter-gerente')?.value;

    if (mes) params.append('mes', mes);
    if (diretor) params.append('diretor', diretor);
    if (gerente) params.append('gerente', gerente);
    return params.toString();
}

async function carregarAnaliseLinha() {
    const tbody = document.getElementById('analise-linha-body');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 18px;">Carregando...</td></tr>';

    try {
        const query = buildQueryString();
        const path = query ? `/api/analise-linha?${query}` : '/api/analise-linha';
        const response = await window.authHelpers.fetchWithAuth(path);
        analiseData = await response.json();
        renderTable();
    } catch (error) {
        console.error('Erro ao carregar análise por linha:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--accent-red); padding: 18px;">Erro ao carregar os dados.</td></tr>';
    }
}

function toggleLinha(linha) {
    if (expandedLinhas.has(linha)) {
        expandedLinhas.delete(linha);
    } else {
        expandedLinhas.add(linha);
    }
    renderTable();
}

function toggleOrigem(linha, origem) {
    const key = `${linha}||${origem}`;
    if (expandedOrigens.has(key)) {
        expandedOrigens.delete(key);
    } else {
        expandedOrigens.add(key);
    }
    renderTable();
}

function renderTable() {
    const tbody = document.getElementById('analise-linha-body');
    tbody.innerHTML = '';

    if (!Array.isArray(analiseData) || analiseData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 18px; color: var(--text-secondary);">Nenhum dado encontrado para os filtros selecionados.</td></tr>';
        return;
    }

    analiseData.forEach(item => {
        const linhaRow = document.createElement('tr');
        linhaRow.classList.add('clickable');
        linhaRow.innerHTML = `
            <td style="font-weight: 700;"><span class="drill-icon">${expandedLinhas.has(item.linha) ? '⊖' : '⊕'}</span>${item.linha}</td>
            <td></td>
            <td class="col-num">${formatCurrency(item.total_orcado)}</td>
            <td class="col-num">${formatCurrency(item.total_previa)}</td>
            <td class="col-num"></td>
        `;
        linhaRow.addEventListener('click', () => toggleLinha(item.linha));
        tbody.appendChild(linhaRow);

        if (!expandedLinhas.has(item.linha)) {
            return;
        }

        item.origens.forEach(origemItem => {
            const origemRow = document.createElement('tr');
            origemRow.classList.add('clickable');
            origemRow.innerHTML = `
                <td style="padding-left: 1.25rem; font-weight: 600;"><span class="drill-icon">${expandedOrigens.has(`${item.linha}||${origemItem.origem}`) ? '⊖' : '⊕'}</span>${origemItem.origem}</td>
                <td></td>
                <td class="col-num"></td>
                <td class="col-num">${formatCurrency(origemItem.total)}</td>
                <td class="col-num"></td>
            `;
            origemRow.addEventListener('click', () => toggleOrigem(item.linha, origemItem.origem));
            tbody.appendChild(origemRow);

            if (!expandedOrigens.has(`${item.linha}||${origemItem.origem}`)) {
                return;
            }

            origemItem.crs.forEach(destino => {
                const crRow = document.createElement('tr');
                crRow.innerHTML = `
                    <td style="padding-left: 2.5rem; color: var(--text-muted);">${destino.cr}</td>
                    <td style="color: var(--text-muted);">${destino.des_cr}</td>
                    <td class="col-num"></td>
                    <td class="col-num">${formatCurrency(destino.valor)}</td>
                    <td class="col-num"></td>
                `;
                tbody.appendChild(crRow);
            });
        });
    });
}

window.addEventListener('load', async () => {
    await carregarFiltros();
    await carregarAnaliseLinha();
});
