from app.database import SessionLocal
from app.models import Object

DISKS = ["disk1", "disk2", "disk3"]


def get_next_disk():

    db = SessionLocal()

    try:
        object_count = db.query(Object).count()

        disk = DISKS[object_count % len(DISKS)]

        return disk

    finally:
        db.close()