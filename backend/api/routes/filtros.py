from fastapi import APIRouter
import backend.db.database as database

router = APIRouter()

@router.get("/filtros")
def listar_filtros():
    return database.get_filtros()
