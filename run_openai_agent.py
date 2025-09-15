#!/usr/bin/env python3
import os, asyncio, hud
from hud.datasets import Task
from hud.agents import OperatorAgent
from hud.settings import settings

RUN_MODE = os.getenv("RUN_MODE", "local").lower()   # "local" or "remote"
IMAGE    = os.getenv("MY_ENV_IMAGE", "my_env:dev")  # local: my_env:dev; remote: docker.io/<you>/my_env:tag
MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TARGET   = int(os.getenv("MY_ENV_TARGET", "4"))
ACTS     = int(os.getenv("MY_ENV_ACTS", "10"))

def mcp_config():
    if RUN_MODE == "remote":
        return {"hud": {
            "url": "https://mcp.hud.so/v3/mcp",
            "headers": {
                "Authorization": f"Bearer {settings.api_key}",
                "Mcp-Image": IMAGE
            }
        }}
    # local: speak MCP over STDIO via docker
    return {"stdio": {"command": "docker", "args": ["run", "--rm", "-i", IMAGE]}}

PROMPT = f"""
TOOLS: setup, act, evaluate
Call tools ONLY and STOP after evaluate:
1) setup
2) act — repeat exactly {ACTS} times
3) evaluate with target={TARGET}
""".strip()

async def main():
    if RUN_MODE == "remote":
        assert settings.api_key, "Set HUD_API_KEY for remote runs"
    assert os.getenv("OPENAI_API_KEY"), "Set OPENAI_API_KEY (OpenAI model)"

    task = Task(
        prompt=PROMPT,
        mcp_config=mcp_config(),
        setup_tool={"name":"setup","arguments":{}},
        evaluate_tool={"name":"evaluate","arguments":{"target":TARGET}},
        allowed_tools=["setup","act","evaluate"],
    )

    agent = OperatorAgent(model=MODEL)
    with hud.trace(f"openai-{RUN_MODE}-{ACTS}acts-target{TARGET}"):
        result = await agent.run(task, max_steps=max(ACTS + 8, 24))
    print("Reward:", getattr(result, "reward", None))

if __name__ == "__main__":
    asyncio.run(main())
