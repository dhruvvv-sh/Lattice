from app.storage_engine.nodes import LocalStorageNode, build_local_node_registry


def test_local_storage_node_writes_reads_and_deletes_owned_disk_shards(tmp_path):
    node = LocalStorageNode(
        node_id="node-b",
        disks={
            "disk3": tmp_path / "node-b" / "disk3",
            "disk4": tmp_path / "node-b" / "disk4",
        },
    )

    shard = node.write_shard("disk3", "object_1_sample.bin.part2", b"shard-data")

    assert shard.node_id == "node-b"
    assert shard.disk_id == "disk3"
    assert node.read_shard("disk3", shard.path) == b"shard-data"

    node.delete_shard("disk3", shard.path)

    try:
        node.read_shard("disk3", shard.path)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected deleted shard to be missing")


def test_local_node_registry_exposes_node_owned_disks_as_cluster_targets(tmp_path):
    registry = build_local_node_registry(
        {
            "node-a": [tmp_path / "node-a" / "disk1", tmp_path / "node-a" / "disk2"],
            "node-b": [tmp_path / "node-b" / "disk3", tmp_path / "node-b" / "disk4"],
            "node-c": [tmp_path / "node-c" / "disk5", tmp_path / "node-c" / "disk6"],
        }
    )

    manager = registry.build_cluster_manager()
    targets = manager.get_storage_targets()

    assert [(target.node_id, target.disk_id) for target in targets] == [
        ("node-a", "disk1"),
        ("node-a", "disk2"),
        ("node-b", "disk3"),
        ("node-b", "disk4"),
        ("node-c", "disk5"),
        ("node-c", "disk6"),
    ]
