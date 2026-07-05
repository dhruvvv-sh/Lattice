# app/storage/disk_manager.py

import os
from pathlib import Path

from app.storage.cluster_state import DEFAULT_CLUSTER_TOPOLOGY, LEGACY_STORAGE_ROOT

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LEGACY_DISKS = [
    LEGACY_STORAGE_ROOT / "disk1",
    LEGACY_STORAGE_ROOT / "disk2",
    LEGACY_STORAGE_ROOT / "disk3",
    LEGACY_STORAGE_ROOT / "disk4",
    LEGACY_STORAGE_ROOT / "disk5",
    LEGACY_STORAGE_ROOT / "disk6",
    LEGACY_STORAGE_ROOT / "disk7",
    LEGACY_STORAGE_ROOT / "disk8",
    LEGACY_STORAGE_ROOT / "disk9",
    LEGACY_STORAGE_ROOT / "disk10",
    LEGACY_STORAGE_ROOT / "disk11",
    LEGACY_STORAGE_ROOT / "disk12",
    LEGACY_STORAGE_ROOT / "disk13",
    LEGACY_STORAGE_ROOT / "disk14",
    LEGACY_STORAGE_ROOT / "disk15",
    LEGACY_STORAGE_ROOT / "disk16",
]

DISKS = [
    disk
    for disks in DEFAULT_CLUSTER_TOPOLOGY.values()
    for disk in disks
]

def write_shard(filename, shard_index, data):
    disk = LEGACY_DISKS[shard_index]

    shard_path = disk / f"{filename}.part{shard_index}"

    print("Writing to:", shard_path)

    shard_path.parent.mkdir(parents=True, exist_ok=True)

    with open(shard_path, "wb") as f:
        f.write(data)

    return str(shard_path)

def read_shard(filename, shard_index):
    disk = LEGACY_DISKS[shard_index]

    shard_path = disk / f"{filename}.part{shard_index}"

    with open(shard_path, "rb") as f:
        return f.read()

def shard_exists(filename: str, shard_index: int):
    """
    Check if a shard exists.
    """

    disk = LEGACY_DISKS[shard_index]

    shard_path = Path(disk) / f"{filename}.part{shard_index}"

    return shard_path.exists()
