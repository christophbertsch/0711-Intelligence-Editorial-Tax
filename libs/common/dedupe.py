import hashlib
from typing import Dict, Any, Set
from .extract import canonicalize_url
from .fetch import compute_content_hash

# In-memory cache for demonstration - in production use Redis
_seen_hashes: Set[str] = set()
_seen_urls: Set[str] = set()

def canonicalize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Canonicalize document by normalizing URL and computing content hash."""
    canonical_url = canonicalize_url(doc['url'])
    content_hash = compute_content_hash(doc['text'])
    
    return {
        **doc,
        'canonical_url': canonical_url,
        'content_hash': content_hash
    }

def is_duplicate(doc: Dict[str, Any]) -> bool:
    """Check if document is a duplicate based on URL or content hash."""
    canonical_url = doc.get('canonical_url', doc['url'])
    content_hash = doc.get('content_hash')
    
    # Check URL duplicate
    if canonical_url in _seen_urls:
        return True
    
    # Check content duplicate
    if content_hash and content_hash in _seen_hashes:
        return True
    
    # Mark as seen
    _seen_urls.add(canonical_url)
    if content_hash:
        _seen_hashes.add(content_hash)
    
    return False

def compute_similarity_hash(text: str, num_hashes: int = 128) -> str:
    """Compute MinHash for near-duplicate detection."""
    # Simple implementation - in production use datasketch library
    words = text.lower().split()
    shingles = set()
    
    # Create 3-word shingles
    for i in range(len(words) - 2):
        shingle = ' '.join(words[i:i+3])
        shingles.add(shingle)
    
    # Compute hash
    hash_values = []
    for shingle in shingles:
        hash_val = hash(shingle) % (2**32)
        hash_values.append(hash_val)
    
    # Take minimum hashes
    hash_values.sort()
    min_hashes = hash_values[:num_hashes] if len(hash_values) >= num_hashes else hash_values
    
    return hashlib.md5(str(min_hashes).encode()).hexdigest()