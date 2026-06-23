# app/storage_engine/disk_selector.py

DISKS = [
    "storage/disk1",
    "storage/disk2",
    "storage/disk3",
    "storage/disk4",
    "storage/disk5",
    "storage/disk6",
]

from datetime import datetime

from app.storage.disk_manager import DISKS
from app.storage.health_check import check_disk_health
from app.storage.cluster_state import disk_status

def scan_disks():
    for disk in DISKS:
        healthy = check_disk_health(disk)
        disk_status[disk] ={
            "status":"healthy" if healthy else "dead",
            "last_seen" : datetime.utcnow().isoformat()
        }
    return disk_status