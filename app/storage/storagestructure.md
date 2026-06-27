# Lattice Storage Engine Architecture

This document describes the current sharded storage design and the cluster-aware placement foundation.

---

# Current State

Lattice now uses the sharded storage path for API uploads and downloads.

| Layer | Location | State |
| --- | --- | --- |
| Object API | `app/api/objects.py` | Accepts uploads, downloads, listings, and deletes |
| Storage engine | `app/storage_engine/sharded.py` | Splits objects, writes shards, reconstructs downloads |
| Placement engine | `app/storage_engine/placement.py` | Chooses storage targets through pluggable strategies |
| Cluster manager | `app/cluster_manager.py` | Tracks storage nodes and storage targets |
| Reed-Solomon engine | `app/storage/erasure.py` | Generates parity and recovers missing shards |
| Metadata | `app/models.py` | Stores objects, shards, and placement manifests |

The older whole-file writer still exists in `app/storage_engine/writer.py`, but the active object API upload path uses Reed-Solomon sharding.

---

# API Upload Flow

```text
Client
  |
  | POST /objects/upload/{bucket_id}
  v
FastAPI API
  |
  | Validate bucket and read uploaded bytes
  v
Storage Engine
  |
  | Split object into 4 data shards
  v
Erasure Engine
  |
  | Generate 2 Reed-Solomon parity shards
  v
Cluster Manager
  |
  | Return available StorageTarget entries
  v
Placement Strategy
  |
  | Return PlacementDecision entries
  v
Storage Engine
  |
  | Write shards to selected targets
  v
Metadata
  |
  | Store object, shard rows, and placement manifest
  v
Return success response
```

---

# API Download Flow

```text
Client
  |
  | GET /objects/{object_id}
  v
FastAPI API
  |
  | Query object and shard metadata
  v
Storage Engine
  |
  | Read available shards from recorded paths
  v
Erasure Engine
  |
  | Recover missing shards when <= 2 shards are missing
  v
Shard Manager
  |
  | Reconstruct bytes and trim to original size
  v
Return object bytes to client
```

---

# Reed-Solomon Fault Tolerance Model

Lattice currently uses a `4+2` Reed-Solomon layout:

```text
4 data shards + 2 parity shards
```

Example logical placement:

```text
node-1/disk1 -> data0
node-1/disk2 -> data1
node-1/disk3 -> data2
node-1/disk4 -> data3
node-1/disk5 -> parity0
node-1/disk6 -> parity1
```

Recovery support:

* One missing data shard
* Two missing data shards
* One missing data shard and one missing parity shard
* Two missing parity shards
* Correct failure when more than two total shards are missing

---

# Cluster Manager

`app/cluster_manager.py` is the source of truth for storage inventory.

Responsibilities:

* Register storage nodes
* Remove storage nodes
* Track node health and online status
* Register storage targets
* Remove storage targets
* Track capacity, free space, used bytes, storage type, region, rack, and latency fields
* Return filtered healthy and online storage targets to the placement engine

The current local implementation bootstraps one node:

```text
node-1
  disk1
  disk2
  disk3
  disk4
  disk5
  disk6
```

This keeps the single-node development experience simple while preparing the model for real multi-node storage.

---

# Placement Engine

`app/storage_engine/placement.py` defines the placement contract.

## StorageTarget

Represents a target that can receive a shard:

```text
node_id
disk_id
path
capacity
free_space
healthy
online
storage_type
used_bytes
region
rack_id
latency_ms
metadata
```

## PlacementDecision

Represents the plan for one shard:

```text
shard_id
node_id
disk_id
path
replica
metadata
```

## PlacementStrategy

Strategies receive a `PlacementRequest` and a list of `StorageTarget` objects.

Built-in strategies:

* `BalancedPlacement`: chooses least-used healthy online targets
* `CapacityAwarePlacement`: chooses targets with the most free space
* `RandomPlacement`: chooses random healthy online targets

Custom placement strategies can be injected into `save_object_shards()` or loaded with:

```text
LATTICE_PLACEMENT_STRATEGY=my_package.MyPlacementStrategy
```

---

# Placement Manifest

Each uploaded object gets one persisted placement manifest.

Example shape:

```json
{
  "strategy": "BalancedPlacement",
  "layout": [
    {
      "shard": 0,
      "type": "data",
      "node": "node-1",
      "disk": "disk1",
      "path": "storage/disk1/object_1_file.bin.part0",
      "replica": false,
      "size": 1024,
      "checksum": "...",
      "metadata": {}
    }
  ]
}
```

Future features will use this manifest for:

* Node recovery
* Shard reconstruction
* Read repair
* Rebalancing
* Replication
* Cluster visualization

---

# Metadata Layer

## `objects`

Stores logical object metadata:

* Object ID
* Bucket ID
* Object name
* Logical sharded path
* Storage mode
* Object size
* Content type
* Checksum
* Created timestamp

## `object_shards`

Stores physical shard metadata:

* Object ID
* Shard index
* Node ID
* Disk ID
* Disk name
* Shard path
* Parity flag
* Shard size
* Shard checksum
* Created timestamp

## `object_placement_manifests`

Stores object-level placement metadata:

* Object ID
* Strategy name
* Manifest JSON
* Created timestamp

---

# Current Verification Results

Automated tests currently cover:

```text
Cluster Manager registration and filtering
PlacementDecision generation
Placement manifest generation
Custom placement strategy compatibility
Sharded upload/download/delete
Recovery after one data shard and one parity shard are missing
Failure when more than two shards are missing
```

Latest result:

```text
10 passed
```

---

# Planned Work

* Add a repair endpoint that rewrites missing recovered shards.
* Add node-to-node shard transfer.
* Persist real multi-node cluster state.
* Add rack-aware and latency-aware placement.
* Add replication-aware placement decisions.
* Add automatic rebalancing.
* Move from `Base.metadata.create_all()` to Alembic migrations.
