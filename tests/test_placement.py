from app.cluster_manager import StorageTarget
from app.storage_engine.placement import (
    BalancedPlacement,
    CapacityAwarePlacement,
    PlacementDecision,
    PlacementRequest,
    RandomPlacement,
    load_strategy,
)


def placement_request(total_shards=3):
    return PlacementRequest(
        object_id=1,
        object_name="object.bin",
        object_size=1024,
        total_shards=total_shards,
    )


def test_balanced_placement_prefers_least_used_healthy_disks(tmp_path):
    targets = [
        StorageTarget("node-1", "disk-a", tmp_path / "a", used_bytes=500),
        StorageTarget("node-1", "disk-b", tmp_path / "b", used_bytes=10),
        StorageTarget("node-2", "disk-c", tmp_path / "c", used_bytes=200),
        StorageTarget("node-2", "disk-d", tmp_path / "d", used_bytes=0, healthy=False),
    ]

    decisions = BalancedPlacement().place_object(
        placement_request(total_shards=2),
        targets,
    )

    assert all(isinstance(decision, PlacementDecision) for decision in decisions)
    assert [decision.disk_id for decision in decisions] == ["disk-b", "disk-c"]
    assert [decision.node_id for decision in decisions] == ["node-1", "node-2"]
    assert [decision.shard_id for decision in decisions] == [0, 1]


def test_capacity_aware_placement_prefers_most_free_space(tmp_path):
    targets = [
        StorageTarget("node-1", "disk-a", tmp_path / "a", used_bytes=10, free_space=100),
        StorageTarget("node-1", "disk-b", tmp_path / "b", used_bytes=10, free_space=900),
        StorageTarget("node-2", "disk-c", tmp_path / "c", used_bytes=10, free_space=500),
    ]

    decisions = CapacityAwarePlacement().place_object(
        placement_request(total_shards=2),
        targets,
    )

    assert [decision.disk_id for decision in decisions] == ["disk-b", "disk-c"]


def test_load_strategy_returns_builtin_strategy():
    assert isinstance(load_strategy("balanced"), BalancedPlacement)
    assert isinstance(load_strategy("capacity_aware"), CapacityAwarePlacement)
    assert isinstance(load_strategy("random"), RandomPlacement)
