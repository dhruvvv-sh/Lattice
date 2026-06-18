from fastapi import APIRouter
from app.database import SessionLocal
from app.models import Bucket
from app.schemas import BucketCreate
from app.models import Object

router = APIRouter(prefix="/buckets",tags=["Buckets"])
@router.post("/")
def create_bucket(bucket: BucketCreate):
    db = SessionLocal()
    new_bucket = Bucket(name = bucket.name)
    db.add(new_bucket)
    db.commit()
    db.refresh(new_bucket)
    db.close()
    return new_bucket

#returning all the buckets
@router.get("/")
def list_buckets():
    db = SessionLocal()
    buckets = db.query(Bucket).all()
    db.close()
    return buckets

#querying bucket id
@router.get("/{bucket_id}")
def get_bucket(bucket_id:int):
    db = SessionLocal()
    bucket = db.query(Bucket).filter(Bucket.id==bucket_id).first()
    db.close()
    return bucket

#delete selective bucket id
@router.delete("/{bucket_id}")
def del_bucketid(bucket_id:int):
    db = SessionLocal()
    bucket = db.query(Bucket).filter(Bucket.id==bucket_id).first()
    if bucket is None:
        db.close()
        return {
            "message":"Bucket not found"
        }
    bucket_name = bucket.name
    db.delete(bucket)
    db.commit()
    db.close()
    return{
        "message":f"bucket {bucket_name} is deleted"
    }

#edit buckets
@router.put("/{bucket_id}")
def put_bucketid(bucket_id: int, bucket_update: BucketCreate):
    db = SessionLocal()
    # Find the bucket
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if bucket is None:
        db.close()
        return {
            "message": "Bucket not found"
        }
    # Update name
    bucket.name = bucket_update.name
    db.commit()
    db.refresh(bucket)
    db.close()
    return bucket

#returning the object

@router.get("/{bucket_id}/objects")
def list_bucket_objects(bucket_id: int):
    db = SessionLocal()

    objects = db.query(Object).filter(
        Object.bucket_id == bucket_id
    ).all()

    db.close()

    return objects