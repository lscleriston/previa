let currentJobId = null;
let selectedFile = null;
let uploadInProgress = false;

console.log('[atualizar.js] script carregado');

const fileInput = document.getElementById('file-input');
const uploadZone = document.getElementById('upload-zone');
const filePreview = document.getElementById('file-preview');
const fileNameEl = document.getElementById('file-name');
const btnIniciar = document.getElementById('btn-iniciar');
const etapasContainer = document.getElementById('etapas-container');
const logContainer = document.getElementById('log-container');

function atualizarPreview(file) {
  selectedFile = file;
  fileNameEl.textContent = file.name;
  filePreview.style.display = 'flex';
}

if (fileInput) {
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    console.log('[atualizar.js] arquivo selecionado', file.name);
    atualizarPreview(file);
  });
}

if (uploadZone) {
  uploadZone.addEventListener('click', () => {
    fileInput.click();
  });

  uploadZone.addEventListener('dragover', (event) => {
    event.preventDefault();
    uploadZone.classList.add('drag-over');
  });

  uploadZone.addEventListener('dragleave', (event) => {
    event.preventDefault();
    uploadZone.classList.remove('drag-over');
  });

  uploadZone.addEventListener('drop', (event) => {
    event.preventDefault();
    uploadZone.classList.remove('drag-over');
    const file = event.dataTransfer.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.xlsx')) {
      alert('Por favor envie um arquivo .xlsx');
      return;
    }
    atualizarPreview(file);
  });
}

const API_BASE = 'http://127.0.0.1:8001';

async function iniciarCarga() {
  if (btnIniciar?.disabled) {
    console.warn('[atualizar.js] iniciarCarga ignorado porque já está em andamento');
    return;
  }

  if (!selectedFile) {
    alert('Selecione um arquivo .xlsx antes de iniciar a carga.');
    return;
  }

  uploadInProgress = true;
  const form = new FormData();
  form.append('file', selectedFile);

  btnIniciar.disabled = true;
  filePreview.style.display = 'flex';
  document.getElementById('progresso').style.display = 'block';
  etapasContainer.innerHTML = '';
  logContainer.innerHTML = '';

  try {
    const healthUrl = `${API_BASE}/api/health`;
    console.log('[atualizar.js] verificando backend em', healthUrl);
    const healthRes = await fetch(healthUrl, { method: 'GET' });
    console.log('[atualizar.js] health response', healthRes.status, healthRes.statusText);
    if (!healthRes.ok) {
      throw new Error(`Backend indisponível: ${healthRes.status} ${healthRes.statusText}`);
    }

    const url = `${API_BASE}/etl/upload`;
    console.log('[atualizar.js] iniciarCarga chamado', selectedFile);
    console.log('[atualizar.js] upload URL', url);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    const res = await fetch(url, {
      method: 'POST',
      body: form,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    console.log('[atualizar.js] upload response', res.status, res.statusText, res.url);
    if (!res.ok) {
      const text = await res.text();
      console.error('[atualizar.js] upload error body', text);
      throw new Error(text || `Falha ao enviar o arquivo. Status: ${res.status}`);
    }

    const { job_id } = await res.json();
    currentJobId = job_id;
    acompanharProgresso(job_id);
  } catch (error) {
    console.error('[atualizar.js] erro iniciarCarga', error);
    btnIniciar.disabled = false;
    uploadInProgress = false;
    const message = error.name === 'AbortError' ? 'Tempo de upload excedido.' : error.message;
    logContainer.innerHTML = `<p style="color: var(--accent-red)">Erro ao iniciar upload: ${message}</p>`;
  }
}

function acompanharProgresso(job_id) {
  const es = new EventSource(`${API_BASE}/etl/progresso/${job_id}`);

  es.onmessage = (e) => {
    const { etapa, pct, status, log } = JSON.parse(e.data);

    let etapaEl = document.getElementById(`etapa-${etapa}`);
    if (!etapaEl) {
      etapaEl = document.createElement('div');
      etapaEl.id = `etapa-${etapa}`;
      etapaEl.className = 'etapa-item';
      etapasContainer.appendChild(etapaEl);
    }

    const icone = status === 'ok' ? '✓' : status === 'erro' ? '✗' : '○';
    const cor = status === 'ok' ? 'var(--accent-green)' : status === 'erro' ? 'var(--accent-red)' : 'var(--text-muted)';
    etapaEl.innerHTML = `
      <span style="color:${cor}">${icone}</span>
      <span class="etapa-nome">${etapa}</span>
      <div class="etapa-bar-bg"><div class="etapa-bar-fill" style="width:${pct}%"></div></div>
      <span class="etapa-pct">${pct}%</span>
    `;

    if (log) {
      const logEl = document.createElement('p');
      logEl.textContent = `[${new Date().toLocaleTimeString()}] ${log}`;
      logContainer.appendChild(logEl);
      logEl.scrollIntoView();
    }

    if (pct === 100 || status === 'erro') {
      es.close();
      btnIniciar.disabled = false;
    }
  };

  es.onerror = () => {
    es.close();
    logContainer.innerHTML += '<p style="color:var(--accent-red)">Conexão perdida com o servidor.</p>';
    btnIniciar.disabled = false;
  };
}

window.iniciarCarga = iniciarCarga;

document.addEventListener('DOMContentLoaded', () => {
  const startButton = document.getElementById('btn-iniciar');
  if (startButton) {
    console.log('[atualizar.js] adicionando listener ao botão iniciar');
    startButton.addEventListener('click', (event) => {
      event.preventDefault();
      iniciarCarga();
    });
  } else {
    console.warn('[atualizar.js] botão iniciar não encontrado');
  }
});
