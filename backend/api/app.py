from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import filtros, forecast, cr, upload, auth

app = FastAPI(title="Forecast App API")

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

app.include_router(filtros.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(cr.router, prefix="/api")
app.include_router(upload.router)
app.include_router(auth.router, prefix="/api")
