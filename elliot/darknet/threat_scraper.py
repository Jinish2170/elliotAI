"""
Multi-Source Threat Intel Scraper for .onion addresses.
Phase 12-02: Onion URL Validator and Threat Scraper.

This module provides:
- Automated uptime checking for .onion services
- Page title and header extraction via TOR
- Darknet marketplace classification based on live content
- Security header analysis (CSP, HSTS, X-Frame-Options) for onion services
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .tor_client import TORClient
from .onion_detector import OnionDetector, MarketplaceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("elliot.darknet.scraper")

class DarknetThreatScraper:
    """Scraper for darknet threat intelligence gathering."""
    
    def __init__(self, proxy_url: str = "socks5h://127.0.0.1:9050"):
        self.proxy_url = proxy_url
        self.detector = OnionDetector()
        
    async def audit_onion(self, onion_url: str) -> Dict[str, Any]:
        """Perform a basic security and content audit of an onion service."""
        if not self.detector.validate_onion(onion_url):
            return {"url": onion_url, "status": "invalid", "error": "Malformed onion address"}
            
        # Ensure protocol is present
        target_url = onion_url if onion_url.startswith("http") else f"http://{onion_url}"
        
        result = {
            "url": onion_url,
            "timestamp": datetime.now().isoformat(),
            "online": False,
            "title": None,
            "marketplace_type": "unknown",
            "security_score": 0,
            "headers": {},
            "error": None
        }
        
        async with TORClient(proxy_url=self.proxy_url) as tor:
            # Check connection first
            if not await tor.check_connection():
                result["error"] = "TOR proxy unreachable"
                return result
                
            response = await tor.get(target_url, timeout=45)
            
            if response["error"]:
                result["error"] = response["error"]
                return result
                
            result["online"] = True
            result["status_code"] = response["status"]
            result["headers"] = response["headers"]
            
            # Extract content if successful
            if response["text"]:
                # Extract title
                import re
                title_match = re.search(r'<title>(.*?)</title>', response["text"], re.IGNORECASE)
                if title_match:
                    result["title"] = title_match.group(1).strip()
                
                # Classify marketplace
                result["marketplace_type"] = self.detector.classify_marketplace(
                    onion_url, response["text"]
                ).value
                
                # Calculate basic security score based on headers
                headers = response["headers"]
                score = 0
                if "Content-Security-Policy" in headers: score += 25
                if "X-Frame-Options" in headers: score += 25
                if "X-Content-Type-Options" in headers: score += 25
                if "Referrer-Policy" in headers: score += 25
                result["security_score"] = score

        return result

    async def batch_audit(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Run parallel audits on a list of onion URLs."""
        tasks = [self.audit_onion(url) for url in urls]
        return await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Quick standalone test
    async def test():
        scraper = DarknetThreatScraper()
        # Test with a known reliable v3 directory or local proxy
        # Since we can't hit live darknet from here reliably, we'd mock or test proxy connectivity
        print("[*] Checking TOR connectivity...")
        async with TORClient() as tor:
            is_up = await tor.check_connection()
            print(f"[*] TOR status: {'ONLINE' if is_up else 'OFFLINE'}")

    asyncio.run(test())
