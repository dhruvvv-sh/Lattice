# Project Organization

This project is organized around the object storage path:

```text
FastAPI API -> metadata models -> placement -> node registry -> shard storage
```

Keep new work close to the layer it belongs to. If a feature crosses layers, start at the API boundary and follow the object write/read path down.

## Code Layout

```text
app/
|-- api/                 FastAPI routes and request/response behavior
|-- storage_engine/      Upload/download orchestration, placement, node clients
|-- storage/             Erasure coding, shard splitting, health helpers
|-- cluster_manager.py   In-memory node and disk target registry
|-- database.py          SQLAlchemy engine/session setup
|-- models.py            Persistent metadata tables
`-- schemas.py           API schemas

tests/                   Focused tests for API, placement, nodes, and sharding
benchmark/               Locust and benchmark notes
docs/                    Architecture and implementation notes
storage/                 Local development data only
```

## Runtime Storage Layout

Runtime object shards should live under `storage/cluster`:

```text
storage/
|-- cluster/
|   |-- node-a/
|   |   |-- disk1/
|   |   `-- disk2/
|   |-- node-b/
|   |   |-- disk3/
|   |   `-- disk4/
|   `-- ...
|-- samples/             Checked-in demo or recovery artifacts
`-- legacy/              Output from older helper scripts
```

The active topology is defined in `app/storage/cluster_state.py`. The current local topology uses five logical nodes and ten local disks. These are local filesystem-backed stand-ins for future networked storage-node services.

## Where To Implement Features

Use this map when adding the next architecture pieces:

| Feature | Primary Location |
| --- | --- |
| Bucket/object HTTP behavior | `app/api/` |
| Metadata fields and relations | `app/models.py` |
| Database connection/session behavior | `app/database.py` |
| Object write/read orchestration | `app/storage_engine/sharded.py` |
| Placement policy | `app/storage_engine/placement.py` |
| Node and disk abstraction | `app/storage_engine/nodes.py` |
| Cluster target registration | `app/cluster_manager.py` |
| Reed-Solomon behavior | `app/storage/erasure.py` |
| Shard splitting/reconstruction | `app/storage/shard_manager.py` |
| Health scan behavior | `app/storage/heartbeat.py` |
| Local API load balancing | `load_balancer.py` |

## Implementation Order

For the distributed architecture, implement in this order:

1. Keep the current local node registry stable and well tested.
2. Add a remote `StorageNodeClient` implementation beside `LocalStorageNode`.
3. Run storage nodes as separate FastAPI services.
4. Add Redis for cache, locks, rate limits, and live node health.
5. Add background workers for healing and rebalancing.
6. Containerize the local load balancer and run multiple API replicas in the
   deployment environment.

This keeps the prototype usable while each layer becomes real.
