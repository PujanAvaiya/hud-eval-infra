import json, hashlib

N = 1000
SHARDS = 20

with open("manifest.jsonl","w") as f:
    for i in range(N):
        f.write(json.dumps({"id": f"item-{i}"})+"\n")

buckets = [[] for _ in range(SHARDS)]
with open("manifest.jsonl") as f:
    for line in f:
        s = json.loads(line)
        h = int(hashlib.md5(s["id"].encode()).hexdigest(),16)
        buckets[h % SHARDS].append(s)

for i, b in enumerate(buckets):
    with open(f"shard-{i:03}.jsonl","w") as f:
        for s in b:
            f.write(json.dumps(s)+"\n")

print("wrote shards:", SHARDS)
