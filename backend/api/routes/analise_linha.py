from typing import Optional
from fastapi import APIRouter
from backend.db.database import get_db_connection

router = APIRouter()


def _build_filters(gerente: Optional[str], diretor: Optional[str], mes: Optional[str]):
    conditions = []
    params = []

    if gerente:
        conditions.append("LOWER(TRIM(d_dest.Gerente)) = LOWER(TRIM(?))")
        params.append(gerente)
    if diretor:
        conditions.append("LOWER(TRIM(d_dest.Diretor)) = LOWER(TRIM(?))")
        params.append(diretor)
    if mes:
        conditions.append("r.mes_ref = ?")
        params.append(mes)

    return conditions, params


def _trimmed_value(value):
    if value is None:
        return None
    sanitized = str(value).strip()
    return sanitized if sanitized and sanitized != '0' else None


@router.get("/analise-linha")
def analise_linha(
    gerente: Optional[str] = None,
    diretor: Optional[str] = None,
    mes: Optional[str] = None,
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        conditions, params = _build_filters(gerente, diretor, mes)
        where_clause = f" AND {' AND '.join(conditions)}" if conditions else ''

        query_rateio = (
            "SELECT 'Rateios' as categoria, r.cr_envio as origem_cr, r.desc_cr_envio as origem_desc, "
            "r.cr as destino_cr, COALESCE(d_dest.Des_CR, r.cr) as destino_desc, SUM(r.rateio) as valor "
            "FROM rateio_automatico r "
            "LEFT JOIN dim_cr d_dest ON d_dest.CR_SAP = r.cr OR d_dest.Cod_Cr = r.cr "
            "WHERE 1=1" + where_clause + " "
            "GROUP BY r.cr_envio, r.desc_cr_envio, r.cr, destino_desc "
            "ORDER BY origem_desc, destino_cr"
        )
        rateio_rows = cursor.execute(query_rateio, params).fetchall()

        query_ajustes = (
            "SELECT resultado as categoria, cr_envio as origem_cr, desc_cr_envio as origem_desc, "
            "cr_destino as destino_cr, COALESCE(desc_cr_destino, cr_destino) as destino_desc, "
            "SUM(COALESCE(incremento_credito, 0) + COALESCE(incremento_debito, 0)) as valor "
            "FROM ajustamentos_gerencia a "
            "LEFT JOIN dim_cr d_dest ON d_dest.CR_SAP = a.cr_destino OR d_dest.Cod_Cr = a.cr_destino "
            "WHERE 1=1" + where_clause + " "
            "GROUP BY resultado, cr_envio, desc_cr_envio, cr_destino, destino_desc "
            "ORDER BY resultado, origem_desc, destino_cr"
        )
        ajuste_rows = cursor.execute(query_ajustes, params).fetchall()

        categories = {}

        def _accumulate(row, categoria, origem, destino_cr, destino_desc, valor):
            if categoria is None:
                categoria = 'Sem Categoria'
            if categoria.lower() == 'rateio':
                categoria = 'Rateios'

            if categoria not in categories:
                categories[categoria] = {
                    'linha': categoria,
                    'total_orcado': 0.0,
                    'total_previa': 0.0,
                    'origens': {}
                }

            entry = categories[categoria]
            entry['total_orcado'] += float(valor or 0.0)
            entry['total_previa'] += float(valor or 0.0)

            origem_key = origem or 'Sem Origem'
            if origem_key not in entry['origens']:
                entry['origens'][origem_key] = {
                    'origem': origem_key,
                    'total': 0.0,
                    'crs': []
                }

            origem_entry = entry['origens'][origem_key]
            origem_entry['total'] += float(valor or 0.0)
            origem_entry['crs'].append({
                'cr': destino_cr or '',
                'des_cr': destino_desc or destino_cr or '',
                'valor': float(valor or 0.0)
            })

        for row in rateio_rows:
            origem = _trimmed_value(row['origem_desc']) or _trimmed_value(row['origem_cr']) or 'Sem Origem'
            _accumulate(row, row['categoria'], origem, row['destino_cr'], row['destino_desc'], row['valor'])

        for row in ajuste_rows:
            origem = _trimmed_value(row['origem_desc']) or _trimmed_value(row['origem_cr']) or 'Sem Origem'
            _accumulate(row, row['categoria'], origem, row['destino_cr'], row['destino_desc'], row['valor'])

        result = []
        for categoria in sorted(categories.keys()):
            category_entry = categories[categoria]
            category_entry['origens'] = [categories[categoria]['origens'][key] for key in sorted(categories[categoria]['origens'].keys())]
            result.append(category_entry)

        return result
