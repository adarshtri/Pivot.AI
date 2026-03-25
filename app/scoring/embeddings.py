"""Semantic embeddings service using local fastembed (ONNX)."""

import logging
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Manages local text embeddings generation using fastembed."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        """Initialize the embedding model. This downloads the model on first run."""
        try:
            from fastembed import TextEmbedding
            # BAAI/bge-small-en-v1.5 is the default and yields 384-dimensional vectors
            self._model = TextEmbedding(model_name=model_name)
            logger.info("Initialized fastembed TextEmbedding model: %s", model_name)
        except ImportError:
            logger.error("fastembed package not installed. Run `pip install fastembed`")
            raise

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single string asynchronously.
        
        Runs the CPU-bound fastembed model in a background thread to prevent
        blocking the main FastAPI asyncio event loop.
        """
        if not text.strip():
            return []
            
        def _do_embed():
            embeddings_gen = self._model.embed([text])
            embeddings_list = list(embeddings_gen)
            if embeddings_list and len(embeddings_list) > 0:
                return embeddings_list[0].tolist()
            return []

        import asyncio
        try:
            return await asyncio.to_thread(_do_embed)
        except Exception as e:
            logger.error("Failed to generate embedding: %s", e)
            
        return []

    def compute_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors (0.0 to 1.0)."""
        if not vec1 or not vec2:
            return 0.0
            
        a = np.array(vec1)
        b = np.array(vec2)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        cos_sim = np.dot(a, b) / (norm_a * norm_b)
        
        # Scale cosine similarity from [-1, 1] to [0, 1]
        # Actually for BGE models, texts are usually positively correlated so it's mostly [0, 1]
        # We clamp it just in case.
        return max(0.0, min(1.0, float(cos_sim)))
