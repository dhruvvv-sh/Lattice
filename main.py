from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import buckets, cluster, objects, visualizer
from app.database import Base, engine, ensure_runtime_schema

app = FastAPI(title="Lattice", version="0.1.0")

Base.metadata.create_all(bind=engine)
ensure_runtime_schema()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(buckets.router)
app.include_router(objects.router)
app.include_router(cluster.router)
app.include_router(visualizer.router)

@app.get("/health")
def health():
    return {"status": "OK"}
