from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Response

from app.database import SessionLocal
from app.models import Object, Bucket
from app.storage_engine.checksum import calculate_checksum_bytes
from app.storage_engine.sharded import (
    cleanup_paths,
    load_object_bytes,
    save_object_shards,
)

router = APIRouter(
    prefix="/objects",
    tags=["Objects"]
)


@router.get("/")
def list_objects():
    db = SessionLocal()
    try:
        return db.query(Object).all()
    finally:
        db.close()


@router.post("/upload/{bucket_id}")
def upload(
    bucket_id: int,
    file: UploadFile = File(...)
):
    db = SessionLocal()
    written_paths = []

    try:
        bucket = db.query(Bucket).filter(
            Bucket.id == bucket_id
        ).first()

        if bucket is None:
            raise HTTPException(
                status_code=404,
                detail="Bucket not found"
            )

        data = file.file.read()
        filename = Path(file.filename).name
        checksum = calculate_checksum_bytes(data)

        obj = Object(
            bucket_id=bucket_id,
            object_name=filename,
            file_path=f"sharded://bucket_{bucket_id}/{filename}",
            disk_name="erasure-4+2",
            checksum=checksum,
            size=len(data),
            content_type=file.content_type,
        )

        db.add(obj)
        db.flush()

        written_paths = save_object_shards(db, obj, data)

        db.commit()
        db.refresh(obj)

        return {
            "object_id": obj.id,
            "filename": obj.object_name,
            "storage": obj.disk_name,
            "shards": len(obj.shards),
            "checksum": obj.checksum,
            "size": obj.size,
        }

    except HTTPException:
        db.rollback()
        cleanup_paths(written_paths)
        raise

    except Exception as e:
        db.rollback()
        cleanup_paths(written_paths)

        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

    finally:
        db.close()


@router.get("/{object_id}")
def download(object_id: int):
    db = SessionLocal()

    try:
        obj = db.query(Object).filter(
            Object.id == object_id
        ).first()

        if obj is None:
            raise HTTPException(
                status_code=404,
                detail="Object not found"
            )

        if not obj.shards:
            raise HTTPException(
                status_code=500,
                detail="Object has no shard metadata."
            )

        data = load_object_bytes(obj)

        return Response(
            content=data,
            media_type=obj.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{obj.object_name}"'
            },
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    finally:
        db.close()


@router.delete("/{object_id}")
def delete_obj(object_id: int):
    db = SessionLocal()

    try:
        obj = db.query(Object).filter(
            Object.id == object_id
        ).first()

        if obj is None:
            raise HTTPException(
                status_code=404,
                detail="Object not found"
            )

        filename = obj.object_name
        shard_paths = [shard.shard_path for shard in obj.shards]

        cleanup_paths(shard_paths)

        db.delete(obj)
        db.commit()

        return {
            "message": "Object deleted successfully",
            "object_id": object_id,
            "filename": filename,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()