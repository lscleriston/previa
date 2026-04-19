// app.js
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8001/api'
    : 'http://backend:8000/api';

async function init() {
    if (document.getElementById('opp-body')) {
        await carregarFiltros();
        await carregarResumo();
        await atualizarDataCarga();
    }
}

async function carregarFiltros() {
    try {
        const response = await fetch(`${API_BASE_URL}/filtros`);
        const filtros = await response.json();
        
        preencherDropdown('filter-gerente', filtros?.gerentes);
        preencherDropdown('filter-pais', filtros?.paises);
        preencherDropdown('filter-cliente', filtros?.clientes);
        preencherDropdown('filter-pratica', filtros?.praticas);
        preencherDropdown('filter-produto', filtros?.produtos);
    } catch (e) {
        console.error("Erro ao carregar filtros", e);
    }
}

function preencherDropdown(id, arrayData) {
    const select = document.getElementById(id);
    if (!select || !Array.isArray(arrayData)) return;

    select.innerHTML = '<option value="">Todos</option>';
    arrayData.forEach(item => {
        if (item) {
            const op = document.createElement('option');
            op.value = item;
            op.innerText = item.length > 30 ? item.substring(0, 30) + '...' : item;
            select.appendChild(op);
        }
    });
}

function getFiltrosAtuais() {
    const getValue = (id) => document.getElementById(id)?.value || '';
    return {
        gerente: getValue('filter-gerente'),
        pais: getValue('filter-pais'),
        cliente: getValue('filter-cliente'),
        pratica: getValue('filter-pratica'),
        produto: getValue('filter-produto')
    };
}

function buildQueryString(filtros) {
    const params = new URLSearchParams();
    for (const key in filtros) {
        if (filtros[key]) params.append(key, filtros[key]);
    }
    return params.toString();
}

async function carregarResumo() {
    const qs = buildQueryString(getFiltrosAtuais());
    try {
        // Carrega KPIs
        const resKpi = await fetch(`${API_BASE_URL}/resumo?${qs}`);
        const dataKpi = await resKpi.json();
        
        document.getElementById('kpi-total-opp').innerText = dataKpi.total_opp.toLocaleString('pt-BR');
        document.getElementById('kpi-rl-forecast').innerText = formatCurrency(dataKpi.rl_total);
        document.getElementById('kpi-rb-total').innerText = formatCurrency(dataKpi.rb_total);

        // Carrega tabela associada
        const resOpp = await fetch(`${API_BASE_URL}/oportunidades?${qs}&page=1`);
        const dataOpp = await resOpp.json();
        renderTable(dataOpp);

    } catch (e) {
        console.error("Erro dados", e);
    }
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
}

function renderTable(oportunidades) {
    const tbody = document.getElementById('opp-body');
    tbody.innerHTML = '';
    
    if(!oportunidades || oportunidades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px">Nenhum dado encontrado</td></tr>';
        return;
    }

    oportunidades.forEach(opp => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${opp.ger_comercial || 'N/D'}</td>
            <td>${opp.pais || 'N/D'}</td>
            <td>${(str => str.length > 20 ? str.substring(0,20)+'...' : str)(opp.cliente || 'N/D')}</td>
            <td>${opp.pratica || 'N/D'} / <br><small style="color:var(--text-secondary)">${opp.produto || 'N/D'}</small></td>
            <td class="text-blue">${formatCurrency(opp.vl_total_forecast_rl)}</td>
            <td class="text-green">${formatCurrency(opp.vl_total_forecast_rb)}</td>
            <td><button class="btn-sm" onclick="alert('Funcionalidade em construção')">Detalhes</button></td>
        `;
        tbody.appendChild(tr);
    });
}

async function atualizarDataCarga() {
    try {
        const res = await fetch(`${API_BASE_URL}/etl/status`);
        const data = await res.json();
        const el = document.getElementById('last-update');
        if (el) el.innerText = data.ultima_carga;
    } catch(e) {}
}

async function atualizarDados() {
    const btn = document.querySelector('.btn-primary');
    const oldText = btn.innerText;
    btn.innerText = "Carregando...";
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE_URL}/etl/executar`, { method: 'POST' });
        const data = await res.json();
        alert(data.mensagem || "ETL disparado com sucesso!");
        await carregarFiltros();
        await carregarResumo();
        await atualizarDataCarga();
    } catch(e) {
        alert("Erro ao rodar ETL");
    } finally {
        btn.innerText = oldText;
        btn.disabled = false;
    }
}

function setTheme(name) {
    document.documentElement.setAttribute('data-theme', name);
    localStorage.setItem('app-theme', name);
    document.querySelectorAll('.theme-menu button').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('onclick').includes(name));
    });
    document.getElementById('theme-menu')?.classList.remove('open');
}

function toggleThemeMenu() {
    document.getElementById('theme-menu')?.classList.toggle('open');
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.theme-switcher')) {
        document.getElementById('theme-menu')?.classList.remove('open');
    }
});

(function initTheme() {
    const saved = localStorage.getItem('app-theme') || 'light-executive';
    setTheme(saved);
})();

// Inicia
init();