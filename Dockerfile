# Use a imagem base do Python
FROM python:3.12-slim AS backend

WORKDIR /app

# Criação da pasta de data
RUN mkdir -p /app/data

# Instala dependências do backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do backend e scripts ETL
COPY backend/ ./backend/
COPY etl_forecast.py init_db.py ./

# Variáveis default
ENV DB_PATH=/app/data/previadb.db
ENV XLSX_PATH=/app/data/Forecast\ Semanal\ 2026\ -\ Abril.xlsx

EXPOSE 8000

# Executa uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
