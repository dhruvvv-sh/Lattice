# Reed-Solomon Storage Test Cases

These checks validate the current `4+2` Reed-Solomon erasure coding flow in
`app/storage/erasure.py`.

## Test Setup

Input data:

```text
b"abcdefghijklmnopqrstuvwxyz0123456789"
```

Shard layout:

```text
4 data shards + 2 parity shards
```

Generated shard sizes:

```text
data_size 36
data_shards 4 [9, 9, 9, 9]
parity_shards 2 [9, 9]
```

## Cases Ran

| Case | Missing Shards | Expected Result | Output |
| ---- | -------------- | --------------- | ------ |
| 1 | One data shard | Recover missing data shard | `case_1_single_data_missing ok` |
| 2 | One data shard and one parity shard | Recover all shards | `case_2_data_and_parity_missing ok` |
| 3 | Two data shards | Recover both data shards | `case_3_two_data_missing ok` |
| 4 | Two parity shards | Rebuild parity from complete data | `case_4_two_parity_missing ok` |
| 5 | Three total shards | Fail because `4+2` can recover only two erasures | `case_5_three_missing failed_as_expected Too many missing shards to recover` |
| 6 | Padded reconstruction | Trim reconstructed bytes to original size | `case_6_reconstruction_trim ok` |

## Full Output

```text
data_size 36
data_shards 4 [9, 9, 9, 9]
parity_shards 2 [9, 9]
case_1_single_data_missing ok
case_2_data_and_parity_missing ok
case_3_two_data_missing ok
case_4_two_parity_missing ok
case_5_three_missing failed_as_expected Too many missing shards to recover
case_6_reconstruction_trim ok
```

## Test Script

```python
from app.storage.shard_manager import split_bytes, reconstruct_bytes
from app.storage.erasure import generate_parity, recover_shards, recover_missing_shard

data = b"abcdefghijklmnopqrstuvwxyz0123456789"
shards = split_bytes(data, 4)
parity = generate_parity(shards)

print("data_size", len(data))
print("data_shards", len(shards), [len(s) for s in shards])
print("parity_shards", len(parity), [len(p) for p in parity])

assert recover_missing_shard([shards[0], shards[1], None, shards[3]], parity, 2) == shards[2]
print("case_1_single_data_missing ok")

recovered_data, recovered_parity = recover_shards(
    [shards[0], None, shards[2], shards[3]],
    [parity[0], None],
)
assert recovered_data == shards and recovered_parity == parity
print("case_2_data_and_parity_missing ok")

recovered_data, recovered_parity = recover_shards(
    [None, shards[1], None, shards[3]],
    parity,
)
assert recovered_data == shards and recovered_parity == parity
print("case_3_two_data_missing ok")

recovered_data, recovered_parity = recover_shards(shards, [None, None])
assert recovered_data == shards and recovered_parity == parity
print("case_4_two_parity_missing ok")

try:
    recover_shards([None, None, None, shards[3]], parity)
except ValueError as exc:
    print("case_5_three_missing failed_as_expected", str(exc))
else:
    raise AssertionError("expected failure")

assert reconstruct_bytes(shards, len(data)) == data
print("case_6_reconstruction_trim ok")
```
