import json, os, asyncio, hud
from hud.datasets import Task
from hud.agents import OperatorAgent
from hud.settings import settings

IMAGE  = os.getenv("IMAGE","docker.io/USER/my_env:0.1.1")
SHARD  = os.getenv("SHARD","shard-000.jsonl")
OUT    = os.getenv("OUT","results-000.jsonl")
TARGET = int(os.getenv("TARGET","4"))
ACTS   = int(os.getenv("ACTS","10"))

async def eval_one(idx):
    task = Task(
        prompt=f"setup; act x{ACTS}; evaluate target={TARGET}",
        mcp_config={"hud": {"url":"https://mcp.hud.so/v3/mcp",
            "headers":{"Authorization": f"Bearer {settings.api_key}","Mcp-Image": IMAGE}}},
        setup_tool={"name":"setup","arguments":{}},
        evaluate_tool={"name":"evaluate","arguments":{"target":TARGET}},
        allowed_tools=["setup","act","evaluate"],
    )
    agent = OperatorAgent(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"))
    with hud.trace(f"s-{os.path.basename(SHARD)}-{idx}"):
        res = await agent.run(task, max_steps=max(ACTS+8,24))
    return float(getattr(res,"reward",0.0))

async def main():
    assert settings.api_key and os.getenv("OPENAI_API_KEY")
    # resume support
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                d = json.loads(line); done.add(d["id"])
    out = open(OUT, "a")
    with open(SHARD) as f:
        items = [json.loads(l) for l in f]

    for i, item in enumerate(items):
        if item["id"] in done: 
            continue
        r = await eval_one(i)
        out.write(json.dumps({"id": item["id"], "reward": r})+"\n")
        out.flush()
    out.close()

if __name__ == "__main__":
    asyncio.run(main())
