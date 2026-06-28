from app.cluster_manager import StorageTarget
from app.storage_engine.placement import (
    BalancedPlacement,
    CapacityAwarePlacement,
    PlacementScheduler,
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
        data_shards=max(total_shards - 2, 0),
        parity_shards=2 if total_shards >= 2 else 0,
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
    assert isinstance(load_strategy("scheduler"), PlacementScheduler)
    assert isinstance(load_strategy(), PlacementScheduler)


def test_placement_scheduler_keeps_parity_on_different_nodes(tmp_path):
    targets = [
        StorageTarget("node-a", "disk1", tmp_path / "node-a" / "disk1"),
        StorageTarget("node-a", "disk2", tmp_path / "node-a" / "disk2"),
        StorageTarget("node-b", "disk3", tmp_path / "node-b" / "disk3"),
        StorageTarget("node-b", "disk4", tmp_path / "node-b" / "disk4"),
        StorageTarget("node-c", "disk5", tmp_path / "node-c" / "disk5"),
        StorageTarget("node-d", "disk6", tmp_path / "node-d" / "disk6"),
    ]

    decisions = PlacementScheduler().place_object(
        PlacementRequest(
            object_id=1,
            object_name="object.bin",
            object_size=1024,
            total_shards=6,
            data_shards=4,
            parity_shards=2,
        ),
        targets,
    )

    parity_nodes = {
        decision.node_id
        for decision in decisions
        if decision.shard_id in {4, 5}
    }

    assert len(decisions) == 6
    assert len({(decision.node_id, decision.disk_id) for decision in decisions}) == 6
    assert len(parity_nodes) == 2
