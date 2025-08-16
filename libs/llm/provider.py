import os
import json
from typing import Dict, Any, List, Tuple
from abc import ABC, abstractmethod
import openai
import anthropic

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        pass
    
    @abstractmethod
    def generate_json(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def generate_json(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        response = self.generate(prompt + "\n\nReturn valid JSON only.", max_tokens, 0.0)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from response: {response}")

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def generate_json(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        response = self.generate(prompt + "\n\nReturn valid JSON only.", max_tokens, 0.0)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from response: {response}")

def get_llm_provider() -> LLMProvider:
    """Get configured LLM provider."""
    provider_name = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        return OpenAIProvider(api_key)
    
    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
        return AnthropicProvider(api_key)
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")

# Convenience functions
_provider = None

def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_llm_provider()
    return _provider

def classify_json(text: str) -> Dict[str, Any]:
    """Classify document and return structured JSON."""
    prompt = f"""You are a strict document classifier. Output JSON only:
{{ "doc_type": one_of["guideline","ruling","article","faq","spec","datasheet"],
  "language": iso639-1,
  "audience": one_of["general","expert","legal"],
  "jurisdiction": null_or_string }}
Decide from the text below. No explanations.

Text:
{text[:2000]}"""
    
    return _get_provider().generate_json(prompt)

def ner_link(text: str, labels: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
    """Extract named entities and relationships."""
    prompt = f"""Extract named entities and relationships from this {labels.get('doc_type', 'document')}.

Return JSON with:
{{
  "entities": [
    {{"name": "entity_name", "type": "Statute|Case|Organization|Form|Concept", "confidence": 0.0-1.0}}
  ],
  "relationships": [
    {{"source": "entity1", "target": "entity2", "relation": "INTERPRETS|APPLIES|MAPS_TO|HARMONIZES", "confidence": 0.0-1.0}}
  ]
}}

Text:
{text[:3000]}"""
    
    result = _get_provider().generate_json(prompt)
    return result.get("entities", []), result.get("relationships", [])

def summarize_with_citations(text: str, labels: Dict[str, Any]) -> str:
    """Generate neutral abstract with citations."""
    language = labels.get('language', 'en')
    doc_type = labels.get('doc_type', 'document')
    
    prompt = f"""Write a neutral abstract (max 180 words) for this {doc_type}. 
{"Write in German" if language == 'de' else "Write in English"}.

- Include only facts from the text
- Add bracketed numeric citations [1], [2], ... for key claims
- Be objective and neutral

Text:
{text[:4000]}"""
    
    return _get_provider().generate(prompt, max_tokens=300)

def extract_claims(abstract: str) -> List[str]:
    """Extract atomic claims from abstract for fact-checking."""
    prompt = f"""Extract up to 10 atomic, verifiable claims from this abstract. 
Return as JSON array of strings. Each claim should be a single factual statement.

Abstract:
{abstract}"""
    
    result = _get_provider().generate_json(prompt)
    if isinstance(result, list):
        return result
    return result.get("claims", [])