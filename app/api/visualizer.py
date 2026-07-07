import hashlib
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.database import SessionLocal
from app.models import Bucket, Object, ObjectShard
from app.storage.cluster_state import DEFAULT_CLUSTER_TOPOLOGY
from app.storage.disk_manager import PROJECT_ROOT
from app.storage_engine.checksum import calculate_checksum_bytes
from app.storage_engine.nodes import build_local_node_registry
from app.storage_engine.sharded import (
    cleanup_paths,
    load_object_bytes,
    save_object_shards,
)
router = APIRouter(tags=["Visualizer"])

VISUALIZER_DIR = PROJECT_ROOT / "app" / "static" / "visualizer"
DEMO_BUCKET_NAME = "visualizer-demo"
DEMO_NODE_DISKS = DEFAULT_CLUSTER_TOPOLOGY

node_status = {
    node_id: {
        "status": "healthy",
        "last_seen": None,
    }
    for node_id in DEMO_NODE_DISKS
}
last_metrics = {
    "upload_ms": None,
    "download_ms": None,
    "recovery_ms": None,
    "last_event": "ready",
}


def _demo_registry():
    return build_local_node_registry(DEMO_NODE_DISKS)


def _healthy_cluster_manager():
    manager = _demo_registry().build_cluster_manager()

    for node_id, status in node_status.items():
        if status["status"] != "healthy":
            manager.mark_node(node_id, online=False, healthy=False)

    return manager


def _ensure_demo_bucket(db):
    bucket = db.query(Bucket).filter(Bucket.name == DEMO_BUCKET_NAME).first()

    if bucket is not None:
        return bucket

    bucket = Bucket(name=DEMO_BUCKET_NAME)
    db.add(bucket)
    db.flush()
    return bucket


def _now_ms() -> float:
    return time.perf_counter() * 1000


def _elapsed_ms(start_ms: float) -> float:
    return round(_now_ms() - start_ms, 2)


def _shard_state(shard: ObjectShard):
    exists = Path(shard.shard_path).exists()

    return {
        "shard_index": shard.shard_index,
        "node_id": shard.node_id,
        "disk_id": shard.disk_id or shard.disk_name,
        "path": shard.shard_path,
        "type": "parity" if shard.is_parity else "data",
        "exists": exists,
        "size": shard.shard_size,
        "checksum": shard.shard_checksum,
    }


def _object_state(obj: Object):
    shards = sorted(obj.shards, key=lambda shard: shard.shard_index)
    missing = [
        shard.shard_index
        for shard in shards
        if not Path(shard.shard_path).exists()
    ]

    return {
        "id": obj.id,
        "name": obj.object_name,
        "size": obj.size,
        "checksum": obj.checksum,
        "missing_shards": missing,
        "recoverable": len(missing) <= 2,
        "shards": [_shard_state(shard) for shard in shards],
    }


def _state_payload(db):
    objects = (
        db.query(Object)
        .join(Bucket)
        .filter(Bucket.name == DEMO_BUCKET_NAME)
        .order_by(Object.id.desc())
        .all()
    )

    return {
        "nodes": [
            {
                "node_id": node_id,
                "status": node_status[node_id]["status"],
                "last_seen": node_status[node_id]["last_seen"],
                "disks": [
                    {
                        "disk_id": disk.name,
                        "path": str(disk),
                        "exists": disk.exists(),
                    }
                    for disk in disks
                ],
            }
            for node_id, disks in DEMO_NODE_DISKS.items()
        ],
        "objects": [_object_state(obj) for obj in objects],
        "metrics": last_metrics,
    }


@router.get("/visualizer", include_in_schema=False)
def visualizer_page():
    return FileResponse(VISUALIZER_DIR / "index.html")


@router.get("/api/visualizer/state")
def visualizer_state():
    db = SessionLocal()

    try:
        return _state_payload(db)
    finally:
        db.close()


@router.post("/api/visualizer/upload")
def visualizer_upload(file: UploadFile = File(...)):
    db = SessionLocal()
    written_paths = []
    start_ms = _now_ms()

    try:
        bucket = _ensure_demo_bucket(db)
        data = file.file.read()
        checksum = calculate_checksum_bytes(data)
        filename = Path(file.filename).name

        obj = Object(
            bucket_id=bucket.id,
            object_name=filename,
            file_path=f"sharded://{DEMO_BUCKET_NAME}/{filename}",
            disk_name="erasure-4+2",
            checksum=checksum,
            size=len(data),
            content_type=file.content_type,
        )

        db.add(obj)
        db.flush()

        written_paths = save_object_shards(
            db,
            obj,
            data,
            cluster_manager=_healthy_cluster_manager(),
            node_registry=_demo_registry(),
        )

        db.commit()
        db.refresh(obj)

        last_metrics["upload_ms"] = _elapsed_ms(start_ms)
        last_metrics["last_event"] = f"uploaded {filename}"

        return {
            "object": _object_state(obj),
            "metrics": last_metrics,
        }
    except Exception as exc:
        db.rollback()
        cleanup_paths(written_paths)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        db.close()


@router.get("/api/visualizer/recover/{object_id}")
def visualizer_recover(object_id: int):
    db = SessionLocal()
    start_ms = _now_ms()

    try:
        obj = db.query(Object).filter(Object.id == object_id).first()

        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")

        data = load_object_bytes(obj, node_registry=_demo_registry())
        recovered_checksum = hashlib.sha256(data).hexdigest()
        recovered = recovered_checksum == obj.checksum

        last_metrics["recovery_ms"] = _elapsed_ms(start_ms)
        last_metrics["download_ms"] = last_metrics["recovery_ms"]
        last_metrics["last_event"] = "recovery succeeded" if recovered else "recovery failed"

        return {
            "object": _object_state(obj),
            "recovered": recovered,
            "checksum": recovered_checksum,
            "metrics": last_metrics,
        }
    except ValueError as exc:
        last_metrics["recovery_ms"] = _elapsed_ms(start_ms)
        last_metrics["download_ms"] = last_metrics["recovery_ms"]
        last_metrics["last_event"] = "recovery failed"
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        db.close()


@router.post("/api/visualizer/nodes/{node_id}/delete")
def visualizer_delete_node(node_id: str):
    if node_id not in DEMO_NODE_DISKS:
        raise HTTPException(status_code=404, detail="Node not found")

    db = SessionLocal()

    try:
        shards = db.query(ObjectShard).filter(ObjectShard.node_id == node_id).all()
        cleanup_paths([shard.shard_path for shard in shards])
        node_status[node_id]["status"] = "dead"
        node_status[node_id]["last_seen"] = None
        last_metrics["last_event"] = f"{node_id} deleted"
        return _state_payload(db)
    finally:
        db.close()


@router.post("/api/visualizer/nodes/reset")
def visualizer_reset_nodes():
    for node_id in node_status:
        node_status[node_id]["status"] = "healthy"
        node_status[node_id]["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    last_metrics["last_event"] = "nodes reset"

    db = SessionLocal()

    try:
        return _state_payload(db)
    finally:
        db.close()


@router.delete("/api/visualizer/objects/{object_id}")
def visualizer_delete_object(object_id: int):
    db = SessionLocal()

    try:
        obj = db.query(Object).filter(Object.id == object_id).first()

        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")

        cleanup_paths([shard.shard_path for shard in obj.shards])
        db.delete(obj)
        db.commit()
        last_metrics["last_event"] = f"object {object_id} deleted"
        return {"deleted": object_id}
    finally:
        db.close()
