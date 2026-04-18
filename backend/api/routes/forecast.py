from fastapi import APIRouter
from typing import Optional
import subprocess
import backend.db.database as database

router = APIRouter()

@router.get("/oportunidades")
def listar_oportunidades(
    gerente: Optional[str] = None,
    diretor: Optional[str] = None,
    pais: Optional[str] = None,
    cliente: Optional[str] = None,
    pratica: Optional[str] = None,
    produto: Optional[str] = None,
    cr: Optional[str] = None,
    mes: Optional[str] = None,
    page: int = 1
):
    filtros = {
        "gerente": gerente,
        "diretor": diretor,
        "pais": pais,
        "cliente": cliente,
        "pratica": pratica,
        "produto": produto,
        "cr": cr,
        "mes": mes,
        "page": page
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}
    return database.get_oportunidades(filtros)

@router.get("/oportunidades/{chave_ek}")
def detalhe_oportunidade(chave_ek: str):
    return {"chave_ek": chave_ek, "detalhes": "Em construção"}

@router.get("/resumo")
def resumo(
    gerente: Optional[str] = None,
    diretor: Optional[str] = None,
    pais: Optional[str] = None,
    cliente: Optional[str] = None,
    pratica: Optional[str] = None,
    produto: Optional[str] = None,
    cr: Optional[str] = None,
    mes: Optional[str] = None
):
    filtros = {
        "gerente": gerente,
        "diretor": diretor,
        "pais": pais,
        "cliente": cliente,
        "pratica": pratica,
        "produto": produto,
        "cr": cr,
        "mes": mes
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}
    return database.get_resumo(filtros)

@router.post("/etl/executar")
def executar_etl():
    try:
        result = subprocess.run(
            ["python", "backend/etl/etl_forecast.py"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        if result.returncode == 0:
            return {"status": "sucesso", "mensagem": "ETL executado com sucesso!"}
        return {"status": "erro", "mensagem": "Falha no ETL: " + result.stderr}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

@router.get("/etl/status")
def status_etl():
    return {"status": "sucesso", "ultima_carga": "2026-04-17 10:00:00"}
