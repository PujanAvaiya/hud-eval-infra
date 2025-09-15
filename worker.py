import os, asyncio, json, redis, hud
from hud.datasets import Task
from hud.agents import OperatorAgent
from hud.settings import settings

R = redis.Redis(host=os.getenv("REDIS_HOST","localhost"), port=6379, db=0)
QUEUE = os.getenv("QUEUE","hud_tasks")

def mcp_for(job):
    mode  = job.get("mode","remote")
    image = job["image"]
    if mode == "remote":
        return {"hud": {
            "url":"https://mcp.hud.so/v3/mcp",
            "headers":{"Authorization": f"Bearer {settings.api_key}","Mcp-Image": image}
        }}
    return {"stdio": {"command":"docker", "args":["run","--rm","-i", image]}}

async def run_job(job):
    target = int(job.get("target", 4))
    acts   = int(job.get("acts", 10))
    task = Task(
        prompt=f"setup; act x{acts}; evaluate target={target}",
        mcp_config=mcp_for(job),
        setup_tool={"name":"setup","arguments":{}},
        evaluate_tool={"name":"evaluate","arguments":{"target": target}},
        allowed_tools=["setup","act","evaluate"],
    )
    agent = OperatorAgent(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"))
    with hud.trace(f"batch-{job.get('mode','remote')}-{acts}-{target}"):
        res = await agent.run(task, max_steps=max(acts+8, 24))
    return float(getattr(res, "reward", 0.0))

async def main():
    if os.getenv("MODE","remote") == "remote":
        assert settings.api_key, "Set HUD_API_KEY"
    assert os.getenv("OPENAI_API_KEY"), "Set OPENAI_API_KEY"

    while True:
        raw = R.blpop(QUEUE, timeout=5)
        if not raw: 
            continue
        _, payload = raw
        job = json.loads(payload)
        try:
            reward = await run_job(job)
            R.rpush(job["result_key"], json.dumps({"status":"ok","reward": reward}))
        except Exception as e:
            R.rpush(job["result_key"], json.dumps({"status":"err","error": str(e)}))

if __name__ == "__main__":
    asyncio.run(main())
