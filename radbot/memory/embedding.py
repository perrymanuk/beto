"""
Text embedding utilities for the Qdrant memory system.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingModel:
    """Data class for embedding model information."""
    name: str
    vector_size: int
    client: Any  # The actual embedding client instance


def get_embedding_model() -> EmbeddingModel:
    """
    Initialize and return the appropriate embedding model based on configuration.
    
    This function selects and initializes the embedding model client
    based on environment variables or configuration.
    
    Returns:
        EmbeddingModel: The configured embedding model
    """
    # Determine which embedding model to use based on environment variables
    embed_model = os.getenv("radbot_EMBED_MODEL", "gemini").lower()
    
    if embed_model == "gemini":
        return _initialize_gemini_embedding()
    elif embed_model == "sentence-transformers":
        return _initialize_sentence_transformers()
    else:
        logger.warning(f"Unknown embedding model '{embed_model}', falling back to Gemini")
        return _initialize_gemini_embedding()


def _initialize_gemini_embedding() -> EmbeddingModel:
    """
    Initialize the Gemini embedding model.
    
    Returns:
        EmbeddingModel: The initialized embedding model
    """
    try:
        # Import here to prevent global dependency
        import google.generativeai as genai
        
        # Configure the client with API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        # Return the model info
        return EmbeddingModel(
            name="gemini-embedding-001",
            vector_size=768,  # Gemini embeddings are 768-dimensional
            client=genai
        )
    except ImportError:
        logger.error("Failed to import google.generativeai. Please install with: pip install google-generativeai")
        raise


def _initialize_sentence_transformers() -> EmbeddingModel:
    """
    Initialize a sentence-transformers embedding model.
    
    Returns:
        EmbeddingModel: The initialized embedding model
    """
    try:
        # Import here to prevent global dependency
        from sentence_transformers import SentenceTransformer
        
        # Get the model name from environment or use default
        model_name = os.getenv("SENTENCE_TRANSFORMERS_MODEL", "all-MiniLM-L6-v2")
        
        # Load the model
        model = SentenceTransformer(model_name)
        
        # Return the model info
        return EmbeddingModel(
            name=model_name,
            vector_size=model.get_sentence_embedding_dimension(),
            client=model
        )
    except ImportError:
        logger.error("Failed to import sentence_transformers. Please install with: pip install sentence-transformers")
        raise


def embed_text(text: str, model: EmbeddingModel, is_query: bool = True, source: str = "agent_memory") -> List[float]:
    """
    Generate embedding vector for a text string.
    
    Args:
        text: The text to embed
        model: The embedding model to use
        is_query: Whether this is a query (True) or a document (False)
        source: The source system for the embedding ("agent_memory" or "crawl4ai")
        
    Returns:
        List of embedding vector values
    """
    try:
        if model.name.startswith("gemini"):
            # Gemini embedding
            if is_query:
                # For queries, use RETRIEVAL_QUERY without title
                result = model.client.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="RETRIEVAL_QUERY"
                )
            else:
                # For documents, use RETRIEVAL_DOCUMENT with title
                title = f"{source.replace('_', ' ').title()} Document"
                result = model.client.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="RETRIEVAL_DOCUMENT",
                    title=title
                )
            return result["embedding"]
        
        elif hasattr(model.client, 'encode'):
            # Sentence Transformers embedding
            embedding = model.client.encode(text)
            return embedding.tolist()
        
        else:
            logger.error(f"Unsupported embedding model: {model.name}")
            raise ValueError(f"Unsupported embedding model: {model.name}")
            
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        # Return a zero vector as fallback (in production, consider a more robust fallback)
        return [0.0] * model.vector_size