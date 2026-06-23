# app/storage/disk_manager.py

from pathlib import Path

DISKS = [
    "storage/disk1",
    "storage/disk2",
    "storage/disk3",
    "storage/disk4",
    "storage/disk5",
    "storage/disk6",
]


def write_shard(filename, shard_index, data):
    disk = DISKS[shard_index]

    shard_path = Path(disk) / f"{filename}.part{shard_index}"

    print("Writing to:", shard_path)

    shard_path.parent.mkdir(parents=True, exist_ok=True)

    with open(shard_path, "wb") as f:
        f.write(data)

    return str(shard_path)

def read_shard(filename, shard_index):
    disk = DISKS[shard_index]

    shard_path = Path(disk) / f"{filename}.part{shard_index}"

    print("Trying to read:", shard_path.resolve())

    with open(shard_path, "rb") as f:
        return f.read()

def shard_exists(filename: str, shard_index: int):
    """
    Check if a shard exists.
    """

    disk = DISKS[shard_index]

    shard_path = Path(disk) / f"{filename}.part{shard_index}"

    return shard_path.exists()