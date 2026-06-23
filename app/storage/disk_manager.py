# app/storage/disk_manager.py

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DISKS = [
    PROJECT_ROOT / "storage" / "disk1",
    PROJECT_ROOT / "storage" / "disk2",
    PROJECT_ROOT / "storage" / "disk3",
    PROJECT_ROOT / "storage" / "disk4",
    PROJECT_ROOT / "storage" / "disk5",
    PROJECT_ROOT / "storage" / "disk6",
]

def write_shard(filename, shard_index, data):
    disk = DISKS[shard_index]

    shard_path = disk / f"{filename}.part{shard_index}"

    print("Writing to:", shard_path)

    shard_path.parent.mkdir(parents=True, exist_ok=True)

    with open(shard_path, "wb") as f:
        f.write(data)

    return str(shard_path)

def read_shard(filename, shard_index):
    disk = DISKS[shard_index]

    shard_path = disk / f"{filename}.part{shard_index}"

    with open(shard_path, "rb") as f:
        return f.read()

def shard_exists(filename: str, shard_index: int):
    """
    Check if a shard exists.
    """

    disk = DISKS[shard_index]

    shard_path = Path(disk) / f"{filename}.part{shard_index}"

    return shard_path.exists()