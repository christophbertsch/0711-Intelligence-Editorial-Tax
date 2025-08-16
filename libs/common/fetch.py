import requests
import hashlib
from typing import Tuple, Dict
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time

class RobotChecker:
    """Check robots.txt compliance."""
    
    def __init__(self):
        self._cache = {}
    
    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self._cache:
            robots_url = urljoin(base_url, "/robots.txt")
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self._cache[base_url] = rp
            except:
                # If robots.txt can't be fetched, assume allowed
                self._cache[base_url] = None
        
        rp = self._cache[base_url]
        if rp is None:
            return True
        
        return rp.can_fetch(user_agent, url)

robot_checker = RobotChecker()

def fetch_url(url: str, respect_robots: bool = True, user_agent: str = "EditorialEngine/1.0") -> Tuple[str, Dict]:
    """Fetch URL content with robots.txt compliance."""
    
    if respect_robots and not robot_checker.can_fetch(url, user_agent):
        raise ValueError(f"Robots.txt disallows fetching {url}")
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Add delay to be respectful
    time.sleep(1)
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    return response.text, dict(response.headers)

def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()