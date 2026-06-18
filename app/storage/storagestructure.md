# Lattice Storage Engine Architecture

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
                   ├── Delegate to Storage Engine
                   │
                   ▼
             Storage Engine
                   │
                   ├── Decide storage location
                   ├── Create bucket directory if needed
                   ├── Write file to disk
                   ├── Calculate SHA-256 checksum
                   ├── Calculate file size
                   └── Return storage metadata
                   │
                   ▼
            Metadata Layer
              (PostgreSQL)
                   │
                   ├── object_id
                   ├── bucket_id
                   ├── object_name
                   ├── file_path
                   ├── checksum
                   └── size
                   │
                   ▼
            Return Success Response
```

---

# Download Flow

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

Retrieve file_path

                │

                ▼

        Storage Engine

                │

Open file from disk

                │

                ▼

 Stream bytes to client
```

---

# Listing Objects

```text
            Client

GET /buckets/{bucket_id}/objects

                │

                ▼

        FastAPI API

                │

                ▼

      Query Metadata Layer

                │

                ▼

Return object metadata

(id, name, size)

                │

                ▼

            JSON Response
```

---

# Current Architecture

```text
                    Client
                       │
                       ▼
               ┌─────────────────┐
               │   FastAPI API   │
               └────────┬────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
      Metadata Layer         Storage Engine
      (PostgreSQL)            (Filesystem)
            │                       │
            ▼                       ▼
   Object metadata          Physical file bytes
```

---

# Storage Engine Responsibilities

* Receive uploaded bytes
* Decide physical storage location
* Create bucket directories
* Write files to disk
* Read files from disk
* Delete physical files
* Compute SHA-256 checksums
* Compute object size
* Return storage metadata to the API layer

---

# Metadata Layer Responsibilities

* Generate object IDs
* Map objects to buckets
* Store object names
* Store file paths
* Store checksums
* Store file sizes
* Support object lookup by ID
* Support listing objects by bucket

---

# Current Features

* Bucket creation
* Bucket deletion
* Object upload
* Object download by ID
* Bucket-wise object listing
* SHA-256 checksum generation
* Metadata persistence
* Filesystem-backed storage engine

---

# Planned Features

## Phase 2

* Object deletion
* Streaming uploads
* Streaming downloads
* Pydantic response filtering

## Phase 3

* Deduplication using checksums
* Presigned URLs
* Redis metadata cache
* Object lifecycle management

## Phase 4

* Multipart uploads
* Object versioning
* Replication
* Erasure coding
* Distributed storage nodes
* Full S3-compatible API

```
```
