from fastapi import FastAPI

from app.api import buckets, cluster, objects
from app.database import Base, engine

app = FastAPI(title="Lattice", version="0.1.0")

Base.metadata.create_all(bind=engine)


app.include_router(buckets.router)
app.include_router(objects.router)
app.include_router(cluster.router)

@app.get("/health")
def health():
    return {"status": "OK"}
