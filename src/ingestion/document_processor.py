import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

import PyPDF2
import pdfplumber
from docx import Document
from sentence_transformers import SentenceTransformer

from ..models import (
    DocumentMetadata, TextChunk, ModalityType, 
    DocumentType, ProcessingStatus
)
from ..config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    async def process_document(self, file_path: str, filename: str) -> DocumentMetadata:
        """Process a document and extract text with metadata."""
        try:
            # Determine document type
            doc_type = self._get_document_type(filename)
            file_size = os.path.getsize(file_path)
            
            # Create metadata
            metadata = DocumentMetadata(
                filename=filename,
                file_path=file_path,
                modality_type=ModalityType.DOCUMENT,
                document_type=doc_type,
                file_size=file_size,
                processing_status=ProcessingStatus.PROCESSING
            )
            
            # Extract text based on document type
            text_content = ""
            page_count = 0
            
            if doc_type == DocumentType.PDF:
                text_content, page_count = await self._extract_pdf_text(file_path)
            elif doc_type == DocumentType.DOCX:
                text_content, page_count = await self._extract_docx_text(file_path)
            elif doc_type == DocumentType.TXT:
                text_content = await self._extract_txt_text(file_path)
                page_count = 1
            
            metadata.page_count = page_count
            
            # Create text chunks
            chunks = await self._create_text_chunks(text_content, metadata.id)
            
            # Generate embeddings for chunks
            await self._generate_chunk_embeddings(chunks)
            
            metadata.processing_status = ProcessingStatus.COMPLETED
            logger.info(f"Successfully processed document: {filename}")
            
            return metadata, chunks
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            metadata.processing_status = ProcessingStatus.FAILED
            return metadata, []
    
    def _get_document_type(self, filename: str) -> DocumentType:
        """Determine document type from filename."""
        ext = Path(filename).suffix.lower()
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.doc': DocumentType.DOCX,
            '.txt': DocumentType.TXT
        }
        return type_mapping.get(ext, DocumentType.TXT)
    
    async def _extract_pdf_text(self, file_path: str) -> tuple[str, int]:
        """Extract text from PDF using pdfplumber for better formatting."""
        text_content = []
        page_count = 0
        
        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        # Add page marker for better chunking
                        text_content.append(f"[Page {page_num}]\n{text}")
                    
            return "\n\n".join(text_content), page_count
            
        except Exception as e:
            logger.warning(f"pdfplumber failed, falling back to PyPDF2: {e}")
            # Fallback to PyPDF2
            return await self._extract_pdf_text_pypdf2(file_path)
    
    async def _extract_pdf_text_pypdf2(self, file_path: str) -> tuple[str, int]:
        """Fallback PDF extraction using PyPDF2."""
        text_content = []
        page_count = 0
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_content.append(f"[Page {page_num}]\n{text}")
        
        return "\n\n".join(text_content), page_count
    
    async def _extract_docx_text(self, file_path: str) -> tuple[str, int]:
        """Extract text from DOCX files."""
        doc = Document(file_path)
        text_content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        # Estimate page count (rough approximation)
        total_text = "\n".join(text_content)
        estimated_pages = max(1, len(total_text) // 2500)  # ~2500 chars per page
        
        return "\n".join(text_content), estimated_pages
    
    async def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from plain text files."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    
    async def _create_text_chunks(self, text: str, document_id: str) -> List[TextChunk]:
        """Split text into chunks for better retrieval."""
        chunks = []
        
        # Simple sentence-aware chunking
        sentences = text.split('.')
        current_chunk = ""
        chunk_index = 0
        current_page = 1
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check for page markers
            if sentence.startswith('[Page '):
                try:
                    current_page = int(sentence.split('[Page ')[1].split(']')[0])
                    continue
                except:
                    pass
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    # Create chunk
                    chunk = TextChunk(
                        document_id=document_id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        page_number=current_page
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk with overlap
                overlap_words = current_chunk.split()[-20:]  # Keep last 20 words
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk += " " + sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunk = TextChunk(
                document_id=document_id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                page_number=current_page
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _generate_chunk_embeddings(self, chunks: List[TextChunk]):
        """Generate embeddings for text chunks."""
        if not chunks:
            return
        
        # Extract text content
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings in batch
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        
        # Assign embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding_vector = embedding.tolist()

class NoteProcessor:
    """Processor for free-form notes."""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.embedding_model)
    
    async def process_note(self, content: str, title: str, author: Optional[str] = None, 
                          tags: List[str] = None) -> tuple[DocumentMetadata, List[TextChunk]]:
        """Process a free-form note."""
        
        metadata = DocumentMetadata(
            filename=f"{title}.note",
            file_path="",  # Notes don't have file paths
            modality_type=ModalityType.TEXT,
            document_type=DocumentType.NOTE,
            file_size=len(content.encode('utf-8')),
            author=author,
            tags=tags or [],
            processing_status=ProcessingStatus.PROCESSING
        )
        
        # Create a single chunk for the note
        chunk = TextChunk(
            document_id=metadata.id,
            content=content,
            chunk_index=0,
            metadata={
                'title': title,
                'author': author,
                'tags': tags or []
            }
        )
        
        # Generate embedding
        embedding = self.embedding_model.encode([content], convert_to_numpy=True)
        chunk.embedding_vector = embedding[0].tolist()
        
        metadata.processing_status = ProcessingStatus.COMPLETED
        
        return metadata, [chunk]