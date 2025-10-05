import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np

from ..models import Citation, SearchResult, ModalityType
from ..config import settings

logger = logging.getLogger(__name__)

class CitationTracker:
    def __init__(self):
        self.sentence_encoder = SentenceTransformer(settings.embedding_model)
        self.citation_counter = 0
    
    async def extract_citations(self, response_text: str, 
                              search_results: List[SearchResult]) -> List[Citation]:
        """Extract and create citations from response text and search results."""
        citations = []
        
        try:
            # Find citation markers in the text [1], [2], etc.
            citation_matches = re.findall(r'\[(\d+)\]', response_text)
            cited_numbers = [int(num) for num in citation_matches]
            
            # Create citations for explicitly referenced sources
            for citation_num in sorted(set(cited_numbers)):
                if citation_num <= len(search_results):
                    search_result = search_results[citation_num - 1]  # 1-indexed to 0-indexed
                    
                    citation = Citation(
                        number=citation_num,
                        document_id=search_result.document_id,
                        content=search_result.content,
                        modality_type=search_result.modality_type,
                        source_reference=search_result.source_reference,
                        page_number=search_result.page_number,
                        timestamp=search_result.timestamp,
                        relevance_score=search_result.relevance_score,
                        metadata=search_result.metadata
                    )
                    
                    citations.append(citation)
            
            # If no explicit citations found, create implicit citations for top sources
            if not citations and search_results:
                citations = await self._create_implicit_citations(response_text, search_results)
            
            # Sort citations by number
            citations.sort(key=lambda x: x.number)
            
            return citations
            
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")
            return []
    
    async def _create_implicit_citations(self, response_text: str, 
                                       search_results: List[SearchResult]) -> List[Citation]:
        """Create citations for sources that likely contributed to the response."""
        citations = []
        
        try:
            # Analyze semantic similarity between response and sources
            response_embedding = self.sentence_encoder.encode([response_text])
            
            source_similarities = []
            for result in search_results[:5]:  # Check top 5 sources
                source_embedding = self.sentence_encoder.encode([result.content])
                similarity = np.dot(response_embedding[0], source_embedding[0])
                source_similarities.append((result, similarity))
            
            # Sort by similarity and create citations for top contributors
            source_similarities.sort(key=lambda x: x[1], reverse=True)
            
            citation_num = 1
            for result, similarity in source_similarities[:3]:  # Top 3 contributors
                if similarity > 0.3:  # Similarity threshold
                    citation = Citation(
                        number=citation_num,
                        document_id=result.document_id,
                        content=result.content,
                        modality_type=result.modality_type,
                        source_reference=result.source_reference,
                        page_number=result.page_number,
                        timestamp=result.timestamp,
                        relevance_score=result.relevance_score,
                        metadata=result.metadata
                    )
                    
                    citations.append(citation)
                    citation_num += 1
            
            return citations
            
        except Exception as e:
            logger.error(f"Implicit citation creation failed: {e}")
            return []
    
    async def create_citation_preview(self, citation: Citation) -> Dict[str, Any]:
        """Create a preview of citation content for UI display."""
        try:
            preview = {
                'citation_number': citation.number,
                'modality': citation.modality_type.value,
                'source': citation.source_reference,
                'preview_text': '',
                'metadata': {},
                'file_info': {}
            }
            
            # Generate preview based on modality type
            if citation.modality_type == ModalityType.DOCUMENT:
                preview.update(await self._create_document_preview(citation))
            elif citation.modality_type == ModalityType.IMAGE:
                preview.update(await self._create_image_preview(citation))
            elif citation.modality_type == ModalityType.AUDIO:
                preview.update(await self._create_audio_preview(citation))
            
            return preview
            
        except Exception as e:
            logger.error(f"Citation preview creation failed: {e}")
            return {'error': 'Preview unavailable'}
    
    async def _create_document_preview(self, citation: Citation) -> Dict[str, Any]:
        """Create preview for document citation."""
        content = citation.content
        
        # Truncate content for preview
        preview_text = content[:300] + "..." if len(content) > 300 else content
        
        return {
            'preview_text': preview_text,
            'metadata': {
                'page_number': citation.page_number,
                'document_id': citation.document_id,
                'source_type': 'document'
            },
            'file_info': {
                'type': 'text',
                'can_expand': True
            }
        }
    
    async def _create_image_preview(self, citation: Citation) -> Dict[str, Any]:
        """Create preview for image citation."""
        metadata = citation.metadata
        
        return {
            'preview_text': citation.content if citation.content else "Image content (OCR extracted text)",
            'metadata': {
                'image_path': metadata.get('image_path', ''),
                'thumbnail_path': metadata.get('thumbnail_path', ''),
                'dimensions': f"{metadata.get('width', 0)}x{metadata.get('height', 0)}",
                'has_text': metadata.get('has_text', False),
                'source_type': 'image'
            },
            'file_info': {
                'type': 'image',
                'thumbnail_available': bool(metadata.get('thumbnail_path')),
                'can_view_full': True
            }
        }
    
    async def _create_audio_preview(self, citation: Citation) -> Dict[str, Any]:
        """Create preview for audio citation."""
        start_time = citation.timestamp or 0
        end_time = citation.metadata.get('end_timestamp', start_time)
        
        # Format timestamp
        start_min = int(start_time // 60)
        start_sec = int(start_time % 60)
        end_min = int(end_time // 60)
        end_sec = int(end_time % 60)
        
        time_range = f"{start_min}:{start_sec:02d} - {end_min}:{end_sec:02d}"
        
        return {
            'preview_text': citation.content,
            'metadata': {
                'time_range': time_range,
                'start_timestamp': start_time,
                'end_timestamp': end_time,
                'confidence': citation.metadata.get('confidence', 0.0),
                'speaker': citation.metadata.get('speaker', 'Unknown'),
                'source_type': 'audio'
            },
            'file_info': {
                'type': 'audio',
                'can_play_segment': True,
                'duration': end_time - start_time
            }
        }
    
    async def generate_citation_html(self, citations: List[Citation]) -> str:
        """Generate HTML for citation display."""
        if not citations:
            return ""
        
        html_parts = ["<div class='citations-container'>"]
        html_parts.append("<h3>Sources</h3>")
        
        for citation in citations:
            preview = await self.create_citation_preview(citation)
            citation_html = await self._create_citation_html_block(citation, preview)
            html_parts.append(citation_html)
        
        html_parts.append("</div>")
        
        return "\n".join(html_parts)
    
    async def _create_citation_html_block(self, citation: Citation, 
                                        preview: Dict[str, Any]) -> str:
        """Create HTML block for individual citation."""
        modality_icon = {
            'document': '📄',
            'image': '🖼️',
            'audio': '🎵',
            'text': '📝'
        }.get(citation.modality_type.value, '📁')
        
        html = f"""
        <div class='citation-block' data-citation='{citation.number}'>
            <div class='citation-header'>
                <span class='citation-number'>[{citation.number}]</span>
                <span class='citation-icon'>{modality_icon}</span>
                <span class='citation-source'>{citation.source_reference}</span>
                <span class='citation-score'>Relevance: {citation.relevance_score:.2f}</span>
            </div>
            <div class='citation-preview'>
                {preview.get('preview_text', '')[:200]}
                {"..." if len(preview.get('preview_text', '')) > 200 else ""}
            </div>
        </div>
        """
        
        return html
    
    async def track_citation_usage(self, response_text: str, citations: List[Citation]) -> Dict[str, Any]:
        """Track how citations are used in the response."""
        usage_stats = {
            'total_citations': len(citations),
            'modality_breakdown': {},
            'citation_density': 0,
            'coverage_score': 0
        }
        
        try:
            # Count citations by modality
            for citation in citations:
                modality = citation.modality_type.value
                usage_stats['modality_breakdown'][modality] = usage_stats['modality_breakdown'].get(modality, 0) + 1
            
            # Calculate citation density (citations per 100 words)
            word_count = len(response_text.split())
            if word_count > 0:
                usage_stats['citation_density'] = (len(citations) / word_count) * 100
            
            # Calculate coverage score (percentage of response backed by citations)
            citation_markers = len(re.findall(r'\[\d+\]', response_text))
            sentences = len(re.split(r'[.!?]+', response_text))
            if sentences > 0:
                usage_stats['coverage_score'] = min(100, (citation_markers / sentences) * 100)
            
            return usage_stats
            
        except Exception as e:
            logger.error(f"Citation usage tracking failed: {e}")
            return usage_stats
    
    async def validate_citations(self, response_text: str, citations: List[Citation]) -> Dict[str, Any]:
        """Validate that citations are properly used and accessible."""
        validation_results = {
            'valid_citations': 0,
            'invalid_citations': 0,
            'missing_content': 0,
            'issues': []
        }
        
        try:
            for citation in citations:
                # Check if citation content is available
                if not citation.content or not citation.content.strip():
                    validation_results['missing_content'] += 1
                    validation_results['issues'].append(f"Citation [{citation.number}] has no content")
                    continue
                
                # Check if citation is referenced in text
                citation_pattern = f"\\[{citation.number}\\]"
                if not re.search(citation_pattern, response_text):
                    validation_results['issues'].append(f"Citation [{citation.number}] not referenced in text")
                
                # Check metadata completeness
                if citation.modality_type == ModalityType.DOCUMENT and not citation.page_number:
                    validation_results['issues'].append(f"Citation [{citation.number}] missing page number")
                
                if citation.modality_type == ModalityType.AUDIO and citation.timestamp is None:
                    validation_results['issues'].append(f"Citation [{citation.number}] missing timestamp")
                
                validation_results['valid_citations'] += 1
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Citation validation failed: {e}")
            return validation_results

class CitationFormatter:
    """Formats citations for different output formats."""
    
    @staticmethod
    async def format_for_json(citations: List[Citation]) -> List[Dict[str, Any]]:
        """Format citations for JSON API response."""
        formatted_citations = []
        
        for citation in citations:
            formatted = {
                'number': citation.number,
                'source': citation.source_reference,
                'modality': citation.modality_type.value,
                'relevance_score': citation.relevance_score,
                'content_preview': citation.content[:200] + "..." if len(citation.content) > 200 else citation.content
            }
            
            # Add modality-specific information
            if citation.page_number:
                formatted['page'] = citation.page_number
            
            if citation.timestamp is not None:
                formatted['timestamp'] = citation.timestamp
            
            formatted_citations.append(formatted)
        
        return formatted_citations
    
    @staticmethod
    async def format_for_markdown(citations: List[Citation]) -> str:
        """Format citations for Markdown output."""
        if not citations:
            return ""
        
        markdown_parts = ["## Sources\n"]
        
        for citation in citations:
            source_line = f"[{citation.number}] **{citation.source_reference}**"
            
            if citation.page_number:
                source_line += f" (Page {citation.page_number})"
            
            if citation.timestamp is not None:
                minutes = int(citation.timestamp // 60)
                seconds = int(citation.timestamp % 60)
                source_line += f" (Time: {minutes}:{seconds:02d})"
            
            source_line += f" - Relevance: {citation.relevance_score:.2f}"
            
            markdown_parts.append(source_line)
            
            # Add content preview
            content_preview = citation.content[:150] + "..." if len(citation.content) > 150 else citation.content
            markdown_parts.append(f"   > {content_preview}\n")
        
        return "\n".join(markdown_parts)