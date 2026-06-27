from pathlib import Path

from app.models import ObjectShard
from app.storage.disk_manager import DISKS
from app.storage.erasure import DATA_SHARDS, PARITY_SHARDS, generate_parity, recover_shards
from app.storage.shard_manager import reconstruct_bytes, split_bytes


TOTAL_SHARDS = DATA_SHARDS + PARITY_SHARDS


def _safe_filename(filename: str) -> str:
    return Path(filename).name


def _shard_base_name(object_id: int, filename: str) -> str:
    return f"object_{object_id}_{_safe_filename(filename)}"


def _write_shard_file(object_id: int, filename: str, shard_index: int, data: bytes) -> str:
    disk = DISKS[shard_index]
    disk.mkdir(parents=True, exist_ok=True)

    shard_path = disk / f"{_shard_base_name(object_id, filename)}.part{shard_index}"

    with open(shard_path, "wb") as shard_file:
        shard_file.write(data)

    return str(shard_path)


def save_object_shards(db, obj, data: bytes):
    data_shards = split_bytes(data, DATA_SHARDS)
    parity_shards = generate_parity(data_shards)
    all_shards = [*data_shards, *parity_shards]

    written_paths = []

    try:
        for shard_index, shard_data in enumerate(all_shards):
            shard_path = _write_shard_file(
                object_id=obj.id,
                filename=obj.object_name,
                shard_index=shard_index,
                data=shard_data,
            )
            written_paths.append(shard_path)

            db.add(
                ObjectShard(
                    object_id=obj.id,
                    shard_index=shard_index,
                    disk_name=DISKS[shard_index].name,
                    shard_path=shard_path,
                    is_parity=shard_index >= DATA_SHARDS,
                    shard_size=len(shard_data),
                )
            )
    except Exception:
        cleanup_paths(written_paths)
        raise

    return written_paths


def cleanup_paths(paths):
    for path in paths:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass


def load_object_bytes(obj):
    data_shards = [None] * DATA_SHARDS
    parity_shards = [None] * PARITY_SHARDS

    for shard in obj.shards:
        shard_path = Path(shard.shard_path)
        if not shard_path.exists():
            continue

        shard_data = shard_path.read_bytes()

        if shard.is_parity:
            parity_index = shard.shard_index - DATA_SHARDS
            if 0 <= parity_index < PARITY_SHARDS:
                parity_shards[parity_index] = shard_data
        elif 0 <= shard.shard_index < DATA_SHARDS:
            data_shards[shard.shard_index] = shard_data

    missing_count = sum(shard is None for shard in [*data_shards, *parity_shards])

    if missing_count > PARITY_SHARDS:
        raise ValueError("Too many missing shards to recover object")

    if any(shard is None for shard in data_shards):
        data_shards, _ = recover_shards(data_shards, parity_shards)

    return reconstruct_bytes(data_shards, original_size=obj.size)
