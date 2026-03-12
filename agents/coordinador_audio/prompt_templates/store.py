"""Store and search prompt templates from text files.

This module provides simple text-based search over prompt template files.
For production use, consider integrating with a vector database like Chroma.
"""
import os
from pathlib import Path
from typing import List, Dict, Any

# Directory containing template examples
TEMPLATES_DIR = Path(__file__).parent / "examples"

# In-memory cache for loaded templates
_template_cache: List[Dict[str, Any]] = []


def _load_templates() -> List[Dict[str, Any]]:
    """Load all template files from the examples directory."""
    global _template_cache
    
    if _template_cache:
        return _template_cache
    
    if not TEMPLATES_DIR.exists():
        return []
    
    templates = []
    for txt_file in TEMPLATES_DIR.glob("*.txt"):
        try:
            content = txt_file.read_text(encoding="utf-8")
            templates.append({
                "text": content,
                "source": str(txt_file.name),
                "metadata": {"filename": txt_file.name}
            })
        except Exception:
            continue
    
    _template_cache = templates
    return templates


def index_templates() -> int:
    """Reload and index all templates. Returns count of indexed templates.
    
    Returns:
        Number of templates indexed.
    """
    global _template_cache
    _template_cache = []
    return len(_load_templates())


def search(query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Search templates by simple keyword matching.
    
    Args:
        query: Search query string
        n_results: Maximum number of results to return
        
    Returns:
        List of matching templates with text, source, and metadata
    """
    templates = _load_templates()
    
    if not query.strip():
        # Return first n_results if no query
        return templates[:n_results]
    
    # Simple keyword matching (case-insensitive)
    query_terms = query.lower().split()
    scored_templates = []
    
    for template in templates:
        text_lower = template["text"].lower()
        # Score based on number of query terms found
        score = sum(1 for term in query_terms if term in text_lower)
        if score > 0:
            scored_templates.append((score, template))
    
    # Sort by score (descending) and return top n_results
    scored_templates.sort(key=lambda x: x[0], reverse=True)
    return [t[1] for t in scored_templates[:n_results]]
