# Lattice Architecture and Pipeline

This document explains the Lattice project in a way that is easy to understand
and easy to present. It focuses on what the system does, how data moves through
it, and why the current technology choices make sense.

## Project Summary

Lattice is an S3-inspired object storage system. In simple terms, it lets a
client create buckets, upload files as objects, download those objects later,
and delete them when they are no longer needed.

The important idea is that Lattice separates object metadata from object data:

| Concern | Stored In | Example |
| --- | --- | --- |
| Metadata | PostgreSQL | Bucket name, object name, checksum, shard locations |
| Object bytes | Local filesystem storage targets | The actual shard files written under `storage/cluster/` |

This separation is common in object storage systems. The database answers
questions like "what object exists?" and "where are its shards?", while the
storage layer handles the file bytes.

## High-Level Architecture

```text
Client
  |
  v
Local load balancer
  |
  v
FastAPI application replicas
  |
  v
API routes
  |
  v
SQLAlchemy metadata models <----> PostgreSQL
  |
  v
Placement strategy
  |
  v
Cluster manager and node registry
  |
  v
Reed-Solomon sharded storage
  |
  v
Local filesystem storage targets
```

The current project can run as one API service or as multiple local API
replicas behind the Python load balancer in `load_balancer.py`. Storage targets
represent disks on storage nodes, but today they are simulated with local
directories. This keeps the project practical while still preserving the
architecture needed for future distributed storage nodes.

## Main Components

### FastAPI Application

The FastAPI app starts in `main.py`. It registers routes for buckets, objects,
cluster health, and the visualizer.

FastAPI is responsible for:

- Receiving HTTP requests.
- Parsing uploaded files and request bodies.
- Returning JSON responses or downloaded object bytes.
- Exposing routes such as `/buckets`, `/objects`, `/cluster/health`, and
  `/health`.

### API Layer

The API layer lives in `app/api/`.

| File | Responsibility |
| --- | --- |
| `buckets.py` | Create, list, update, and delete buckets |
| `objects.py` | Upload, download, list, and delete objects |
| `cluster.py` | Return cluster health information |
| `visualizer.py` | Serve the storage visualizer UI |

The API layer should stay focused on request and response behavior. It should
not contain the full storage algorithm. Instead, it calls lower-level modules
that know how to place shards, write files, and reconstruct objects.

### Local Load Balancer

The local load balancer is implemented in `load_balancer.py` with FastAPI and
HTTPX.

The load balancer is responsible for:

- Listening on host port `8000`.
- Forwarding requests to backend API replicas such as `127.0.0.1:8001` and
  `127.0.0.1:8002`.
- Routing requests with a simple round-robin strategy.
- Exposing `/lb/health` and `/lb/backends` for development visibility.
- Preserving forwarded request headers for future observability.

This lets the project validate load-balancing behavior during normal local
development before containerizing that layer later.

### PostgreSQL Metadata Database

PostgreSQL stores the metadata tables defined in `app/models.py`.

The key tables are:

| Table | Purpose |
| --- | --- |
| `buckets` | Stores bucket records |
| `objects` | Stores logical object records |
| `object_shards` | Stores one row per physical shard copy, including shard index, copy index, role, path, node ID, disk ID, health, size, and checksum |
| `object_placement_manifests` | Stores the full placement decision for each object |

PostgreSQL does not store the uploaded file bytes directly. It stores the map
that tells Lattice where those bytes were written.

### SQLAlchemy ORM

SQLAlchemy connects Python code to PostgreSQL.

It is used for:

- Creating database sessions.
- Defining models as Python classes.
- Querying buckets and objects.
- Persisting object shard metadata.
- Deleting related shard metadata when an object is removed.

The database setup lives in `app/database.py`.

### Storage Engine

The storage engine lives mainly in `app/storage_engine/` and `app/storage/`.

Its job is to turn one uploaded file into multiple recoverable shards.

Important modules:

| File | Responsibility |
| --- | --- |
| `app/storage_engine/sharded.py` | Coordinates splitting, parity generation, placement, writes, reads, and cleanup |
| `app/storage_engine/placement.py` | Chooses which storage target should hold each shard |
| `app/storage_engine/nodes.py` | Defines local storage node clients and the node registry |
| `app/storage/erasure.py` | Handles Reed-Solomon parity and recovery |
| `app/storage/shard_manager.py` | Splits bytes into data shards and reconstructs bytes |

### Cluster Manager

`app/cluster_manager.py` tracks storage nodes and storage targets.

A storage node is a logical machine. A storage target is a specific disk or
directory owned by a node.

Today, these are local directories. In a future distributed version, the same
architecture can point to remote storage-node services.

### Placement Strategy

Placement strategies decide where each shard should go.

Current strategies include:

- `node_hash`: deterministic placement based on object and shard IDs.
- `balanced`: prefers targets with lower used space.
- `capacity_aware`: prefers targets with more free space.
- `random` / `scheduler`: spreads shards randomly across healthy targets.
- `replication_aware`: places each logical shard as a primary copy plus replica
  copies on different logical nodes.

The default strategy is `node_hash`, configured in
`app/storage_engine/placement.py`.

### Reed-Solomon Erasure Coding

Lattice currently uses a `4+2` Reed-Solomon layout:

```text
4 data shards + 2 parity shards = 6 total shards
```

This means the system can recover the object if up to two shards are missing.
That is the main durability feature of the current storage engine.

### Shard-Level Replication

Lattice also has the metadata and placement path for shard-level replication.
Replication happens per logical Reed-Solomon shard, not by copying the whole
object.

With replication factor `2`, each logical shard has two physical copies:

```text
logical shard 0 -> primary copy on node-a/disk1
logical shard 0 -> replica copy on node-c/disk5

logical shard 1 -> primary copy on node-b/disk3
logical shard 1 -> replica copy on node-d/disk7
```

The `object_shards` table stores every physical copy. The `copy_index` column
identifies copy `0` as the primary, while copy indexes `1+` are replicas. The
`role` column stores `primary` or `replica`, and `healthy` prepares the system
for future repair workflows.

Replication complements Reed-Solomon:

- Replication gives a fast alternate copy of a shard.
- Reed-Solomon reconstructs the object when logical shard data is unavailable.

## Upload Pipeline

When a client uploads a file, this is the flow:

```text
1. Client sends file to FastAPI
2. API validates the bucket exists
3. API reads the uploaded bytes
4. API calculates a SHA-256 checksum
5. API creates an object metadata row in PostgreSQL
6. Storage engine splits the file into 4 data shards
7. Storage engine creates 2 parity shards with Reed-Solomon
8. Placement strategy chooses storage targets for all logical shards
9. If replication is enabled, placement chooses primary and replica targets
   for each logical shard
10. Node registry writes every physical shard copy to the selected local disk
    path
11. PostgreSQL stores one row per physical copy in object_shards
12. PostgreSQL stores the full placement manifest
13. API commits the transaction and returns upload metadata
```

In short:

```text
One uploaded file -> checksum -> metadata row -> 4 data shards -> 2 parity shards
-> placement decisions -> primary and replica shard files -> shard-copy metadata
```

If the upload fails after writing some shard files, the API rolls back the
database transaction and removes the partially written shard files.

Current replicated upload behavior:

```text
logical shard -> primary physical copy + replica physical copy
```

The download path still treats available physical copies as shard data and will
be updated to explicitly prefer primaries, then replicas, before Reed-Solomon
reconstruction.

## Download Pipeline

When a client downloads an object, this is the flow:

```text
1. Client requests an object by object ID
2. API loads the object metadata from PostgreSQL
3. API loads the shard metadata for that object
4. Storage engine tries to read each shard from its recorded node and disk
5. If all data shards are present, the object is reconstructed directly
6. If one or two shards are missing, Reed-Solomon recovery rebuilds the missing data
7. Reconstructed bytes are trimmed back to the original object size
8. API returns the file bytes to the client
```

In short:

```text
Object ID -> metadata lookup -> shard lookup -> shard reads -> optional recovery
-> byte reconstruction -> file response
```

If more than two shards are missing, the system cannot recover the object with
the current `4+2` layout and returns an error.

## Delete Pipeline

When a client deletes an object:

```text
1. API loads the object metadata
2. API collects all shard paths
3. Storage engine deletes the shard files from disk
4. API deletes the object row from PostgreSQL
5. SQLAlchemy cascades deletion to related shard metadata and placement manifest
6. API commits the transaction
```

This keeps metadata and physical shard files aligned.

## Technology Stack and Tradeoffs

### Python

Python makes the project easy to build, read, and explain. It has strong
libraries for APIs, databases, testing, and data processing.

Tradeoffs:

- Great for fast development and clear prototypes.
- Strong ecosystem for backend services.
- Slower than lower-level languages for very high-throughput storage engines.
- Future performance-critical paths may need optimization, batching, or a
  lower-level implementation.

### FastAPI

FastAPI is used for the HTTP API.

Why it fits:

- Simple route definitions.
- Good support for file uploads.
- Automatic OpenAPI documentation.
- Strong Python type support.
- Works well with async-capable web servers such as Uvicorn.

Tradeoffs:

- The current code uses mostly synchronous database and file operations, so it
  does not fully use async I/O yet.
- For a large distributed storage system, API workers, background jobs, and
  storage nodes would need to be separated more clearly.

### PostgreSQL

PostgreSQL stores metadata, not object bytes.

Why it fits:

- Reliable transactional database.
- Good for relationships between buckets, objects, shards, and placement
  manifests.
- Supports indexes, constraints, and JSON metadata.
- Easy to run locally with Docker Compose.

Tradeoffs:

- PostgreSQL is excellent for metadata but not ideal for storing large file
  bytes directly.
- As object count grows, indexes and query patterns must be designed carefully.
- A production system would need real migrations, backups, connection pooling,
  and possibly read replicas.

### SQLAlchemy

SQLAlchemy keeps database access in Python instead of writing raw SQL
everywhere.

Why it fits:

- Models are easy to understand.
- Relationships and cascade deletes are useful for object and shard metadata.
- Keeps database code organized.

Tradeoffs:

- ORM behavior can hide expensive queries if the project grows.
- The project currently uses `create_all()` plus a small runtime schema patch.
  A production version should use Alembic migrations instead.

### Local Filesystem Storage

The actual shard bytes are stored on the local filesystem under
`storage/cluster/`.

Why it fits:

- Very easy to inspect and debug.
- No external storage service is required.
- Good for demonstrating placement, sharding, recovery, and deletion.

Tradeoffs:

- Local directories are not the same as real networked storage nodes.
- Local storage does not provide true machine-level fault tolerance.
- Future distributed versions need remote storage node APIs, node-to-node
  transfer, background healing, and rebalancing.

### Reed-Solomon Erasure Coding

Reed-Solomon is used to reduce data loss risk without storing full copies of
every object.

Why it fits:

- The `4+2` layout can tolerate two missing shards.
- More space-efficient than simple triple replication.
- Demonstrates a real object-storage durability concept.

Tradeoffs:

- More complex than replication.
- Uploads and downloads require encoding or reconstruction work.
- Recovery is limited by the number of parity shards. With two parity shards,
  three missing shards means the object cannot be recovered.

### Docker Compose

Docker Compose runs the API and PostgreSQL together for local development.

Why it fits:

- Makes the project easier to start consistently.
- Keeps PostgreSQL setup simple.
- Uses a volume for database persistence and a bind mount for storage files.

Tradeoffs:

- Good for local development, but not a production orchestration solution.
- Production deployments would need Kubernetes, ECS, Nomad, or another
  deployment platform.
- The local load balancer should be containerized later when the deployment
  shape is stable.

### Pytest and Locust

Pytest verifies the storage behavior and API paths. Locust is used for
benchmarking concurrent upload behavior.

Why they fit:

- Pytest is simple and effective for unit and integration tests.
- Locust helps simulate real API load.

Tradeoffs:

- Tests are only as strong as the scenarios they cover.
- Load tests on local storage do not fully represent distributed production
  performance.

## Current Architecture Boundary

Lattice currently has the shape of a distributed object storage system, but it
is still a local prototype.

What is real today:

- FastAPI object and bucket APIs.
- Local round-robin API load balancing.
- PostgreSQL metadata persistence.
- Object sharding.
- Reed-Solomon parity generation.
- Recovery from up to two missing shards.
- Placement decisions across logical nodes and disks.
- Local filesystem shard storage.

What is still future work:

- Containerized load balancer deployment.
- Separate storage-node services.
- Real network transfer between API and storage nodes.
- Background healing when shards are missing.
- Rebalancing when nodes are added or removed.
- Authentication and authorization.
- Production migrations with Alembic.
- Caching, distributed locks, and live node health through Redis or similar
  infrastructure.

## How To Explain The Project Quickly

Here is a concise explanation:

> Lattice is a prototype object storage system inspired by S3. The API is built
> with FastAPI, metadata is stored in PostgreSQL, and uploaded files are split
> into Reed-Solomon shards on local storage targets. PostgreSQL remembers where
> each shard lives, while the filesystem stores the actual bytes. On download,
> Lattice reads the shard metadata, loads the shard files, and reconstructs the
> original object, even if up to two shards are missing.

The most important design choice is the separation between metadata and data.
That keeps the system understandable and gives the project a clear path from a
local prototype toward a distributed storage platform.
