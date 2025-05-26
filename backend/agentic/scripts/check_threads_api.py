#!/usr/bin/env python3
import asyncio
from azure.ai.agents.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

async def main():
    cred = DefaultAzureCredential()
    client = AIProjectClient(endpoint="test", credential=cred)
    print("Thread operations:", [m for m in dir(client.agents.threads) if not m.startswith('_')])
    await cred.close()
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())