# app/storage/check_hash.py

import hashlib


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


print("Original :", sha("original_part2.bin"))
print("Recovered:", sha("recovered_part2.bin"))