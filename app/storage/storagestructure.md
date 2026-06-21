# Lattice Storage Engine Architecture (v2)

## Upload Flow

```text
                Client
                   │
                   │ POST /objects/upload/{bucket_id}
                   │ file = resume.pdf
                   ▼
              FastAPI API
                   │
                   ├── Validate bucket exists
                   ├── Receive uploaded bytes
                   └── Delegate to Storage Engine
                              │
                              ▼
                      Encoder Layer
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
         Split into Shards          Generate Parity
                │                           │
                └─────────────┬─────────────┘
                              ▼
                        Disk Manager
                              │
      ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
      ▼          ▼          ▼          ▼          ▼          ▼
    disk1      disk2      disk3      disk4      disk5      disk6
   data0      data1      data2      data3     parity0    parity1
                              │
                              ▼
                      Metadata Layer
                        (PostgreSQL)
                              │
                              ▼
                     Return Success Response
```

---

## Download Flow

```text
                Client

        GET /objects/{object_id}

                    │
                    ▼

              FastAPI API

                    │
                    ▼

          Query Metadata Layer

                    │
                    ▼

          Retrieve Shard Metadata

                    │
                    ▼

              Storage Engine

                    │

          Read Available Shards

                    │

     Recover Missing Shards if Needed

                    │
                    ▼

            Reconstruct Object

                    │
                    ▼

          Stream Bytes to Client
```

---

## Current Architecture

```text
                    Client
                       │
                       ▼
               ┌─────────────────┐
               │   FastAPI API   │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ Storage Engine  │
               └────────┬────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    Shard Manager  Erasure Engine  Disk Manager
         │              │              │
         └──────┬───────┴───────┬──────┘
                ▼               ▼
          Metadata Layer   Physical Disks
            PostgreSQL
```

---

## Storage Engine Responsibilities

* Receive uploaded bytes
* Split objects into shards
* Generate parity shards
* Distribute shards across multiple disks
* Read object shards from disk
* Recover missing shards using parity
* Reconstruct original objects
* Compute SHA-256 checksums
* Compute object sizes
* Return storage metadata to the API layer

---

## Metadata Layer Responsibilities

### Objects Table

* Object ID
* Bucket ID
* Object Name
* Object Size
* Object Checksum

### Object Shards Table

* Object ID
* Shard Index
* Disk Name
* File Path
* Parity Flag
* Shard Size

---

## Fault Tolerance Model

Lattice currently uses an experimental erasure-coding architecture:

```text
4 Data Shards + 2 Parity Shards
```

Example:

```text
disk1 -> data0
disk2 -> data1
disk3 -> data2
disk4 -> data3
disk5 -> parity0
disk6 -> parity1
```

Objects are reconstructed from shards during reads. Lost shards can be rebuilt from parity information.

---

## Current Features

* Bucket creation
* Bucket deletion
* Object upload
* Object download
* Bucket-wise object listing
* SHA-256 checksum generation
* Metadata persistence using PostgreSQL
* Multi-disk storage
* File sharding
* Parity generation
* Shard reconstruction
* Single-shard recovery
* Experimental erasure coding

---

## Planned Features

### Phase 3

* Streaming uploads
* Streaming downloads
* Redis metadata cache
* Deduplication using checksums
* Presigned URLs
* Object lifecycle management

### Phase 4

* Reed-Solomon erasure coding
* Automatic shard healing
* Background repair jobs
* Disk health monitoring
* Multipart uploads
* Object versioning
* Distributed storage nodes
* Cross-node replication
* S3-compatible API
* RAG-powered semantic file retrieval

```
```
