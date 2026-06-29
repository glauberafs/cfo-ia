"""CFO IA - API (FastAPI, multiusuario)."""
from fastapi import FastAPI

from .routers import (
    alertas, anomalias, aposentadoria, auth, contas, dashboard, dre, eventos, forecast, investimentos,
    orcamentos, patrimonio, score, sync,
)

app = FastAPI(title="CFO IA API", version="0.8.0")

# Esquema do banco e gerenciado por migracoes Alembic (ver apps/api/alembic/).
# Rode `alembic upgrade head` antes de subir a API.

app.include_router(auth.router)
app.include_router(contas.router)
app.include_router(sync.router)
app.include_router(eventos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)
app.include_router(forecast.router)
app.include_router(aposentadoria.router)
app.include_router(dre.router)
app.include_router(alertas.router)
app.include_router(patrimonio.router)
app.include_router(anomalias.router)
app.include_router(score.router)
app.include_router(investimentos.router)


@app.get("/health")
def health():
    return {"status": "ok"}
