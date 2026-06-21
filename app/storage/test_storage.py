from pathlib import Path

from shard_manager import split_bytes
from disk_manager import write_shard

pdf_path = Path(__file__).parent / "Sample.pdf"

print("Reading:", pdf_path)

with open(pdf_path, "rb") as f:
    data = f.read()

shards = split_bytes(data, 4)

for idx, shard in enumerate(shards):
    path = write_shard("Sample.pdf", idx, shard)
    print(f"Stored shard {idx} -> {path}")