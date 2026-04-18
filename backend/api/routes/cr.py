from fastapi import APIRouter
from typing import Optional
import backend.db.database as database

router = APIRouter()

@router.get("/resumo/cr")
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
    return database.get_resumo_por_cr(filtros)

@router.get("/cr/{cr}/lancamentos")
def lancamentos_por_cr(cr: str, categoria: str, mes: Optional[str] = None):
    return database.get_lancamentos_por_cr_categoria(cr, categoria, mes)
