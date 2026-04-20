from typing import Optional
from fastapi import APIRouter
from backend.db.database import get_db_connection

router = APIRouter()


def _build_filters(gerente: Optional[str], diretor: Optional[str], mes: Optional[str]):
    rateio_conditions = []
    ajustes_conditions = []
    orcamento_conditions = []
    folha_conditions = []
    rateio_params = []
    ajustes_params = []
    orcamento_params = []
    folha_params = []

    if gerente:
        rateio_conditions.append("LOWER(TRIM(d_dest.Gerente)) = LOWER(TRIM(?))")
        ajustes_conditions.append("LOWER(TRIM(d_dest.Gerente)) = LOWER(TRIM(?))")
        orcamento_conditions.append("LOWER(TRIM(d.Gerente)) = LOWER(TRIM(?))")
        folha_conditions.append("LOWER(TRIM(d.Gerente)) = LOWER(TRIM(?))")
        rateio_params.append(gerente)
        ajustes_params.append(gerente)
        orcamento_params.append(gerente)
        folha_params.append(gerente)
    if diretor:
        rateio_conditions.append("LOWER(TRIM(d_dest.Diretor)) = LOWER(TRIM(?))")
        ajustes_conditions.append("LOWER(TRIM(d_dest.Diretor)) = LOWER(TRIM(?))")
        orcamento_conditions.append("LOWER(TRIM(d.Diretor)) = LOWER(TRIM(?))")
        folha_conditions.append("LOWER(TRIM(d.Diretor)) = LOWER(TRIM(?))")
        rateio_params.append(diretor)
        ajustes_params.append(diretor)
        orcamento_params.append(diretor)
        folha_params.append(diretor)
    if mes:
        rateio_conditions.append("r.mes_ref = ?")
        ajustes_conditions.append("a.mes_ref = ?")
        orcamento_conditions.append("o.mes_ref = ?")
        folha_conditions.append("p.mes_ref = ?")
        rateio_params.append(mes)
        ajustes_params.append(mes)
        orcamento_params.append(mes)
        folha_params.append(mes)

    return (
        rateio_conditions,
        rateio_params,
        ajustes_conditions,
        ajustes_params,
        orcamento_conditions,
        orcamento_params,
        folha_conditions,
        folha_params,
    )


def _normalize_category(value):
    if value is None:
        return ''
    normalized = str(value).strip().lower()
    if normalized == 'rateios':
        return 'rateio'
    return normalized


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
        rateio_conditions, rateio_params, ajustes_conditions, ajustes_params, orcamento_conditions, orcamento_params, folha_conditions, folha_params = _build_filters(gerente, diretor, mes)
        where_clause_rateio = f" AND {' AND '.join(rateio_conditions)}" if rateio_conditions else ''
        where_clause_ajustes = f" AND {' AND '.join(ajustes_conditions)}" if ajustes_conditions else ''
        where_clause_orcamento = f" AND {' AND '.join(orcamento_conditions)}" if orcamento_conditions else ''
        where_clause_folha = f" AND {' AND '.join(folha_conditions)}" if folha_conditions else ''

        query_rateio = (
            "SELECT 'Rateios' as categoria, r.cr_envio as origem_cr, r.desc_cr_envio as origem_desc, "
            "r.cr as destino_cr, COALESCE(d_dest.Des_CR, r.cr) as destino_desc, SUM(r.rateio) as valor "
            "FROM rateio_automatico r "
            "LEFT JOIN dim_cr d_dest ON d_dest.CR_SAP = r.cr OR d_dest.Cod_Cr = r.cr "
            "WHERE 1=1" + where_clause_rateio + " "
            "GROUP BY r.cr_envio, r.desc_cr_envio, r.cr, COALESCE(d_dest.Des_CR, r.cr) "
            "ORDER BY origem_desc, destino_cr"
        )
        rateio_rows = cursor.execute(query_rateio, rateio_params).fetchall()

        query_ajustes = (
            "SELECT resultado as categoria, cr_envio as origem_cr, desc_cr_envio as origem_desc, "
            "cr_destino as destino_cr, COALESCE(desc_cr_destino, cr_destino) as destino_desc, "
            "SUM(COALESCE(incremento_credito, 0) + COALESCE(incremento_debito, 0)) as valor "
            "FROM ajustamentos_gerencia a "
            "LEFT JOIN dim_cr d_dest ON d_dest.CR_SAP = a.cr_destino OR d_dest.Cod_Cr = a.cr_destino "
            "WHERE 1=1" + where_clause_ajustes + " "
            "GROUP BY resultado, cr_envio, desc_cr_envio, cr_destino, COALESCE(desc_cr_destino, cr_destino) "
            "ORDER BY resultado, origem_desc, destino_cr"
        )
        ajuste_rows = cursor.execute(query_ajustes, ajustes_params).fetchall()

        query_orcamento = (
            "SELECT o.categoria_despesa as categoria, SUM(o.valor_plano) as valor "
            "FROM orcamento_previa o "
            "LEFT JOIN dim_cr d ON d.CR_SAP = o.cr OR d.Cod_Cr = o.cr "
            "WHERE o.cr IS NOT NULL" + where_clause_orcamento + " "
            "GROUP BY o.categoria_despesa"
        )
        orcamento_rows = cursor.execute(query_orcamento, orcamento_params).fetchall()
        orcamento_totals = {
            _normalize_category(row['categoria']): float(row['valor'] or 0.0)
            for row in orcamento_rows
        }

        query_folha = (
            "SELECT SUM(p.valor) as valor "
            "FROM previa_folha_th p "
            "LEFT JOIN dim_cr d ON d.CR_SAP = p.cr OR d.Cod_Cr = p.cr "
            "WHERE p.cr IS NOT NULL" + where_clause_folha
        )
        folha_total = float((cursor.execute(query_folha, folha_params).fetchone()['valor'] or 0.0))

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

        # Populate orcado totals from orcamento_previa and add folha TH as preview for Pessoal
        for categoria, entry in categories.items():
            entry['total_orcado'] = orcamento_totals.get(_normalize_category(categoria), 0.0)

        if folha_total:
            pessoal_key = next((key for key in categories if _normalize_category(key) == 'pessoal'), None)
            folha_origem_key = 'Folha TH'
            if pessoal_key:
                categories[pessoal_key]['total_previa'] += folha_total
                if folha_origem_key not in categories[pessoal_key]['origens']:
                    categories[pessoal_key]['origens'][folha_origem_key] = {
                        'origem': folha_origem_key,
                        'total': 0.0,
                        'crs': []
                    }
                categories[pessoal_key]['origens'][folha_origem_key]['total'] += folha_total
            elif 'pessoal' in orcamento_totals:
                categories['Pessoal'] = {
                    'linha': 'Pessoal',
                    'total_orcado': orcamento_totals.get('pessoal', 0.0),
                    'total_previa': folha_total,
                    'origens': {
                        folha_origem_key: {
                            'origem': folha_origem_key,
                            'total': folha_total,
                            'crs': []
                        }
                    }
                }

        result = []
        for categoria in sorted(categories.keys()):
            category_entry = categories[categoria]
            category_entry['origens'] = [categories[categoria]['origens'][key] for key in sorted(categories[categoria]['origens'].keys())]
            result.append(category_entry)

        return result
