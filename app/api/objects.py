from fastapi import APIRouter
from app.database import SessionLocal
from app.models import Object
from app.schemas import ObjectCreate

router = APIRouter(
    prefix="/objects",
    tags=["Objects"]
)

@router.post("/")
def create_object(obj: ObjectCreate):
    db = SessionLocal()
    new_object = Object(
        name = obj.name,
        bucket_id = obj.bucket_id
    )
    db.add(new_object)
    db.commit()
    db.refresh(new_object)
    db.close()
    return new_object

@router.get("/")
def list_objects():
    db = SessionLocal()
    objects = db.query(Object).all()
    db.close()
    return objects

