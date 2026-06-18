#structure flow
Client
   │
   │ POST /objects/upload/1
   │ file = resume.pdf #example
   ▼
FastAPI
   │
   ├── Check bucket 1 exists
   ├── Create storage/bucket_1 if needed
   ├── Save resume.pdf to disk
   ├── Calculate file size
   ├── Calculate checksum
   ├── Save metadata in PostgreSQL
   └── Return success

#Thought process:
Client
                   │
                   ▼
          ┌─────────────────┐
          │   FastAPI API   │
          └─────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
   Metadata Layer      Storage Engine
   (PostgreSQL)         
         │                   │
         ▼                   ▼
    Bucket/Object       Read & Write
      metadata           actual bytes

#current requirements:
-Receive bytes
-Decide where to store them
-Write them to disk
-Read them back later
-Delete them when requested