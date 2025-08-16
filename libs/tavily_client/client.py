import os
import requests
from typing import List, Dict, Any, Tuple

class TavilyClient:
    """Client for Tavily search and extract APIs."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"
    
    def search(self, query: str, max_results: int = 10, search_depth: str = "basic", 
               include_domains: List[str] = None, exclude_domains: List[str] = None,
               time_range: str = None) -> List[Dict[str, Any]]:
        """Search web content using Tavily."""
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": False,
            "include_raw_content": True
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        if time_range:
            payload["time_range"] = time_range
        
        response = requests.post(f"{self.base_url}/search", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("results", [])
    
    def extract(self, urls: List[str], extract_depth: str = "basic") -> List[Dict[str, Any]]:
        """Extract content from URLs using Tavily."""
        
        payload = {
            "api_key": self.api_key,
            "urls": urls,
            "extract_depth": extract_depth
        }
        
        response = requests.post(f"{self.base_url}/extract", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("results", [])

# Global client instance
_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable required")
        _client = TavilyClient(api_key)
    return _client

def tavily_search(query: str, max_results: int = 25, freshness: str = "30d", 
                  allow: List[str] = None, deny: List[str] = None) -> List[Dict[str, Any]]:
    """Search using Tavily with freshness and domain filtering."""
    
    # Convert freshness to time_range
    time_range_map = {
        "1d": "day", "7d": "week", "30d": "month", "365d": "year"
    }
    time_range = time_range_map.get(freshness, "month")
    
    return _get_client().search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_domains=allow,
        exclude_domains=deny,
        time_range=time_range
    )

def tavily_extract(urls: List[str]) -> List[Dict[str, Any]]:
    """Extract content from URLs using Tavily."""
    return _get_client().extract(urls, extract_depth="advanced")

def corroborate_claims(claims: List[str], required: int = 2) -> Tuple[bool, List[Dict]]:
    """Corroborate claims using Tavily search."""
    
    all_citations = []
    verified_claims = 0
    
    for claim in claims:
        # Search for evidence of this claim
        results = tavily_search(claim, max_results=5)
        
        claim_citations = []
        for result in results:
            if result.get("content") and claim.lower() in result["content"].lower():
                claim_citations.append({
                    "claim": claim,
                    "url": result["url"],
                    "title": result.get("title", ""),
                    "snippet": result.get("content", "")[:200] + "..."
                })
        
        if len(claim_citations) >= required:
            verified_claims += 1
            all_citations.extend(claim_citations[:required])
    
    # Consider corroborated if at least 80% of claims are verified
    success = verified_claims >= len(claims) * 0.8
    
    return success, all_citations