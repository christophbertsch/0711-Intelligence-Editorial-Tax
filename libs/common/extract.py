import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import PyPDF2
import io
import requests

def extract_text(html: str, url: str) -> Dict[str, Any]:
    """Extract clean text from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
        element.decompose()
    
    # Extract title
    title_elem = soup.find('title')
    title = title_elem.get_text().strip() if title_elem else ""
    
    # Extract main content
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
    if main_content:
        text = main_content.get_text(separator=' ', strip=True)
    else:
        text = soup.get_text(separator=' ', strip=True)
    
    # Clean up text
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Extract metadata
    metadata = {}
    
    # Meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        if name and content:
            metadata[name] = content
    
    # Extract links
    links = []
    for link in soup.find_all('a', href=True):
        href = urljoin(url, link['href'])
        links.append({
            'url': href,
            'text': link.get_text().strip()
        })
    
    return {
        'title': title,
        'text': text,
        'metadata': metadata,
        'links': links,
        'url': url
    }

def extract_pdf_text(pdf_url: str) -> str:
    """Extract text from PDF URL."""
    response = requests.get(pdf_url, timeout=30)
    response.raise_for_status()
    
    pdf_file = io.BytesIO(response.content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    
    return text.strip()

def canonicalize_url(url: str) -> str:
    """Canonicalize URL by removing tracking parameters."""
    parsed = urlparse(url)
    
    # Remove common tracking parameters
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'wt_mc', 'wt_zmc', '_ga', '_gid'
    }
    
    if parsed.query:
        params = []
        for param in parsed.query.split('&'):
            if '=' in param:
                key = param.split('=')[0]
                if key not in tracking_params:
                    params.append(param)
        
        query = '&'.join(params) if params else ''
    else:
        query = ''
    
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}" + (f"?{query}" if query else "")