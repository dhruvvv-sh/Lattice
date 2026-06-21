# app/storage/save_original.py

from disk_manager import read_shard

data = read_shard("Sample.pdf", 2)

with open("original_part2.bin", "wb") as f:
    f.write(data)

print("Saved original shard")