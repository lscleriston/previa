import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "db", "previadb.db")
)

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_forecast_oportunidades_schema(conn)
    try:
        yield conn
    finally:
        conn.close()


def get_user_by_username(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, is_admin, created_at FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, is_admin, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def list_users():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, is_admin, created_at FROM users ORDER BY username"
        )
        return [dict(row) for row in cursor.fetchall()]


def create_user(username, password_hash, is_admin=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, int(is_admin), datetime.utcnow().isoformat())
        )
        conn.commit()
        return get_user_by_id(cursor.lastrowid)


def update_user(user_id, username=None, password_hash=None, is_admin=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        if username is not None:
            updates.append("username = ?")
            params.append(username)
        if password_hash is not None:
            updates.append("password_hash = ?")
            params.append(password_hash)
        if is_admin is not None:
            updates.append("is_admin = ?")
            params.append(int(is_admin))
        if not updates:
            return get_user_by_id(user_id)
        params.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
        conn.commit()
        return get_user_by_id(user_id)


def delete_user(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


def ensure_forecast_oportunidades_schema(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(forecast_oportunidades)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'cr2' not in cols:
        cursor.execute("ALTER TABLE forecast_oportunidades ADD COLUMN cr2 TEXT")
        conn.commit()


def get_filtros():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        filtros = {}
        
        cursor.execute("SELECT DISTINCT Gerente as gerente FROM dim_cr WHERE Gerente IS NOT NULL ORDER BY Gerente")
        filtros['gerentes'] = [row['gerente'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Diretor as diretor FROM dim_cr WHERE Diretor IS NOT NULL ORDER BY Diretor")
        filtros['diretores'] = [row['diretor'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Pais as pais FROM dim_cr WHERE Pais IS NOT NULL ORDER BY Pais")
        filtros['paises'] = [row['pais'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Cliente as cliente FROM dim_cr WHERE Cliente IS NOT NULL ORDER BY Cliente")
        filtros['clientes'] = [row['cliente'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT pratica FROM forecast_oportunidades WHERE pratica IS NOT NULL ORDER BY pratica")
        filtros['praticas'] = [row['pratica'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT produto FROM forecast_oportunidades WHERE produto IS NOT NULL ORDER BY produto")
        filtros['produtos'] = [row['produto'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT COALESCE(CR_SAP, Cod_Cr) as cr FROM dim_cr WHERE COALESCE(CR_SAP, Cod_Cr) IS NOT NULL ORDER BY cr")
        filtros['crs'] = [row['cr'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT mes_ref as mes FROM forecast_valores WHERE mes_ref IS NOT NULL ORDER BY mes_ref")
        filtros['meses'] = [row['mes'] for row in cursor.fetchall()]

        return filtros

def get_oportunidades(filtros):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT o.*, 
                   SUM(CASE WHEN v.cenario='Forecast' THEN v.valor_rl ELSE 0 END) as vl_total_forecast_rl,
                   SUM(CASE WHEN v.cenario='Forecast' THEN v.valor_rb ELSE 0 END) as vl_total_forecast_rb
            FROM forecast_oportunidades o
            LEFT JOIN forecast_valores v ON o.chave_ek = v.chave_ek
            LEFT JOIN dim_cr d ON (o.cr = d.CR_SAP OR o.cr = d.Cod_Cr OR o.cr2 = d.CR_SAP OR o.cr2 = d.Cod_Cr)
            WHERE 1=1
        """
        params = []
        
        if filtros.get('gerente'):
            query += " AND LOWER(TRIM(d.Gerente)) = LOWER(TRIM(?))"
            params.append(filtros['gerente'])
        if filtros.get('diretor'):
            query += " AND LOWER(TRIM(d.Diretor)) = LOWER(TRIM(?))"
            params.append(filtros['diretor'])
        if filtros.get('pais'):
            query += " AND LOWER(TRIM(d.Pais)) = LOWER(TRIM(?))"
            params.append(filtros['pais'])
        if filtros.get('cliente'):
            query += " AND LOWER(TRIM(d.Cliente)) = LOWER(TRIM(?))"
            params.append(filtros['cliente'])
        if filtros.get('pratica'):
            query += " AND LOWER(TRIM(o.pratica)) = LOWER(TRIM(?))"
            params.append(filtros['pratica'])
        if filtros.get('produto'):
            query += " AND LOWER(TRIM(o.produto)) = LOWER(TRIM(?))"
            params.append(filtros['produto'])
        if filtros.get('cr'):
            query += " AND (d.CR_SAP = ? OR d.Cod_Cr = ? OR o.cr = ? OR o.cr2 = ?)"
            params.append(filtros['cr'])
            params.append(filtros['cr'])
            params.append(filtros['cr'])
            params.append(filtros['cr'])
        if filtros.get('mes'):
            query += " AND v.mes_ref = ?"
            params.append(filtros['mes'])

        query += " GROUP BY o.id LIMIT 50 OFFSET ?"
        offset = (int(filtros.get('page', 1)) - 1) * 50
        params.append(offset)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_resumo(filtros):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        base_query = "FROM forecast_oportunidades o LEFT JOIN forecast_valores v ON o.chave_ek = v.chave_ek LEFT JOIN dim_cr d ON (o.cr = d.CR_SAP OR o.cr = d.Cod_Cr OR o.cr2 = d.CR_SAP OR o.cr2 = d.Cod_Cr) WHERE 1=1"
        params = []
        
        if filtros.get('gerente'):
            base_query += " AND LOWER(TRIM(d.Gerente)) = LOWER(TRIM(?))"
            params.append(filtros['gerente'])
        if filtros.get('diretor'):
            base_query += " AND LOWER(TRIM(d.Diretor)) = LOWER(TRIM(?))"
            params.append(filtros['diretor'])
        if filtros.get('pais'):
            base_query += " AND LOWER(TRIM(d.Pais)) = LOWER(TRIM(?))"
            params.append(filtros['pais'])
        if filtros.get('cliente'):
            base_query += " AND LOWER(TRIM(d.Cliente)) = LOWER(TRIM(?))"
            params.append(filtros['cliente'])
        if filtros.get('pratica'):
            base_query += " AND LOWER(TRIM(o.pratica)) = LOWER(TRIM(?))"
            params.append(filtros['pratica'])
        if filtros.get('produto'):
            base_query += " AND LOWER(TRIM(o.produto)) = LOWER(TRIM(?))"
            params.append(filtros['produto'])
        if filtros.get('cr'):
            base_query += " AND (d.CR_SAP = ? OR d.Cod_Cr = ? OR o.cr = ? OR o.cr2 = ?)"
            params.append(filtros['cr'])
            params.append(filtros['cr'])
            params.append(filtros['cr'])
            params.append(filtros['cr'])
        if filtros.get('mes'):
            base_query += " AND v.mes_ref = ?"
            params.append(filtros['mes'])
            
        cursor.execute(f"SELECT COUNT(DISTINCT o.id) as total_opp {base_query}", params)
        total_opp = dict(cursor.fetchone())['total_opp']
        
        cursor.execute(f"SELECT SUM(v.valor_rl) as rl_total, SUM(v.valor_rb) as rb_total {base_query}", params)
        resumo_valores = dict(cursor.fetchone())
        
        return {
            "total_opp": total_opp,
            "rl_total": resumo_valores['rl_total'] or 0,
            "rb_total": resumo_valores['rb_total'] or 0
        }


def get_resumo_por_cr(filtros):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        base_query = "FROM forecast_oportunidades o LEFT JOIN forecast_valores v ON o.chave_ek = v.chave_ek LEFT JOIN dim_cr d ON (o.cr = d.CR_SAP OR o.cr = d.Cod_Cr OR o.cr2 = d.CR_SAP OR o.cr2 = d.Cod_Cr) WHERE 1=1"
        params = []
        
        if filtros.get('gerente'):
            base_query += " AND LOWER(TRIM(d.Gerente)) = LOWER(TRIM(?))"
            params.append(filtros['gerente'])
        if filtros.get('diretor'):
            base_query += " AND LOWER(TRIM(d.Diretor)) = LOWER(TRIM(?))"
            params.append(filtros['diretor'])
        if filtros.get('pais'):
            base_query += " AND LOWER(TRIM(d.Pais)) = LOWER(TRIM(?))"
            params.append(filtros['pais'])
        if filtros.get('cliente'):
            base_query += " AND LOWER(TRIM(d.Cliente)) = LOWER(TRIM(?))"
            params.append(filtros['cliente'])
        if filtros.get('pratica'):
            base_query += " AND LOWER(TRIM(o.pratica)) = LOWER(TRIM(?))"
            params.append(filtros['pratica'])
        if filtros.get('produto'):
            base_query += " AND LOWER(TRIM(o.produto)) = LOWER(TRIM(?))"
            params.append(filtros['produto'])
        if filtros.get('cr'):
            base_query += " AND (d.CR_SAP = ? OR d.Cod_Cr = ? OR o.cr = ? OR o.cr2 = ?)"
            params.append(filtros['cr'])
            params.append(filtros['cr'])
            params.append(filtros['cr'])
            params.append(filtros['cr'])
        if filtros.get('mes'):
            base_query += " AND v.mes_ref = ?"
            params.append(filtros['mes'])

        query = f"SELECT COALESCE(d.Cod_Cr, o.cr, o.cr2) as cr, COALESCE(d.CR_SAP, o.cr, o.cr2) as cr_sap, COALESCE(d.Des_CR, o.cr, o.cr2) as des_cr, COUNT(DISTINCT o.id) as qtd_opp, SUM(CASE WHEN v.cenario='Forecast' THEN v.valor_rl ELSE 0 END) as total_rl, SUM(CASE WHEN v.cenario='Forecast' THEN v.valor_rb ELSE 0 END) as total_rb {base_query} GROUP BY COALESCE(d.Cod_Cr, o.cr, o.cr2), COALESCE(d.CR_SAP, o.cr, o.cr2), COALESCE(d.Des_CR, o.cr, o.cr2) ORDER BY total_rl DESC"
        cursor.execute(query, params)
        crs = [dict(row) for row in cursor.fetchall()]

        mes_filter = filtros.get('mes')

        # Busca orçado
        orcamento = {}
        q_orc = "SELECT cr, categoria_despesa, SUM(valor_plano) as val FROM orcamento_previa WHERE cr IS NOT NULL"
        p_orc = []
        if mes_filter:
            q_orc += " AND mes_ref = ?"
            p_orc.append(mes_filter)
        q_orc += " GROUP BY cr, categoria_despesa"
        
        for row in cursor.execute(q_orc, p_orc).fetchall():
            cr = row['cr']
            if cr not in orcamento:
                orcamento[cr] = {}
            if row['categoria_despesa'] not in orcamento[cr]:
                orcamento[cr][row['categoria_despesa']] = 0.0
            orcamento[cr][row['categoria_despesa']] += row['val']

        folha_previas = {}
        q_folha = "SELECT cr, SUM(valor) as val FROM previa_folha_th WHERE cr IS NOT NULL"
        p_folha = []
        if mes_filter:
            q_folha += " AND mes_ref = ?"
            p_folha.append(mes_filter)
        q_folha += " GROUP BY cr"

        for row in cursor.execute(q_folha, p_folha).fetchall():
            folha_previas[row['cr']] = row['val']

        ajustes = {}
        # Créditos (cr_credito)
        q_credito = (
            "SELECT COALESCE(d.Cod_Cr, a.cr_credito) as cr, a.resultado, SUM(a.incremento_credito) as val "
            "FROM ajustamentos_gerencia a "
            "LEFT JOIN dim_cr d ON d.CR_SAP = a.cr_credito OR d.Cod_Cr = a.cr_credito "
            "WHERE a.cr_credito IS NOT NULL"
        )
        p_credito = []
        if mes_filter:
            q_credito += " AND a.mes_ref = ?"
            p_credito.append(mes_filter)
        q_credito += " GROUP BY COALESCE(d.Cod_Cr, a.cr_credito), a.resultado"

        for row in cursor.execute(q_credito, p_credito).fetchall():
            cr = row['cr']
            if cr not in ajustes:
                ajustes[cr] = {}
            if row['resultado'] not in ajustes[cr]:
                ajustes[cr][row['resultado']] = 0.0
            ajustes[cr][row['resultado']] += row['val']

        # Débitos (cr_debito)
        q_debito = (
            "SELECT COALESCE(d.Cod_Cr, a.cr_debito) as cr, a.resultado, SUM(a.incremento_debito) as val "
            "FROM ajustamentos_gerencia a "
            "LEFT JOIN dim_cr d ON d.CR_SAP = a.cr_debito OR d.Cod_Cr = a.cr_debito "
            "WHERE a.cr_debito IS NOT NULL"
        )
        p_debito = []
        if mes_filter:
            q_debito += " AND a.mes_ref = ?"
            p_debito.append(mes_filter)
        q_debito += " GROUP BY COALESCE(d.Cod_Cr, a.cr_debito), a.resultado"

        for row in cursor.execute(q_debito, p_debito).fetchall():
            cr = row['cr']
            if cr not in ajustes:
                ajustes[cr] = {}
            if row['resultado'] not in ajustes[cr]:
                ajustes[cr][row['resultado']] = 0.0
            ajustes[cr][row['resultado']] += row['val']

        # Rateio automático
        q_rateio = (
            "SELECT COALESCE(d.Cod_Cr, r.cr) as cr, SUM(r.rateio) as val "
            "FROM rateio_automatico r "
            "LEFT JOIN dim_cr d ON d.CR_SAP = r.cr OR d.Cod_Cr = r.cr "
            "WHERE r.cr IS NOT NULL"
        )
        p_rateio = []
        if mes_filter:
            q_rateio += " AND r.mes_ref = ?"
            p_rateio.append(mes_filter)
        q_rateio += " GROUP BY COALESCE(d.Cod_Cr, r.cr)"

        for row in cursor.execute(q_rateio, p_rateio).fetchall():
            cr = row['cr']
            if cr not in ajustes:
                ajustes[cr] = {}
            ajustes[cr]['Rateio'] = ajustes[cr].get('Rateio', 0.0) + row['val']

        for cr in crs:
            cr_code = cr['cr']
            cr_sap = cr.get('cr_sap')
            cr['ajustes'] = []
            cr['previas'] = []
            if cr_code in ajustes:
                for grupo, valor in ajustes[cr_code].items():
                    if valor != 0:
                        cr['ajustes'].append({
                            "grupo": grupo,
                            "valor": valor
                        })
                        cr['previas'].append({
                            "categoria": grupo,
                            "valor": valor
                        })
            cr['orcamento'] = []
            if cr_code in orcamento:
                for categoria, valor in orcamento[cr_code].items():
                    if valor != 0:
                        cr['orcamento'].append({
                            "categoria": categoria,
                            "valor": valor
                        })
            cr['pessoal_previa'] = (
                folha_previas.get(cr_sap, 0.0) + folha_previas.get(cr_code, 0.0)
            )

        return crs


def get_lancamentos_por_cr_categoria(cr, categoria, mes_ref=None):
    slug_to_resultado = {
        'receita_bruta': 'Receita Bruta',
        'deducoes': 'Deduções',
        'receita_liquida': 'Receita Líquida',
        'pessoal': 'Pessoal',
        'aluguéis': 'Aluguéis',
        'despesas_gerais': 'Despesas Gerais',
        'frota': 'Frota',
        'impostos_taxas_multas': 'Impostos, Taxas e Multas',
        'manutencao_operacao': 'Manutenção da Operação',
        'manutencao_maquinas': 'Manutenção de Máquinas',
        'manutencao_predial': 'Manutenção Predial',
        'marketing': 'Marketing',
        'outros': 'Outros',
        'pontuais': 'Pontuais',
        'seguros': 'Seguros',
        'servicos_de_terceiros': 'Serviços de Terceiros',
        'telecomunicacoes': 'Telecomunicações',
        'ti': 'TI',
        'treinamentos': 'Treinamentos',
        'utilidades': 'Utilidades',
        'viagens': 'Viagens',
        'rateio': 'Rateio',
        'recuperacao_outros_gastos': 'Recuperação Outros Gastos',
        'recuperacao_pessoal': 'Recuperação Pessoal'
    }

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if categoria == 'Pessoal' or categoria == 'pessoal':
            code_set = {cr}
            cursor.execute("SELECT CR_SAP, Cod_Cr FROM dim_cr WHERE CR_SAP = ? OR Cod_Cr = ?", (cr, cr))
            for row in cursor.fetchall():
                if row['CR_SAP']:
                    code_set.add(row['CR_SAP'])
                if row['Cod_Cr']:
                    code_set.add(row['Cod_Cr'])

            placeholders = ','.join(['?'] * len(code_set))
            query = f"SELECT cliente as descricao, fonte as origem, valor, cr FROM previa_folha_th WHERE cr IN ({placeholders})"
            params = list(code_set)
            if mes_ref:
                query += " AND mes_ref = ?"
                params.append(mes_ref)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        resultado = slug_to_resultado.get(categoria, categoria)

        code_set = {cr}
        cursor.execute("SELECT CR_SAP, Cod_Cr FROM dim_cr WHERE CR_SAP = ? OR Cod_Cr = ?", (cr, cr))
        for row in cursor.fetchall():
            if row['CR_SAP']:
                code_set.add(row['CR_SAP'])
            if row['Cod_Cr']:
                code_set.add(row['Cod_Cr'])

        code_values = list(code_set)
        placeholders = ','.join(['?'] * len(code_values))
        query = (
            f"SELECT * FROM ajustamentos_gerencia "
            f"WHERE LOWER(TRIM(resultado)) = LOWER(TRIM(?)) "
            f"AND (cr_credito IN ({placeholders}) OR cr_debito IN ({placeholders}) "
            f"OR cr_envio IN ({placeholders}) OR cr_destino IN ({placeholders}))"
        )
        params = [resultado] + code_values * 4
        if mes_ref:
            query += " AND mes_ref = ?"
            params.append(mes_ref)

        rows = cursor.execute(query, params).fetchall()
        results = []
        for row in rows:
            valor = 0.0
            if row['cr_credito'] in code_set:
                valor = abs(row['incremento_credito'] or 0)
            elif row['cr_debito'] in code_set:
                valor = -abs(row['incremento_debito'] or 0)
            elif row['cr_envio'] in code_set:
                valor = abs(row['incremento_credito'] or 0)
            elif row['cr_destino'] in code_set:
                valor = -abs(row['incremento_debito'] or 0)
            else:
                valor = abs(row['incremento_credito'] or row['incremento_debito'] or 0)

            origem = row['desc_cr_envio'] or row['desc_cr_destino'] or row['resultado']
            results.append({
                'descricao': row['justificativa'] or row['resultado'],
                'origem': origem,
                'descricao_cr_envio': row['desc_cr_envio'],
                'responsavel_cr_envio': row['gestor_cr_envio'],
                'aba_origem': row['aba_origem'],
                'valor': valor
            })

        if resultado.lower() == 'rateio':
            placeholders = ','.join(['?'] * len(code_values))
            query_rateio = (
                f"SELECT cr, rateio, cr_envio, desc_cr_envio, gestor_cr_envio, cliente, rl_rateio, descricao, aba_origem "
                f"FROM rateio_automatico WHERE cr IN ({placeholders})"
            )
            params_rateio = code_values[:]
            if mes_ref:
                query_rateio += " AND mes_ref = ?"
                params_rateio.append(mes_ref)
            rateio_rows = cursor.execute(query_rateio, params_rateio).fetchall()
            for row in rateio_rows:
                descricao = row['descricao'] or row['cliente'] or 'Rateio'
                origem = row['desc_cr_envio'] or row['descricao']
                results.append({
                    'descricao': descricao,
                    'origem': origem,
                    'descricao_cr_envio': row['desc_cr_envio'],
                    'responsavel_cr_envio': row['gestor_cr_envio'],
                    'aba_origem': row['aba_origem'],
                    'valor': row['rateio'] or 0
                })

        return results
