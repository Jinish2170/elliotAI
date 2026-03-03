import asyncio
import sys
import os
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from veritas.agents.security_agent import SecurityAgent

async def test_run():
    print("Starting Elliot Phase 12/13 Integration Test...")
    agent = SecurityAgent()
    
    # Simulate finding an onion link and a specific server header
    # We pass custom headers to trigger the VulnerabilityMapper
    result = await agent.analyze(
        url="https://syntharatechnologies.com",
        page_content="Check our mirrors at v2c7...onion for secure access.",
        headers={"Server": "Next.js"},
        use_tier_execution=True
    )
    
    print("\n[Analysis Results]")
    print(f"Target: {result.url}")
    print(f"Score: {result.composite_score:.2f}")
    
    if result.darknet_correlation:
        print(f"[OK] Darknet Intel: {result.darknet_correlation.get('threat_level')} (Score: {result.darknet_correlation.get('confidence')})")

    if result.vulnerability_intel:
        print(f"[OK] Vulnerability Intel: Found {result.vulnerability_intel.get('total_matches')} CVE matches for stack.")
        for vuln in result.vulnerability_intel.get('vulnerabilities', []):
            print(f"  - {vuln['cve']}: {vuln['title']} ({vuln['severity']})")

    if result.advisories:
        print(f"\n[OK] Exploitation Advisories: Generated {len(result.advisories)} remediation steps.")
        for adv in result.advisories:
            print(f"  - [{adv['priority']}] {adv['cve']}: {adv['remediation']}")

    if result.scenarios:
        print(f"\n[OK] Attack Scenarios: Generated {len(result.scenarios)} theoretical flows.")
        for scenario in result.scenarios:
            print(f"  - {scenario['title']} (CVE: {scenario['cve']})")
            for step in scenario['attack_flow']:
                print(f"    {step}")
            print(f"    Impact: {scenario['potential_impact']}")

    print("\nTest Complete.")

if __name__ == "__main__":
    asyncio.run(test_run())
