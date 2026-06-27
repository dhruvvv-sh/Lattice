from app.cluster_manager import ClusterManager


def test_cluster_manager_registers_nodes_and_storage_targets(tmp_path):
    manager = ClusterManager()
    node = manager.register_node(
        node_id="node-1",
        host="10.0.0.1",
        port=8000,
        region="us-east",
        rack_id="rack-a",
    )
    target = manager.register_storage_target(
        node_id=node.node_id,
        disk_id="disk-1",
        path=tmp_path / "disk-1",
        capacity=1000,
        free_space=750,
        used_bytes=250,
    )

    targets = manager.get_storage_targets()

    assert targets == [target]
    assert target.node_id == "node-1"
    assert target.disk_id == "disk-1"
    assert target.region == "us-east"
    assert target.rack_id == "rack-a"
    assert target.free_space == 750


def test_cluster_manager_filters_unhealthy_and_offline_nodes_and_targets(tmp_path):
    manager = ClusterManager()
    manager.register_node("node-1")
    manager.register_node("node-2")
    manager.register_node("node-3")
    manager.register_storage_target("node-1", "disk-1", tmp_path / "disk-1")
    manager.register_storage_target(
        "node-2",
        "disk-1",
        tmp_path / "disk-2",
        healthy=False,
    )
    manager.register_storage_target("node-3", "disk-1", tmp_path / "disk-3")

    manager.mark_node("node-3", online=False)

    targets = manager.get_storage_targets()
    all_targets = manager.get_storage_targets(
        include_unhealthy=True,
        include_offline=True,
    )

    assert [(target.node_id, target.disk_id) for target in targets] == [
        ("node-1", "disk-1")
    ]
    assert len(all_targets) == 3


def test_cluster_manager_removes_node_targets(tmp_path):
    manager = ClusterManager()
    manager.register_storage_target("node-1", "disk-1", tmp_path / "disk-1")
    manager.register_storage_target("node-1", "disk-2", tmp_path / "disk-2")
    manager.register_storage_target("node-2", "disk-1", tmp_path / "disk-3")

    manager.remove_node("node-1")

    assert [(target.node_id, target.disk_id) for target in manager.get_storage_targets()] == [
        ("node-2", "disk-1")
    ]
