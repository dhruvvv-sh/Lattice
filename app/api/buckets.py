from fastapi import APIRouter
from app.database import SessionLocal
from app.models import Bucket
router = APIRouter(prefix="/buckets",tags=["Buckets"])
@router.post("/{name}")
def create_bucket(name: str):
    db = SessionLocal()
    bucket = Bucket(name = name)
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    db.close()
    return bucket

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
def put_bucketid(bucket_id: int, bucket_name: str):
    db = SessionLocal()
    # Find the bucket
    bucket = db.query(Bucket).filter(Bucket.id == bucket_id).first()
    if bucket is None:
        db.close()
        return {
            "message": "Bucket not found"
        }
    bucket.name = bucket_name
    db.commit()
    db.refresh(bucket)
    db.close()
    return {
        "message": f"Name successfully changed to {bucket_name}"
    }
