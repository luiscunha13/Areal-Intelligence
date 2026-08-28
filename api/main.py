"""
api/main.py
────────────
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import macro, sectors, etfs, stocks

app = FastAPI(
    title="Areal Intelligence API",
    description="Automated financial intelligence platform — macro, sectors, ETFs, stocks",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(macro.router,   prefix="/api/macro",   tags=["Macro"])
app.include_router(sectors.router, prefix="/api/sectors", tags=["Sectors"])
app.include_router(etfs.router,    prefix="/api/etfs",    tags=["ETFs"])
app.include_router(stocks.router,  prefix="/api/stocks",  tags=["Stocks"])


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
