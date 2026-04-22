from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import products, opportunities, scan, billing
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="CAST API", version="0.1.0", lifespan=lifespan)

app.include_router(products.router)
app.include_router(opportunities.router)
app.include_router(scan.router)
app.include_router(billing.router)


@app.get("/health")
def health():
    return {"status": "ok"}
