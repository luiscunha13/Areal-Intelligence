"""
api/main.py
────────────
FastAPI application entry point.
"""
from typing import Optional
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

# ─── Legacy Backward-Compatibility Router Aliases ───────────────────────────
from fastapi import Query, Depends
from sqlalchemy.orm import Session
from api.database import get_db

@app.get("/api/regime/current", tags=["Legacy"])
def legacy_current_regime(db: Session = Depends(get_db)):
    return macro.get_current_regime(db=db)

@app.get("/api/regime/history", tags=["Legacy"])
def legacy_regime_history(limit: int = Query(60, le=2000), db: Session = Depends(get_db)):
    return macro.get_regime(limit=limit, db=db)

@app.get("/api/companies/rankings", tags=["Legacy"])
@app.get("/api/entry/ranking", tags=["Legacy"])
@app.get("/api/candidates", tags=["Legacy"])
def legacy_stock_rankings(
    search: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    limit: int = Query(2000, le=2000),
    db: Session = Depends(get_db)
):
    return stocks.screener(sector=sector, limit=limit, db=db)

@app.get("/api/companies/{ticker}", tags=["Legacy"])
@app.get("/api/entry/company/{ticker}", tags=["Legacy"])
def legacy_company_detail(ticker: str, db: Session = Depends(get_db)):
    return stocks.get_stock_detail(ticker=ticker, db=db)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

