# app/storage/reconstruction.py

from shard_manager import reconstruct_bytes
from disk_manager import read_shard

shards = []

for i in range(4):
    shards.append(read_shard("Sample.pdf", i))

data = reconstruct_bytes(shards)

with open("restored.pdf", "wb") as f:
    f.write(data)

print("File reconstructed successfully!")