from fastapi import APIRouter,UploadFile, File, HTTPException
from app.database import SessionLocal
from app.models import Object
from app.models import Bucket
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
    bucket = db.query(Bucket).filter(
        Bucket.id == bucket_id
    ).first()

    if bucket is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Bucket not found"
        )
    path = save_file(bucket_id, file)

    checksum = calculate_checksum(path)

    size = os.path.getsize(path)

    obj = Object(
        bucket_id=bucket_id,
        object_name=file.filename,
        file_path=path,
        checksum=checksum,
        size=size
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)
    response = {
    "object_id": obj.id,
    "filename": obj.object_name,
    "checksum": obj.checksum,
    "size": obj.size
    }  
    db.close()
    return response



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