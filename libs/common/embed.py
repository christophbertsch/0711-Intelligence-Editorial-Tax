from typing import List
import openai
import os

def embed_chunks(chunks: List[str], model: str = "text-embedding-ada-002") -> List[List[float]]:
    """Generate embeddings for text chunks."""
    
    if not chunks:
        return []
    
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response = client.embeddings.create(
            model=model,
            input=chunks
        )
        
        return [embedding.embedding for embedding in response.data]
    
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Return zero vectors as fallback
        return [[0.0] * 1536 for _ in chunks]  # Ada-002 has 1536 dimensions