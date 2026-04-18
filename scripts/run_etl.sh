#!/bin/bash
set -e

echo "Executando ETLs em sequência..."
python backend/etl/etl_dim_cr.py
python backend/etl/etl_forecast.py
python backend/etl/etl_gerencias.py
python backend/etl/etl_orcado_previa.py
python backend/etl/etl_previa_folha.py

echo "ETLs concluídos."
