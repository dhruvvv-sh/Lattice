from fastapi import APIRouter

from app.storage.heartbeat import scan_disks

router = APIRouter()

@router.get("/cluster/health")
def cluster_heatlh():
    return scan_disks()