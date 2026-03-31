import asyncio
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from veritas.core.orchestrator import VeritasOrchestrator

async def main():
    print("Starting deep forensic audit of example.com")
    orchestrator = VeritasOrchestrator()
    result = await orchestrator.audit("https://example.com", tier="deep_forensic")
    print(f"Investigated URLs: {result.get('investigated_urls')}")
    print(f"Scout Results len: {len(result.get('scout_results', []))}")
    print(f"Status: {result.get('status')}")

if __name__ == "__main__":
    asyncio.run(main())