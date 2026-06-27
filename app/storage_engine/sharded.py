import hashlib
from pathlib import Path

from app.cluster_manager import ClusterManager, build_local_cluster_manager
from app.models import ObjectPlacementManifest, ObjectShard
from app.storage.disk_manager import DISKS
from app.storage.erasure import DATA_SHARDS, PARITY_SHARDS, generate_parity, recover_shards
from app.storage.shard_manager import reconstruct_bytes, split_bytes
from app.storage_engine.placement import (
    PlacementDecision,
    PlacementRequest,
    PlacementStrategy,
    load_strategy,
)


TOTAL_SHARDS = DATA_SHARDS + PARITY_SHARDS


def _safe_filename(filename: str) -> str:
    return Path(filename).name


def _shard_base_name(object_id: int, filename: str) -> str:
    return f"object_{object_id}_{_safe_filename(filename)}"


def _write_shard_file(
    object_id: int,
    filename: str,
    shard_index: int,
    disk: Path,
    data: bytes,
) -> str:
    disk.mkdir(parents=True, exist_ok=True)

    shard_path = disk / f"{_shard_base_name(object_id, filename)}.part{shard_index}"

    with open(shard_path, "wb") as shard_file:
        shard_file.write(data)

    return str(shard_path)


def _normalize_decision(decision) -> PlacementDecision:
    if isinstance(decision, PlacementDecision):
        return decision

    if all(hasattr(decision, attr) for attr in ("shard_index", "disk_name", "disk_path")):
        return PlacementDecision(
            shard_id=decision.shard_index,
            node_id=getattr(decision, "node_id", "node-1"),
            disk_id=decision.disk_name,
            path=decision.disk_path,
            replica=getattr(decision, "replica", False),
            metadata=getattr(decision, "metadata", None),
        )

    raise TypeError("Placement strategy must return PlacementDecision objects")


def _strategy_name(strategy: PlacementStrategy) -> str:
    return strategy.__class__.__name__


def _shard_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest_entry(
    decision: PlacementDecision,
    shard_path: str,
    is_parity: bool,
    shard_size: int,
    shard_checksum: str,
):
    return {
        "shard": decision.shard_id,
        "type": "parity" if is_parity else "data",
        "node": decision.node_id,
        "disk": decision.disk_id,
        "path": shard_path,
        "replica": decision.replica,
        "size": shard_size,
        "checksum": shard_checksum,
        "metadata": decision.metadata or {},
    }


def save_object_shards(
    db,
    obj,
    data: bytes,
    placement_strategy: PlacementStrategy | None = None,
    cluster_manager: ClusterManager | None = None,
):
    data_shards = split_bytes(data, DATA_SHARDS)
    parity_shards = generate_parity(data_shards)
    all_shards = [*data_shards, *parity_shards]
    strategy = placement_strategy or load_strategy()
    manager = cluster_manager or build_local_cluster_manager(DISKS)
    decisions = [
        _normalize_decision(decision)
        for decision in strategy.place_object(
            PlacementRequest(
                object_id=obj.id,
                object_name=obj.object_name,
                object_size=len(data),
                total_shards=TOTAL_SHARDS,
            ),
            manager.get_storage_targets(),
        )
    ]

    if len(decisions) != TOTAL_SHARDS:
        raise ValueError("Placement strategy must return one placement per shard")

    decisions_by_shard = {
        decision.shard_id: decision
        for decision in decisions
    }

    if set(decisions_by_shard) != set(range(TOTAL_SHARDS)):
        raise ValueError("Placement strategy returned invalid shard indexes")

    manifest = {
        "strategy": _strategy_name(strategy),
        "layout": [],
    }

    written_paths = []

    try:
        for shard_index, shard_data in enumerate(all_shards):
            decision = decisions_by_shard[shard_index]
            shard_path = _write_shard_file(
                object_id=obj.id,
                filename=obj.object_name,
                shard_index=shard_index,
                disk=decision.path,
                data=shard_data,
            )
            written_paths.append(shard_path)
            checksum = _shard_checksum(shard_data)
            is_parity = shard_index >= DATA_SHARDS

            db.add(
                ObjectShard(
                    object_id=obj.id,
                    shard_index=shard_index,
                    disk_name=decision.disk_id,
                    node_id=decision.node_id,
                    disk_id=decision.disk_id,
                    shard_path=shard_path,
                    is_parity=is_parity,
                    shard_size=len(shard_data),
                    shard_checksum=checksum,
                )
            )
            manifest["layout"].append(
                _manifest_entry(
                    decision=decision,
                    shard_path=shard_path,
                    is_parity=is_parity,
                    shard_size=len(shard_data),
                    shard_checksum=checksum,
                )
            )

        db.add(
            ObjectPlacementManifest(
                object_id=obj.id,
                strategy=manifest["strategy"],
                manifest=manifest,
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
