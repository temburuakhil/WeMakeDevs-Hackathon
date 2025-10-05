from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from uuid import uuid4

class ModalityType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    NOTE = "note"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    file_path: str
    modality_type: ModalityType
    document_type: Optional[DocumentType] = None
    file_size: int
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    page_count: Optional[int] = None
    duration: Optional[float] = None  # For audio files
    dimensions: Optional[Dict[str, int]] = None  # For images
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class TextChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    start_timestamp: Optional[float] = None  # For audio
    end_timestamp: Optional[float] = None    # For audio
    embedding_vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ImageData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    image_path: str
    thumbnail_path: Optional[str] = None
    extracted_text: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
    width: int
    height: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AudioSegment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    transcript: str
    start_timestamp: float
    end_timestamp: float
    confidence: Optional[float] = None
    speaker: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResult(BaseModel):
    id: str
    document_id: str
    content: str
    modality_type: ModalityType
    relevance_score: float
    metadata: Dict[str, Any]
    source_reference: str
    page_number: Optional[int] = None
    timestamp: Optional[float] = None

class Citation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    number: int
    document_id: str
    content: str
    modality_type: ModalityType
    source_reference: str
    page_number: Optional[int] = None
    timestamp: Optional[float] = None
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    modality_filters: Optional[List[ModalityType]] = None
    max_results: int = Field(default=10, ge=1, le=50)
    include_images: bool = True
    include_audio: bool = True
    include_documents: bool = True

class RAGResponse(BaseModel):
    answer: str
    query: str
    citations: List[Citation]
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    retrieved_contexts: List[SearchResult]

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    modality_type: ModalityType
    processing_status: ProcessingStatus
    message: str