import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import chromadb
from chromadb.config import Settings
import numpy as np
from datetime import datetime
import json

from ..models import (
    DocumentMetadata, TextChunk, ImageData, AudioSegment as AudioSegmentModel,
    ModalityType, SearchResult
)
from ..config import settings

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=settings.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collection names for different modalities
        self.collections = {
            ModalityType.TEXT: "text_embeddings",
            ModalityType.DOCUMENT: "document_embeddings", 
            ModalityType.IMAGE: "image_embeddings",
            ModalityType.AUDIO: "audio_embeddings"
        }
        
        # Initialize collections
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections for each modality."""
        for modality, collection_name in self.collections.items():
            try:
                # Create or get collection
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"modality": modality.value}
                )
                logger.info(f"Initialized collection: {collection_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize collection {collection_name}: {e}")
    
    async def store_document_metadata(self, metadata: DocumentMetadata):
        """Store document metadata."""
        try:
            # Store in a separate metadata collection
            metadata_collection = self.client.get_or_create_collection("document_metadata")
            
            metadata_dict = metadata.dict()
            # Convert datetime to string for storage
            metadata_dict['upload_timestamp'] = metadata.upload_timestamp.isoformat()
            
            # ChromaDB only accepts str, int, float, bool for metadata
            # Convert or remove unsupported types
            clean_metadata = {}
            for key, value in metadata_dict.items():
                if value is None:
                    continue
                elif isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    # Convert list to comma-separated string
                    clean_metadata[key] = ','.join(str(v) for v in value) if value else ''
                elif isinstance(value, dict):
                    # Convert dict to JSON string
                    clean_metadata[key] = json.dumps(value)
                else:
                    # Convert other types to string
                    clean_metadata[key] = str(value)
            
            metadata_collection.add(
                ids=[metadata.id],
                metadatas=[clean_metadata],
                documents=[f"{metadata.filename} - {metadata.modality_type.value}"]
            )
            
            logger.info(f"Stored metadata for document: {metadata.filename}")
            
        except Exception as e:
            logger.error(f"Failed to store document metadata: {e}")
    
    async def store_text_chunks(self, chunks: List[TextChunk]):
        """Store text chunks with embeddings."""
        if not chunks:
            return
        
        try:
            collection = self.client.get_collection(self.collections[ModalityType.DOCUMENT])
            
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for chunk in chunks:
                if chunk.embedding_vector:
                    ids.append(chunk.id)
                    embeddings.append(chunk.embedding_vector)
                    documents.append(chunk.content)
                    
                    metadata = {
                        'document_id': chunk.document_id,
                        'chunk_index': chunk.chunk_index,
                        'page_number': chunk.page_number,
                        'modality_type': ModalityType.DOCUMENT.value,
                        'content_type': 'text_chunk'
                    }
                    metadata.update(chunk.metadata)
                    metadatas.append(metadata)
            
            if ids:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                
                logger.info(f"Stored {len(ids)} text chunks")
            
        except Exception as e:
            logger.error(f"Failed to store text chunks: {e}")
    
    async def store_image_data(self, image_data: ImageData):
        """Store image data with embeddings."""
        if not image_data or not image_data.embedding_vector:
            return
        
        try:
            collection = self.client.get_collection(self.collections[ModalityType.IMAGE])
            
            metadata = {
                'document_id': image_data.document_id,
                'image_path': image_data.image_path,
                'thumbnail_path': image_data.thumbnail_path or '',
                'width': image_data.width,
                'height': image_data.height,
                'has_text': bool(image_data.extracted_text),
                'modality_type': ModalityType.IMAGE.value,
                'content_type': 'image'
            }
            metadata.update(image_data.metadata)
            
            # Use extracted text as document content, fallback to filename
            document_content = image_data.extracted_text or f"Image: {image_data.image_path}"
            
            collection.add(
                ids=[image_data.id],
                embeddings=[image_data.embedding_vector],
                documents=[document_content],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored image data: {image_data.image_path}")
            
        except Exception as e:
            logger.error(f"Failed to store image data: {e}")
    
    async def store_audio_segments(self, segments: List[AudioSegmentModel]):
        """Store audio segments with embeddings."""
        if not segments:
            return
        
        try:
            collection = self.client.get_collection(self.collections[ModalityType.AUDIO])
            
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for segment in segments:
                if segment.embedding_vector and segment.transcript.strip():
                    ids.append(segment.id)
                    embeddings.append(segment.embedding_vector)
                    documents.append(segment.transcript)
                    
                    # Clean metadata - remove any lists or complex objects
                    cleaned_segment_metadata = {}
                    for key, value in segment.metadata.items():
                        if value is None:
                            continue
                        elif isinstance(value, (str, int, float, bool)):
                            cleaned_segment_metadata[key] = value
                        elif isinstance(value, list):
                            # Skip lists (like word-level timestamps)
                            continue
                        elif isinstance(value, dict):
                            # Convert dict to JSON string
                            cleaned_segment_metadata[key] = json.dumps(value)
                        else:
                            cleaned_segment_metadata[key] = str(value)
                    
                    metadata = {
                        'document_id': segment.document_id,
                        'start_timestamp': segment.start_timestamp,
                        'end_timestamp': segment.end_timestamp,
                        'confidence': segment.confidence or 0.0,
                        'speaker': segment.speaker or 'unknown',
                        'modality_type': ModalityType.AUDIO.value,
                        'content_type': 'audio_transcript'
                    }
                    metadata.update(cleaned_segment_metadata)
                    metadatas.append(metadata)
            
            if ids:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                
                logger.info(f"Stored {len(ids)} audio segments")
            
        except Exception as e:
            logger.error(f"Failed to store audio segments: {e}")
    
    async def search_by_text(self, query_text: str, query_embedding: List[float], 
                           modality_filters: Optional[List[ModalityType]] = None,
                           max_results: int = 10) -> List[SearchResult]:
        """Search across all modalities using text query."""
        all_results = []
        
        # Determine which collections to search
        search_collections = []
        if not modality_filters:
            search_collections = list(self.collections.items())
        else:
            search_collections = [(modality, name) for modality, name in self.collections.items() 
                                if modality in modality_filters]
        
        for modality, collection_name in search_collections:
            try:
                collection = self.client.get_collection(collection_name)
                
                # Perform similarity search
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max_results,
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Convert to SearchResult objects
                for i, (doc_id, document, metadata, distance) in enumerate(zip(
                    results['ids'][0],
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to similarity score (1 - normalized distance)
                    similarity_score = max(0, 1 - distance)
                    
                    search_result = SearchResult(
                        id=doc_id,
                        document_id=metadata.get('document_id', ''),
                        content=document,
                        modality_type=modality,
                        relevance_score=similarity_score,
                        metadata=metadata,
                        source_reference=self._create_source_reference(metadata),
                        page_number=metadata.get('page_number'),
                        timestamp=metadata.get('start_timestamp')
                    )
                    
                    all_results.append(search_result)
                    
            except Exception as e:
                logger.warning(f"Search failed for collection {collection_name}: {e}")
        
        # Sort by relevance score and return top results
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_results[:max_results]
    
    async def search_by_image(self, image_embedding: List[float], 
                            max_results: int = 10) -> List[SearchResult]:
        """Search for similar images."""
        try:
            collection = self.client.get_collection(self.collections[ModalityType.IMAGE])
            
            results = collection.query(
                query_embeddings=[image_embedding],
                n_results=max_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_results = []
            for doc_id, document, metadata, distance in zip(
                results['ids'][0],
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            ):
                similarity_score = max(0, 1 - distance)
                
                search_result = SearchResult(
                    id=doc_id,
                    document_id=metadata.get('document_id', ''),
                    content=document,
                    modality_type=ModalityType.IMAGE,
                    relevance_score=similarity_score,
                    metadata=metadata,
                    source_reference=self._create_source_reference(metadata)
                )
                
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []
    
    async def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get all content for a specific document."""
        content = {
            'metadata': None,
            'text_chunks': [],
            'images': [],
            'audio_segments': []
        }
        
        try:
            # Get document metadata
            metadata_collection = self.client.get_collection("document_metadata")
            metadata_results = metadata_collection.get(
                ids=[document_id],
                include=['metadatas']
            )
            
            if metadata_results['metadatas']:
                content['metadata'] = metadata_results['metadatas'][0]
            
            # Get content from each modality collection
            for modality, collection_name in self.collections.items():
                try:
                    collection = self.client.get_collection(collection_name)
                    results = collection.get(
                        where={"document_id": document_id},
                        include=['documents', 'metadatas']
                    )
                    
                    if modality == ModalityType.DOCUMENT:
                        content['text_chunks'] = results['documents'] or []
                    elif modality == ModalityType.IMAGE:
                        content['images'] = results['metadatas'] or []
                    elif modality == ModalityType.AUDIO:
                        content['audio_segments'] = list(zip(
                            results['documents'] or [],
                            results['metadatas'] or []
                        ))
                        
                except Exception as e:
                    logger.warning(f"Failed to get content from {collection_name}: {e}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to get document content: {e}")
            return content
    
    def _create_source_reference(self, metadata: Dict[str, Any]) -> str:
        """Create a human-readable source reference."""
        content_type = metadata.get('content_type', 'unknown')
        
        if content_type == 'text_chunk':
            page = metadata.get('page_number')
            if page:
                return f"Document page {page}"
            return f"Document chunk {metadata.get('chunk_index', 0)}"
            
        elif content_type == 'image':
            path = metadata.get('image_path', '')
            filename = path.split('/')[-1] if path else 'image'
            return f"Image: {filename}"
            
        elif content_type == 'audio_transcript':
            start_time = metadata.get('start_timestamp', 0)
            end_time = metadata.get('end_timestamp', 0)
            start_min = int(start_time // 60)
            start_sec = int(start_time % 60)
            return f"Audio transcript at {start_min}:{start_sec:02d}"
        
        return "Unknown source"
    
    async def delete_document(self, document_id: str):
        """Delete all data associated with a document."""
        try:
            # Delete from metadata collection
            metadata_collection = self.client.get_collection("document_metadata")
            try:
                metadata_collection.delete(ids=[document_id])
            except:
                pass
            
            # Delete from all modality collections
            for modality, collection_name in self.collections.items():
                try:
                    collection = self.client.get_collection(collection_name)
                    collection.delete(where={"document_id": document_id})
                except Exception as e:
                    logger.warning(f"Failed to delete from {collection_name}: {e}")
            
            logger.info(f"Deleted document: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database."""
        stats = {}
        
        try:
            for modality, collection_name in self.collections.items():
                try:
                    collection = self.client.get_collection(collection_name)
                    count = collection.count()
                    stats[modality.value] = count
                except:
                    stats[modality.value] = 0
            
            # Get total documents
            try:
                metadata_collection = self.client.get_collection("document_metadata")
                stats['total_documents'] = metadata_collection.count()
            except:
                stats['total_documents'] = 0
                
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
        
        return stats