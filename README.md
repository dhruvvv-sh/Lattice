# Lattice

Lattice is an S3-inspired object storage engine built with Python, FastAPI, and PostgreSQL. The project explores the internal architecture of modern object storage systems such as Amazon S3, MinIO, and Ceph by implementing their core storage mechanisms from first principles.

Rather than functioning as a simple file upload service, Lattice separates metadata management from physical storage and introduces fault-tolerant storage concepts including object sharding, parity generation, disk health monitoring, and parity-based recovery.

The long-term goal is to evolve Lattice into a distributed, fault-tolerant object storage platform with S3-compatible APIs, background healing, multi-node replication, and AI-powered semantic retrieval.

---

# Current Features

### Object Storage

* Bucket creation and management
* Object upload, download, and deletion
* PostgreSQL-backed metadata persistence
* SHA-256 checksum generation
* Multi-disk storage architecture
* Concurrent upload support

### Fault Tolerance

* Object sharding across multiple storage disks
* XOR parity generation
* Shard reconstruction
* Single-shard recovery
* Disk failure simulation
* Disk health monitoring
* Cluster health endpoint

### Engineering

* Modular storage engine architecture
* Separation of metadata and storage layers
* Performance benchmarking with Locust
* Extensible foundation for distributed storage

---

# Architecture

```text
                    Client
                       │
                       ▼
                 FastAPI Server
                       │
                       ▼
                Storage Engine
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  Shard Manager   Erasure Engine   Disk Manager
        │              │              │
        └──────┬───────┴───────┬──────┘
               ▼               ▼
        PostgreSQL        Storage Disks
          Metadata
```

The API layer remains independent of the underlying storage implementation.

Objects are processed through the storage engine, split into shards, protected using parity information, and distributed across multiple storage disks. Metadata describing object placement and storage details is stored separately in PostgreSQL.

---

# Fault-Tolerant Storage Model

Lattice currently implements an experimental parity-based storage architecture.

```text
4 Data Shards + XOR Parity
```

Example:

```text
disk1 → data0
disk2 → data1
disk3 → data2
disk4 → data3
disk5 → parity
```

Workflow:

```text
Object
   ↓
Split Into Shards
   ↓
Generate Parity
   ↓
Distribute Across Disks
   ↓
Detect Failure
   ↓
Recover Missing Shard
```

Current implementation supports recovery of a single missing shard using parity information.

Future releases will replace the current XOR parity implementation with Reed-Solomon erasure coding for stronger fault tolerance and multi-shard recovery.

---

# Storage Simulations

Lattice includes fault-tolerance simulations used to validate storage reliability.

### Shard Recovery Simulation

1. Split object into multiple data shards
2. Generate parity information
3. Simulate shard loss
4. Recover missing shard
5. Verify integrity using SHA-256 hashes

Example Verification:

```text
Original :
4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc

Recovered:
4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc
```

Result:

```text
Recovery Successful
Integrity Verified
```

### Disk Health Monitoring

Lattice periodically checks storage disks and exposes cluster health information.

Example:

```json
{
  "disk1": "healthy",
  "disk2": "healthy",
  "disk3": "dead",
  "disk4": "healthy",
  "disk5": "healthy",
  "disk6": "healthy"
}
```

This serves as the foundation for future automatic healing and background repair systems.

---

# Technology Stack

| Component         | Technology          |
| ----------------- | ------------------- |
| Language          | Python 3            |
| API               | FastAPI             |
| ORM               | SQLAlchemy          |
| Metadata Database | PostgreSQL          |
| Storage Backend   | Local Filesystem    |
| Fault Tolerance   | XOR Parity Recovery |
| Load Testing      | Locust              |
| Authentication    | JWT (Planned)       |
| Cache             | Redis (Planned)     |

---

# Project Structure

```text
lattice/

├── app/
│   ├── api/
│   │   ├── buckets.py
│   │   ├── objects.py
│   │   └── cluster.py
│   │
│   ├── storage/
│   │   ├── shard_manager.py
│   │   ├── disk_manager.py
│   │   ├── erasure.py
│   │   ├── reconstruction.py
│   │   ├── health_checker.py
│   │   ├── heartbeat.py
│   │   └── cluster_state.py
│   │
│   ├── models/
│   ├── database.py
│   └── utils/
│
├── storage/
│   ├── disk1/
│   ├── disk2/
│   ├── disk3/
│   ├── disk4/
│   ├── disk5/
│   └── disk6/
│
├── benchmarks/
├── tests/
├── simulationoutputs.md
├── README.md
└── requirements.txt
```

---

# Metadata Architecture

## Objects

Stores logical object metadata:

* Object ID
* Bucket ID
* Object Name
* Object Size
* SHA-256 Checksum

## Future Shard Metadata Layer

Planned metadata for shard tracking:

* Object ID
* Shard Index
* Disk Name
* File Path
* Parity Flag
* Shard Size

This abstraction enables future storage placement strategies, replication policies, and automatic repair workflows.

---

# Benchmark Evolution

## Version 1 — SQLite

* SQLite metadata backend
* Concurrent upload failures due to database locking
* Initial storage engine implementation

## Version 2 — PostgreSQL

* Migrated metadata layer to PostgreSQL
* Eliminated SQLite write-lock bottlenecks
* Improved concurrent upload performance
* Reduced request failure rates

Performance benchmark results are available in the `benchmarks/` directory.

---

# Design Principles

* Separation of metadata and object storage
* Modular storage engine architecture
* Fault-tolerant storage design
* Extensible placement strategies
* S3-inspired object model
* Performance-driven development
* Distributed-systems learning focus
* Storage-first engineering approach

---

# Roadmap

## Completed

* Bucket management
* Object CRUD operations
* PostgreSQL metadata engine
* Multi-disk storage abstraction
* Object sharding
* XOR parity generation
* Shard reconstruction
* Single-shard recovery
* Disk health monitoring
* Cluster health endpoint
* Performance benchmarking

## In Progress

* Upload pipeline integration with parity storage
* Download reconstruction pipeline
* Automatic shard recovery
* Shard placement metadata
* Background repair workflows

## Planned

* Reed-Solomon erasure coding
* Multipart uploads
* Redis metadata caching
* Object versioning
* Deduplication
* Presigned URLs
* S3-compatible client support
* Read repair
* Background healing jobs
* Distributed multi-node storage
* Cross-node replication
* Kubernetes deployment
* AI-powered semantic object retrieval (RAG)

---

# Motivation

Lattice was created as a systems engineering project to understand how modern object storage platforms separate metadata management from physical storage while maintaining durability, scalability, and fault tolerance.

Instead of relying on existing storage frameworks, Lattice implements core storage concepts directly, including object sharding, parity-based recovery, metadata management, disk health monitoring, and multi-disk placement.

The long-term vision is to evolve Lattice into a distributed object storage engine capable of fault-tolerant storage, S3 compatibility, automatic healing, and intelligent semantic retrieval.

---

# License

MIT License
