from fastapi import APIRouter, UploadFile, File, HTTPException
from app.database import SessionLocal
from app.models import Object, Bucket
from app.storage_engine.writer import save_file
from app.storage_engine.checksum import calculate_checksum
from app.storage_engine.reader import read_file
import os

router = APIRouter(
    prefix="/objects",
    tags=["Objects"]
)


@router.get("/")
def list_objects():
    db = SessionLocal()
    objects = db.query(Object).all()
    db.close()
    return objects


@router.post("/upload/{bucket_id}")
def upload(
    bucket_id: int,
    file: UploadFile = File(...)
):

    db = SessionLocal()
    path = None

    try:
        bucket = db.query(Bucket).filter(
            Bucket.id == bucket_id
        ).first()

        if bucket is None:
            raise HTTPException(
                status_code=404,
                detail="Bucket not found"
            )

        # save_file now returns both path and disk
        path, disk = save_file(bucket_id, file)

        checksum = calculate_checksum(path)
        size = os.path.getsize(path)

        obj = Object(
            bucket_id=bucket_id,
            object_name=file.filename,
            file_path=path,
            disk_name=disk,      # <-- present for the disk selection function 
            checksum=checksum,
            size=size
        )

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return {
            "object_id": obj.id,
            "filename": obj.object_name,
            "disk": obj.disk_name,
            "checksum": obj.checksum,
            "size": obj.size
        }

    except Exception as e:
        db.rollback()

        if path and os.path.exists(path):
            os.remove(path)

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

    obj = db.query(Object).filter(
        Object.id == object_id
    ).first()

    if obj is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Object not found"
        )

    if not os.path.exists(obj.file_path):
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Object not found"
        )

    path = obj.file_path

    db.close()

    return read_file(path)


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

        if os.path.exists(obj.file_path):
            os.remove(obj.file_path)

        db.delete(obj)
        db.commit()

        return {
            "message": "Object deleted successfully",
            "object_id": object_id,
            "filename": obj.object_name
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
