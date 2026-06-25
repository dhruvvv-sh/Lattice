# shard_manager.py

import math


def split_bytes(data: bytes, num_shards=4):
    shard_size = math.ceil(len(data) / num_shards)

    shards = []

    for i in range(num_shards):
        start = i * shard_size
        end = start + shard_size

        shard = data[start:end]

        if len(shard) < shard_size:
            shard += b"\x00" * (shard_size - len(shard))

        shards.append(shard)

    return shards


def reconstruct_bytes(shards, original_size=None):
    data = b"".join(shards)

    if original_size is not None:
        return data[:original_size]

    return data
