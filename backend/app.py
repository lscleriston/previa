from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import backend.database as database

app = FastAPI(title="Forecast App API")

# Permite acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API está rodando"}

@app.get("/api/filtros")
def listar_filtros():
    return database.get_filtros()

@app.get("/api/oportunidades")
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
    # Remove valores vazios
    filtros = {k: v for k, v in filtros.items() if v is not None}
    return database.get_oportunidades(filtros)

@app.get("/api/oportunidades/{chave_ek}")
def detalhe_oportunidade(chave_ek: str):
    # Pode ser feito um endpoint mais completo.
    return {"chave_ek": chave_ek, "detalhes": "Em construção"}

@app.get("/api/resumo")
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

import subprocess

@app.post("/api/etl/executar")
def executar_etl():
    try:
        # A pasta root é /app
        result = subprocess.run(["python", "etl_forecast.py"], capture_output=True, text=True, cwd="/app")
        if result.returncode == 0:
            return {"status": "sucesso", "mensagem": "ETL executado com sucesso!"}
        else:
            return {"status": "erro", "mensagem": "Falha no ETL: " + result.stderr}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

@app.get("/api/etl/status")
def status_etl():
    return {"status": "sucesso", "ultima_carga": "2026-04-17 10:00:00"}



@app.get("/api/resumo/cr")
def resumo_cr(
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
        "gerente": gerente, "diretor": diretor, "pais": pais, "cliente": cliente, "pratica": pratica, "produto": produto, "cr": cr, "mes": mes
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}
    return database.get_resumo_por_cr(filtros)

@app.get("/api/cr/{cr}/lancamentos")
def lancamentos_por_cr(cr: str, categoria: str, mes: Optional[str] = None):
    lancamentos = database.get_lancamentos_por_cr_categoria(cr, categoria, mes)
    return lancamentos
