import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from PIL import Image

from ..models import (
    ModalityType, SearchResult, QueryRequest
)
from ..config import settings
from .vector_database import VectorDatabase
from ..ingestion.image_processor import ImageProcessor
from ..ingestion.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

class CrossModalRetrieval:
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.text_encoder = SentenceTransformer(settings.embedding_model)
        
        # Initialize CLIP for image-text cross-modal search
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model = SentenceTransformer('clip-ViT-B-32')
        
        # Initialize processors for cross-modal operations
        self.image_processor = ImageProcessor()
        self.audio_processor = AudioProcessor()
    
    async def search(self, query_request: QueryRequest) -> List[SearchResult]:
        """Unified search across all modalities."""
        query = query_request.query
        modality_filters = query_request.modality_filters
        max_results = query_request.max_results
        
        try:
            # Generate text embedding for the query
            text_embedding = self.text_encoder.encode([query], convert_to_numpy=True)[0]
            
            # Perform cross-modal search
            results = []
            
            # 1. Text-to-Text search (documents and audio transcripts)
            if self._should_search_modality(ModalityType.DOCUMENT, modality_filters, query_request.include_documents):
                text_results = await self.vector_db.search_by_text(
                    query, text_embedding.tolist(), 
                    [ModalityType.DOCUMENT], 
                    max_results
                )
                results.extend(text_results)
            
            if self._should_search_modality(ModalityType.AUDIO, modality_filters, query_request.include_audio):
                audio_results = await self.vector_db.search_by_text(
                    query, text_embedding.tolist(),
                    [ModalityType.AUDIO],
                    max_results
                )
                results.extend(audio_results)
            
            # 2. Text-to-Image search using CLIP
            if self._should_search_modality(ModalityType.IMAGE, modality_filters, query_request.include_images):
                image_results = await self._search_images_by_text(query, max_results)
                results.extend(image_results)
            
            # Rank and filter results
            ranked_results = await self._rank_and_filter_results(results, query, max_results)
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def search_by_image(self, image_path: str, max_results: int = 10) -> List[SearchResult]:
        """Search using an uploaded image."""
        try:
            # Generate image embedding
            image = Image.open(image_path).convert('RGB')
            image_embedding = await self.image_processor._generate_image_embedding(image)
            
            # Search for similar images
            image_results = await self.vector_db.search_by_image(image_embedding, max_results)
            
            # Also extract text from the query image and search text content
            extracted_text = await self.image_processor._extract_text_from_image(image_path)
            
            if extracted_text and extracted_text.strip():
                text_results = await self.search(QueryRequest(
                    query=extracted_text,
                    max_results=max_results//2
                ))
                
                # Combine results
                combined_results = image_results + text_results
                return await self._rank_and_filter_results(combined_results, extracted_text, max_results)
            
            return image_results
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []
    
    async def search_by_audio_content(self, query_text: str, max_results: int = 10) -> List[SearchResult]:
        """Search specifically in audio content."""
        try:
            text_embedding = self.text_encoder.encode([query_text], convert_to_numpy=True)[0]
            
            results = await self.vector_db.search_by_text(
                query_text, text_embedding.tolist(),
                [ModalityType.AUDIO],
                max_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Audio content search failed: {e}")
            return []
    
    async def _search_images_by_text(self, query: str, max_results: int) -> List[SearchResult]:
        """Search images using text query via CLIP."""
        try:
            # Encode text query with CLIP using sentence-transformers
            text_embedding = self.clip_model.encode(query, convert_to_numpy=True).flatten().tolist()
            
            # Search in image collection
            results = await self.vector_db.search_by_image(text_embedding, max_results)
            
            return results
            
        except Exception as e:
            logger.error(f"CLIP image search failed: {e}")
            return []
    
    async def find_cross_references(self, document_id: str, content: str) -> List[SearchResult]:
        """Find cross-references to content across all modalities."""
        try:
            # Generate embeddings for the content
            text_embedding = self.text_encoder.encode([content], convert_to_numpy=True)[0]
            
            # Search across all modalities
            results = await self.vector_db.search_by_text(
                content, text_embedding.tolist(),
                modality_filters=None,  # Search all modalities
                max_results=20
            )
            
            # Filter out results from the same document
            cross_references = [r for r in results if r.document_id != document_id]
            
            return cross_references[:10]  # Return top 10 cross-references
            
        except Exception as e:
            logger.error(f"Cross-reference search failed: {e}")
            return []
    
    async def find_temporal_connections(self, timestamp: float, window_minutes: int = 30) -> List[SearchResult]:
        """Find content created around the same time."""
        try:
            # This would require storing and indexing timestamps
            # For now, return empty list - could be implemented with metadata filtering
            logger.info(f"Temporal search for timestamp {timestamp} ± {window_minutes} minutes")
            return []
            
        except Exception as e:
            logger.error(f"Temporal search failed: {e}")
            return []
    
    async def _rank_and_filter_results(self, results: List[SearchResult], 
                                     query: str, max_results: int) -> List[SearchResult]:
        """Rank and filter search results for relevance."""
        try:
            # Remove duplicates based on content
            seen_content = set()
            unique_results = []
            
            for result in results:
                content_hash = hash(result.content[:100])  # Hash first 100 chars
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)
            
            # Sort by relevance score
            unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Apply additional ranking based on content quality
            ranked_results = []
            for result in unique_results:
                # Boost score for longer, more detailed content
                length_boost = min(1.1, 1 + len(result.content) / 10000)
                
                # Boost score for content with specific metadata
                metadata_boost = 1.0
                if result.page_number:
                    metadata_boost += 0.05
                if result.timestamp is not None:
                    metadata_boost += 0.05
                
                # Apply boosts
                result.relevance_score *= length_boost * metadata_boost
                
                # Ensure score doesn't exceed 1.0
                result.relevance_score = min(1.0, result.relevance_score)
                
                ranked_results.append(result)
            
            # Sort again after boosting
            ranked_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return ranked_results[:max_results]
            
        except Exception as e:
            logger.error(f"Result ranking failed: {e}")
            return results[:max_results]
    
    def _should_search_modality(self, modality: ModalityType, 
                              modality_filters: Optional[List[ModalityType]], 
                              include_flag: bool) -> bool:
        """Determine if a modality should be searched."""
        if not include_flag:
            return False
        
        if modality_filters:
            return modality in modality_filters
        
        return True
    
    async def get_context_for_rag(self, query: str, max_context_items: int = 5) -> List[Dict[str, Any]]:
        """Get contextual information for RAG system."""
        try:
            # Search for relevant content
            query_request = QueryRequest(
                query=query,
                max_results=max_context_items * 2  # Get more results to filter
            )
            
            search_results = await self.search(query_request)
            
            # Convert to context format for RAG
            context_items = []
            for result in search_results[:max_context_items]:
                context_item = {
                    'content': result.content,
                    'source': result.source_reference,
                    'modality': result.modality_type.value,
                    'relevance_score': result.relevance_score,
                    'metadata': {
                        'document_id': result.document_id,
                        'page_number': result.page_number,
                        'timestamp': result.timestamp,
                        **result.metadata
                    }
                }
                context_items.append(context_item)
            
            return context_items
            
        except Exception as e:
            logger.error(f"Failed to get RAG context: {e}")
            return []

class SemanticAnalyzer:
    """Advanced semantic analysis for better retrieval."""
    
    def __init__(self):
        self.text_encoder = SentenceTransformer(settings.embedding_model)
    
    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query intent to improve search strategy."""
        intent = {
            'query_type': 'general',
            'temporal_references': [],
            'modality_hints': [],
            'entity_mentions': [],
            'complexity': 'simple'
        }
        
        query_lower = query.lower()
        
        # Detect query types
        if any(word in query_lower for word in ['show', 'display', 'image', 'picture', 'photo']):
            intent['modality_hints'].append(ModalityType.IMAGE)
        
        if any(word in query_lower for word in ['audio', 'recording', 'transcript', 'said', 'mentioned']):
            intent['modality_hints'].append(ModalityType.AUDIO)
        
        if any(word in query_lower for word in ['document', 'text', 'page', 'write', 'written']):
            intent['modality_hints'].append(ModalityType.DOCUMENT)
        
        # Detect temporal references
        temporal_words = ['yesterday', 'today', 'last week', 'recently', 'ago', 'before', 'after']
        for word in temporal_words:
            if word in query_lower:
                intent['temporal_references'].append(word)
        
        # Assess complexity
        if len(query.split()) > 10 or '?' in query:
            intent['complexity'] = 'complex'
        
        return intent
    
    async def expand_query(self, query: str) -> List[str]:
        """Generate expanded queries for better retrieval."""
        expanded_queries = [query]
        
        # Simple synonym expansion (in practice, would use a more sophisticated approach)
        synonyms = {
            'document': ['file', 'paper', 'report'],
            'image': ['picture', 'photo', 'screenshot'],
            'audio': ['recording', 'speech', 'voice'],
            'find': ['search', 'locate', 'get']
        }
        
        words = query.lower().split()
        for word in words:
            if word in synonyms:
                for synonym in synonyms[word]:
                    expanded_query = query.lower().replace(word, synonym)
                    expanded_queries.append(expanded_query)
        
        return expanded_queries[:3]  # Limit to 3 variations