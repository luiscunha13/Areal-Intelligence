import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import macro, regime, sectors, companies, candidates, entry

logger = logging.getLogger(__name__)

async def run_autonomous_sync_in_background():
    try:
        import subprocess
        logger.info("Triggering autonomous universe SEC EDGAR background sync...")
        subprocess.Popen(["python3", "scripts/sync_autonomous_universe.py"])
    except Exception as e:
        logger.error(f"Background universe sync failed: {e}")

app = FastAPI(
    title="Areal Intelligence - Quantitative Investment Engine",
    description="Institutional-grade Macro, Sector, Stock & Entry Timing Intelligence Platform",
    version="4.0.0",
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_autonomous_sync_in_background())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(macro.router, prefix="/api/macro")
app.include_router(regime.router, prefix="/api/regime")
app.include_router(sectors.router)
app.include_router(companies.router)
app.include_router(candidates.router)
app.include_router(entry.router)

@app.get("/health")
def health():
    return {"status": "ok", "phase": "Phase 4 Autonomous Engine Active", "total_equities": "10,398+"}
