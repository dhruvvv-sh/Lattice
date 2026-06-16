# Beacon
S3-compatible storage engine
---
#Architecture being used 
                AWS CLI
                     │
                     ▼
               FastAPI Server
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   PostgreSQL                 Redis Cache
(metadata/users)         (hot objects/cache)

                     │
                     ▼
            Object Storage Engine
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
      Disk 1                 Disk 2
#Folder Structure

lattice/

├── app/
│   ├── api/
│   ├── auth/
│   ├── buckets/
│   ├── objects/
│   ├── storage/
│   ├── metadata/
│   ├── replication/
│   ├── multipart/
│   ├── dedup/
│   ├── scheduler/
│   └── utils/
│
├── tests/
│
├── docker/
│
├── docs/
│
├── benchmarks/
│
├── scripts/
│
├── docker-compose.yml
│
└── README.md

#Database Schema:
id
email
password_hash
created_at
---
#Buckets:
id
owner_id
bucket_name
created_at
---
#Objects:
id
bucket_id
key
size
sha256
version
created_at
storage_path
---
