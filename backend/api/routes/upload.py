import json
import os
import queue
import sys
import threading
import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.responses import StreamingResponse

router = APIRouter()

ROOT_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = ROOT_DIR / 'data' / 'raw'
UPLOAD_PATH = UPLOAD_DIR / 'forecast_upload.xlsx'
DB_PATH = os.environ.get('DB_PATH', str(ROOT_DIR / 'data' / 'db' / 'previadb.db'))

ETL_STEPS = [
    ("Validando arquivo", 5, "init_db"),
    ("Limpando banco", 10, "drop_tables"),
    ("Recriando estrutura", 15, "init_db"),
    ("ETL Dimensão CR", 25, "etl_dim_cr"),
    ("ETL Forecast", 45, "etl_forecast"),
    ("ETL Orçado/Prévia", 60, "etl_orcado_previa"),
    ("ETL Folha de Pessoal", 75, "etl_previa_folha"),
    ("ETL Gerências", 88, "etl_gerencias"),
    ("ETL Rateio Custo Direto", 92, "etl_rateio_custo"),
    ("Verificando integridade", 95, "verify_cr"),
    ("Concluído", 100, None),
]

JOB_STORE = {}
EVENT_SENTINEL = None


def build_sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def emit_event(job_id: str, etapa: str, pct: int, status: str, log: str):
    job = JOB_STORE.get(job_id)
    if not job:
        return
    job['queue'].put(build_sse_event({
        'etapa': etapa,
        'pct': pct,
        'status': status,
        'log': log
    }))


def get_script_path(name: str) -> Path:
    if name == 'verify_cr':
        return ROOT_DIR / 'backend' / 'utils' / 'verify_cr.py'
    if name == 'init_db':
        return ROOT_DIR / 'backend' / 'db' / 'init_db.py'
    return ROOT_DIR / 'backend' / 'etl' / f'{name}.py'


def run_script(job_id: str, etapa: str, pct: int, script_name: str) -> bool:
    script_path = get_script_path(script_name)
    if not script_path.exists():
        emit_event(job_id, etapa, pct, 'erro', f'Script não encontrado: {script_path.name}')
        return False

    emit_event(job_id, etapa, pct, 'em_andamento', f'Executando {script_path.name}...')

    env = os.environ.copy()
    env['XLSX_PATH'] = str(UPLOAD_PATH)
    env['DB_PATH'] = DB_PATH

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            env=env,
            timeout=3600
        )
    except subprocess.TimeoutExpired:
        emit_event(job_id, etapa, pct, 'erro', f'{script_path.name} excedeu o tempo limite')
        return False

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or 'Erro desconhecido'
        emit_event(job_id, etapa, pct, 'erro', f'{script_path.name} falhou: {message}')
        return False

    emit_event(job_id, etapa, pct, 'ok', f'{script_path.name} concluído com sucesso')
    return True


def run_drop_tables(job_id: str, etapa: str, pct: int) -> bool:
    emit_event(job_id, etapa, pct, 'em_andamento', 'Removendo tabelas existentes...')
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(
            """
            DROP TABLE IF EXISTS forecast_oportunidades;
            DROP TABLE IF EXISTS forecast_valores;
            DROP TABLE IF EXISTS etl_log;
            DROP TABLE IF EXISTS previa_folha_th;
            DROP TABLE IF EXISTS rateio_automatico;
            DROP TABLE IF EXISTS dim_cr;
            DROP TABLE IF EXISTS ajustamentos_gerencia;
            """
        )
        conn.commit()
        conn.close()
        emit_event(job_id, etapa, pct, 'ok', 'Banco limpo com sucesso')
        return True
    except Exception as exc:
        emit_event(job_id, etapa, pct, 'erro', f'Falha ao limpar banco: {exc}')
        return False


def etl_worker(job_id: str):
    for etapa, pct, script in ETL_STEPS:
        if script is None:
            emit_event(job_id, etapa, pct, 'ok', 'Carga finalizada com sucesso')
            break

        if script == 'drop_tables':
            success = run_drop_tables(job_id, etapa, pct)
        else:
            success = run_script(job_id, etapa, pct, script)

        if not success:
            break

    JOB_STORE[job_id]['queue'].put(EVENT_SENTINEL)


def event_generator(job_id: str):
    job = JOB_STORE.get(job_id)
    if not job:
        return
    while True:
        event = job['queue'].get()
        if event is EVENT_SENTINEL:
            break
        yield event


@router.post('/etl/upload')
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail='Somente arquivos .xlsx são aceitos')

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    with open(UPLOAD_PATH, 'wb') as f:
        f.write(data)

    job_id = str(uuid4())
    JOB_STORE[job_id] = {
        'status': 'recebido',
        'queue': queue.Queue(),
        'thread_started': False,
    }

    return {'job_id': job_id, 'status': 'recebido'}


@router.get('/etl/progresso/{job_id}')
def progresso(job_id: str):
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job não encontrado')

    if not job['thread_started']:
        job['thread_started'] = True
        worker = threading.Thread(target=etl_worker, args=(job_id,), daemon=True)
        job['thread'] = worker
        worker.start()

    return StreamingResponse(
        event_generator(job_id),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache'},
    )
