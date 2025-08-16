import re
from typing import List

def chunk_by_headings(text: str, keep_headings: bool = True, target_tokens: int = 500) -> List[str]:
    """Chunk text by headings and target token count."""
    
    # Split by common heading patterns
    heading_pattern = r'(?m)^(?:#+ |={2,}|={2,}\n|\d+\.\s+|\w+\.\s+|[A-Z][A-Z\s]+:)'
    sections = re.split(heading_pattern, text)
    
    chunks = []
    current_chunk = ""
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        section_tokens = len(section) // 4
        current_tokens = len(current_chunk) // 4
        
        if current_tokens + section_tokens > target_tokens and current_chunk:
            # Save current chunk and start new one
            chunks.append(current_chunk.strip())
            current_chunk = section
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += "\n\n" + section
            else:
                current_chunk = section
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def chunk_by_sentences(text: str, target_tokens: int = 500, overlap_tokens: int = 50) -> List[str]:
    """Chunk text by sentences with overlap."""
    
    # Split into sentences
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_tokens = len(sentence) // 4
        current_tokens = len(current_chunk) // 4
        
        if current_tokens + sentence_tokens > target_tokens and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Create overlap
            overlap_sentences = []
            overlap_tokens = 0
            for prev_sentence in reversed(current_chunk.split('. ')):
                if overlap_tokens < overlap_tokens:
                    overlap_sentences.insert(0, prev_sentence)
                    overlap_tokens += len(prev_sentence) // 4
                else:
                    break
            
            current_chunk = '. '.join(overlap_sentences) + '. ' + sentence if overlap_sentences else sentence
        else:
            if current_chunk:
                current_chunk += ' ' + sentence
            else:
                current_chunk = sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks