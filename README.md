# Lattice

Lattice is an S3-inspired object storage engine built with Python, FastAPI, and PostgreSQL. The project explores how systems such as Amazon S3, MinIO, and Ceph separate metadata from physical object storage while preserving durability, scalability, and fault tolerance.

The current project has three active layers:

* A working FastAPI object API backed by SQLAlchemy metadata and local filesystem storage.
* A sharded storage engine that routes API uploads through Reed-Solomon `4+2` erasure coding.
* A cluster and placement layer that models storage nodes, storage targets, placement decisions, and persisted placement manifests.

The long-term goal is to evolve Lattice into a distributed, fault-tolerant object storage platform with S3-compatible APIs, background healing, multi-node replication, and AI-powered semantic retrieval.

---

# Current Features

## Object API

* Bucket creation, listing, update, and deletion
* Object upload, download, listing, and deletion
* PostgreSQL-backed metadata persistence
* SHA-256 checksum generation
* Sharded object placement through the placement engine
* Download reconstruction from shard metadata
* Recovery during download when up to two shards are missing
* Concurrent upload benchmarking with Locust

## Storage Engine

* Object splitting into 4 data shards
* Reed-Solomon parity generation with a `4+2` layout
* API upload path writes 4 data shards and 2 parity shards
* API download path reconstructs objects from shard metadata
* Recovery from one or two missing shards
* Full object reconstruction from data shards
* Original-size trimming after padded reconstruction
* Persisted `object_shards` metadata
* Persisted placement manifest per object
* Disk health checks and cluster health state
* Documented Reed-Solomon recovery test cases

## Cluster and Placement

* `ClusterManager` registers storage nodes and storage targets
* `StorageTarget` models node, disk, capacity, health, online status, and storage type
* `PlacementStrategy` implementations operate on storage targets, not raw disks
* Built-in strategies include balanced, capacity-aware, and random placement
* `PlacementDecision` records shard destination node, disk, path, and replica metadata
* Custom placement strategies can be injected directly or loaded by environment variable

## Current Boundary

Lattice currently runs as a single API process with local storage targets. The architecture now has the right seams for multi-node storage, but actual node-to-node transfer, replication, background repair, and rebalancing are still planned work.

For a practical map of where each layer lives and where to add future features, see `docs/project-organization.md`.

---

# Architecture

```text
                    Client
                       |
                       v
                 FastAPI Server
                       |
                       v
              Object API / Metadata
                       |
                       v
               Placement Engine
                       |
                       v
                Cluster Manager
                       |
                       v
              Storage Targets
                       |
                       v
       Reed-Solomon 4+2 Sharded Storage
                       |
                       v
                  PostgreSQL
```

The API layer now uses the sharded path for uploads and downloads. The cluster manager is the source of truth for candidate storage targets, while placement strategies decide where each shard should be written.

---

# Fault-Tolerant Storage Model

The storage prototype now uses Reed-Solomon erasure coding:

```text
4 Data Shards + 2 Parity Shards
```

Example logical placement:

```text
storage/cluster/node-a/disk1 -> data0
storage/cluster/node-a/disk2 -> data1
storage/cluster/node-b/disk3 -> data2
storage/cluster/node-b/disk4 -> data3
storage/cluster/node-c/disk5 -> parity0
storage/cluster/node-c/disk6 -> parity1
```

Supported recovery cases:

* One missing data shard
* Two missing data shards
* One missing data shard plus one missing parity shard
* Two missing parity shards
* Failure when more than two total shards are missing

Detailed results are documented in `app/storage/reed_solomon_test_cases.md`.

---

# Verification

The automated tests validate both the Reed-Solomon storage layer and the API-integrated sharded path.

## Reed-Solomon Verification

The current verification covers:

```text
data_size 36
data_shards 4 [9, 9, 9, 9]
parity_shards 2 [9, 9]
case_1_single_data_missing ok
case_2_data_and_parity_missing ok
case_3_two_data_missing ok
case_4_two_parity_missing ok
case_5_three_missing failed_as_expected Too many missing shards to recover
case_6_reconstruction_trim ok
```

## Sample PDF Recovery

The sample shard recovery flow also verifies a recovered shard with SHA-256:

```text
Original : 4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc
Recovered: 4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc
```

Result:

```text
Recovery Successful
Integrity Verified
```

## Current Test Suite

The current pytest suite covers:

* Cluster manager node and storage-target registration
* Healthy and offline target filtering
* Balanced, capacity-aware, and random placement strategy behavior
* Custom placement strategy compatibility
* API upload through sharded storage
* Placement manifest persistence
* Download recovery after one data shard and one parity shard are missing
* Object delete cleanup for shard files and metadata

Latest verification:

```text
10 passed
```

---

# Technology Stack

| Component | Technology |
| --- | --- |
| Language | Python 3 |
| API | FastAPI |
| ORM | SQLAlchemy |
| Metadata Database | PostgreSQL |
| Storage Backend | Local Filesystem |
| Erasure Coding | Reed-Solomon via `reedsolo` |
| Placement | Pluggable placement strategies |
| Load Testing | Locust |
| Container Runtime | Docker Compose |
| Load Balancer | FastAPI + HTTPX local reverse proxy |
| Authentication | JWT (planned) |
| Cache | Redis (planned) |

---

# Run Local Load Balancer

Start two API replicas on different ports:

```bash
uvicorn main:app --host 127.0.0.1 --port 8001
uvicorn main:app --host 127.0.0.1 --port 8002
```

Start the load balancer on port `8000`:

```bash
LATTICE_BACKENDS=http://127.0.0.1:8001,http://127.0.0.1:8002 uvicorn load_balancer:app --host 127.0.0.1 --port 8000
```

The application is then available through the load balancer at:

```text
http://localhost:8000
```

The load balancer uses round-robin routing across the configured API replicas.
You can check its status at:

```text
http://localhost:8000/lb/health
```

---

# Run With Docker

Build and start the API with PostgreSQL:

```bash
docker compose --env-file .env.docker up --build
```

The API will be available at:

```text
http://localhost:8000
```

PostgreSQL runs inside Docker with this connection string:

```text
postgresql://postgres:postgres@localhost:5432/lattice
```

Uploaded object shards are stored under `storage/cluster/` through a bind mount, and database files are stored in the Docker volume `postgres_data`.

To stop the containers:

```bash
docker compose --env-file .env.docker down
```

To remove the database volume as well:

```bash
docker compose --env-file .env.docker down -v
```

---

# Project Structure

```text
lattice/
|-- app/
|   |-- api/
|   |   |-- buckets.py
|   |   |-- objects.py
|   |   `-- cluster.py
|   |-- cluster_manager.py
|   |-- storage/
|   |   |-- shard_manager.py
|   |   |-- disk_manager.py
|   |   |-- erasure.py
|   |   |-- reconstruction.py
|   |   |-- health_check.py
|   |   |-- heartbeat.py
|   |   |-- cluster_state.py
|   |   |-- storagestructure.md
|   |   `-- reed_solomon_test_cases.md
|   |-- storage_engine/
|   |   |-- placement.py
|   |   |-- sharded.py
|   |   |-- writer.py
|   |   |-- reader.py
|   |   |-- disk_selector.py
|   |   |-- checksum.py
|   |   `-- delete.py
|   |-- database.py
|   |-- models.py
|   `-- schemas.py
|-- benchmark/
|   |-- benchmarks_locust_v1.md
|   `-- benchmarks_locust_v2.md
|-- docs/
|   `-- project-organization.md
|-- tests/
|   |-- test_cluster_manager.py
|   |-- test_objects_api.py
|   |-- test_placement.py
|   `-- test_sharded_storage.py
|-- storage/
|   |-- cluster/
|   |   |-- node-a/
|   |   |-- node-b/
|   |   `-- ...
|   |-- legacy/
|   `-- samples/
|-- load_balancer.py
|-- Dockerfile
|-- docker-compose.yml
|-- simulationoutputs.md
|-- README.md
`-- requirements.txt
```

---

# Metadata Architecture

## Objects Table

Stores logical object metadata:

* Object ID
* Bucket ID
* Object name
* Logical sharded path
* Storage mode
* Object size
* Content type
* SHA-256 checksum

## Object Shards Table

The `ObjectShard` model stores physical shard metadata:

* Object ID
* Shard index
* Node ID
* Disk ID
* Disk name
* Shard path
* Parity flag
* Shard size
* Shard checksum

## Object Placement Manifests Table

The `ObjectPlacementManifest` model stores an object-level placement document:

* Object ID
* Placement strategy name
* Manifest JSON with shard layout, node, disk, path, type, size, checksum, and future replica metadata

The manifest is intended to support future recovery, rebalancing, replication, and cluster visualization workflows.

---

# Benchmark Evolution

## Version 1: SQLite

* SQLite metadata backend
* Concurrent upload failures due to database locking
* Initial storage engine implementation

## Version 2: PostgreSQL

* Migrated metadata layer to PostgreSQL
* Eliminated SQLite write-lock bottlenecks
* Improved concurrent upload performance
* Reduced request failure rates

Performance benchmark results are available in the `benchmark/` directory.

---

# Roadmap

## Completed

* Bucket management
* Object CRUD operations
* PostgreSQL metadata engine
* Docker Compose setup for API plus PostgreSQL
* Local round-robin load balancer for multiple API replicas
* Multi-disk storage directories
* Object sharding prototype
* Reed-Solomon parity generation
* One- and two-shard recovery in the storage prototype
* Full shard reconstruction helper
* Disk health monitoring
* Cluster health endpoint
* Locust performance benchmarking
* Upload pipeline integration with Reed-Solomon shard storage
* Download reconstruction pipeline for API reads
* Persisting shard placement metadata during uploads
* Cluster manager for node and storage-target inventory
* Pluggable placement engine
* Placement decision and manifest generation
* API-level tests for sharded upload/download/delete

## In Progress

* Automatic shard recovery
* Background repair workflows

## Planned

* Node-to-node shard transfer
* Multi-node cluster deployment
* Containerized load balancer deployment
* Rack-aware and latency-aware placement
* Replication-aware placement decisions
* Automatic rebalancing
* Multipart uploads
* Redis metadata caching
* Object versioning
* Deduplication
* Presigned URLs
* S3-compatible client support
* Read repair
* Cross-node replication
* Kubernetes deployment
* AI-powered semantic object retrieval (RAG)

---

# FOR THE VISUAL LEARNERS ;)
<img width="1378" height="478" alt="Screenshot 2026-07-02 at 10 12 11 PM" src="https://github.com/user-attachments/assets/4daefad1-8e2d-4a29-a445-46bdea1abd4d" />



---

# License

MIT License
