import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import time
import re
from cerebras.cloud.sdk import Cerebras
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from ..models import RAGResponse, Citation, QueryRequest, SearchResult
from ..config import settings
from ..retrieval.cross_modal_search import CrossModalRetrieval
from ..citations.citation_tracker import CitationTracker

logger = logging.getLogger(__name__)

class LlamaRAGSystem:
    def __init__(self):
        self.retrieval_engine = CrossModalRetrieval()
        self.citation_tracker = CitationTracker()
        
        # Initialize Cerebras client for fast inference
        self.cerebras_client = Cerebras(api_key=settings.cerebras_api_key)
        
        # Fallback to local Llama model if Cerebras is unavailable
        self.local_model = None
        self.local_tokenizer = None
        # Only initialize local model if explicitly enabled (disabled by default to save GPU memory)
        if settings.use_local_model:
            self._initialize_local_model()
        
        # Conversation memory
        self.conversation_history = {}
    
    def _initialize_local_model(self):
        """Initialize local Llama model as fallback."""
        try:
            # Note: This requires significant memory. Use smaller models for demo
            model_name = "microsoft/DialoGPT-medium"  # Lighter alternative for demo
            
            self.local_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.local_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            if self.local_tokenizer.pad_token is None:
                self.local_tokenizer.pad_token = self.local_tokenizer.eos_token
            
            logger.info("Local model initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize local model: {e}")
            self.local_model = None
            self.local_tokenizer = None
    
    async def generate_response(self, query_request: QueryRequest, 
                              session_id: Optional[str] = None) -> RAGResponse:
        """Generate RAG response with citations."""
        start_time = time.time()
        
        try:
            # 1. Retrieve relevant context
            context_items = await self.retrieval_engine.get_context_for_rag(
                query_request.query, 
                max_context_items=settings.max_retrieved_docs
            )
            
            # 2. Create search results for citation tracking
            search_results = []
            for item in context_items:
                search_result = SearchResult(
                    id=item['metadata'].get('document_id', ''),
                    document_id=item['metadata'].get('document_id', ''),
                    content=item['content'],
                    modality_type=item['modality'],
                    relevance_score=item['relevance_score'],
                    metadata=item['metadata'],
                    source_reference=item['source'],
                    page_number=item['metadata'].get('page_number'),
                    timestamp=item['metadata'].get('timestamp')
                )
                search_results.append(search_result)
            
            # 3. Generate response with LLM
            llm_response = await self._generate_llm_response(
                query_request.query, context_items, session_id
            )
            
            # 4. Extract and track citations
            citations = await self.citation_tracker.extract_citations(
                llm_response, search_results
            )
            
            # 5. Calculate confidence score
            confidence = await self._calculate_confidence(
                query_request.query, context_items, llm_response
            )
            
            processing_time = time.time() - start_time
            
            return RAGResponse(
                answer=llm_response,
                query=query_request.query,
                citations=citations,
                confidence=confidence,
                processing_time=processing_time,
                retrieved_contexts=search_results
            )
            
        except Exception as e:
            logger.error(f"RAG response generation failed: {e}")
            return RAGResponse(
                answer="I apologize, but I encountered an error while processing your request. Please try again.",
                query=query_request.query,
                citations=[],
                retrieved_contexts=[]
            )
    
    async def _generate_llm_response(self, query: str, context_items: List[Dict[str, Any]], 
                                   session_id: Optional[str] = None) -> str:
        """Generate response using Cerebras API or local model."""
        
        # Build context string
        context_str = await self._build_context_string(context_items)
        
        # Get conversation history
        conversation_context = self._get_conversation_context(session_id)
        
        # Create prompt
        prompt = await self._create_rag_prompt(query, context_str, conversation_context)
        
        try:
            # Try Cerebras API first
            response = await self._generate_with_cerebras(prompt)
            if response:
                # Additional cleaning just in case
                response = self._clean_response(response)
                self._update_conversation_history(session_id, query, response)
                return response
                
        except Exception as e:
            logger.warning(f"Cerebras API failed, falling back to local model: {e}")
        
        # Fallback to local model
        try:
            response = await self._generate_with_local_model(prompt)
            if response:
                self._update_conversation_history(session_id, query, response)
                return response
                
        except Exception as e:
            logger.error(f"Local model generation failed: {e}")
        
        # Final fallback
        return await self._generate_fallback_response(query, context_items)
    
    async def _generate_with_cerebras(self, prompt: str) -> Optional[str]:
        """Generate response using Cerebras API."""
        try:
            chat_completion = self.cerebras_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a knowledgeable and friendly AI assistant. Provide clear, natural, conversational answers. Never use citation markers like [1] or markdown formatting like **bold**. Write in plain, easy-to-read language."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3.1-8b",
                max_tokens=2048,
                temperature=0.8,
                top_p=0.95
            )
            
            response = chat_completion.choices[0].message.content
            # Clean the response
            cleaned = self._clean_response(response.strip())
            return cleaned
            
        except Exception as e:
            logger.error(f"Cerebras generation failed: {e}")
            return None
    
    async def _generate_with_local_model(self, prompt: str) -> Optional[str]:
        """Generate response using local model."""
        if not self.local_model or not self.local_tokenizer:
            return None
        
        try:
            # Encode input
            inputs = self.local_tokenizer.encode(prompt, return_tensors="pt", truncate=True, max_length=512)
            
            # Generate response
            with torch.no_grad():
                outputs = self.local_model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 256,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.local_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.local_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part
            generated = response[len(prompt):].strip()
            
            return generated if generated else None
            
        except Exception as e:
            logger.error(f"Local model generation failed: {e}")
            return None
    
    async def _build_context_string(self, context_items: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved items."""
        context_parts = []
        
        for i, item in enumerate(context_items, 1):
            modality = item['modality']
            content = item['content']
            source = item['source']
            
            context_part = f"[{i}] {modality.upper()} - {source}\n{content}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    async def _create_rag_prompt(self, query: str, context: str, 
                               conversation_context: str = "") -> str:
        """Create RAG prompt with context and instructions."""
        
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context.

IMPORTANT:
- Give clear, natural, conversational answers
- Use information from the context provided below
- Break down complex topics into easy-to-understand explanations
- Do NOT use citation markers like [1], [2] or ** markdown formatting
- Write in plain, natural language
- If the context doesn't have enough information, say so clearly and offer what you know

CONTEXT:
{context}

{conversation_context}

USER QUESTION: {query}

Provide a helpful, natural answer:"""
        
        return prompt
    
    def _get_conversation_context(self, session_id: Optional[str]) -> str:
        """Get conversation history for context."""
        if not session_id or session_id not in self.conversation_history:
            return ""
        
        history = self.conversation_history[session_id]
        if len(history) == 0:
            return ""
        
        context_parts = ["CONVERSATION HISTORY:"]
        
        # Include last 3 exchanges
        for exchange in history[-3:]:
            context_parts.append(f"Q: {exchange['query']}")
            context_parts.append(f"A: {exchange['response'][:200]}...")  # Truncate for brevity
        
        context_parts.append("")  # Empty line separator
        
        return "\n".join(context_parts)
    
    def _clean_response(self, response: str) -> str:
        """Clean up response by removing citations and formatting markers."""
        import re
        
        # Remove citation markers like [1], [2], etc.
        cleaned = re.sub(r'\[\d+\]', '', response)
        
        # Remove ** markdown bold markers
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        
        # Remove * markdown italic markers (but not bullet points)
        cleaned = re.sub(r'(?<!\n)\*([^*\n]+)\*(?!\*)', r'\1', cleaned)
        
        # Clean up extra whitespace
        cleaned = re.sub(r' +', ' ', cleaned)
        cleaned = re.sub(r'\n\n+', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def _update_conversation_history(self, session_id: Optional[str], 
                                   query: str, response: str):
        """Update conversation history."""
        if not session_id:
            return
        
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            'query': query,
            'response': response,
            'timestamp': time.time()
        })
        
        # Keep only last 10 exchanges
        if len(self.conversation_history[session_id]) > 10:
            self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
    
    async def _generate_fallback_response(self, query: str, 
                                        context_items: List[Dict[str, Any]]) -> str:
        """Generate a simple fallback response."""
        if not context_items:
            return "I couldn't find any relevant information in the knowledge base to answer your question."
        
        # Simple template-based response
        response_parts = [
            f"Based on the available information, here's what I found regarding '{query}':",
            ""
        ]
        
        for i, item in enumerate(context_items[:3], 1):
            content_preview = item['content'][:200] + "..." if len(item['content']) > 200 else item['content']
            response_parts.append(f"[{i}] From {item['source']}: {content_preview}")
        
        response_parts.append("")
        response_parts.append("Please note that this is a simplified response. For more detailed analysis, please try your query again.")
        
        return "\n".join(response_parts)
    
    async def _calculate_confidence(self, query: str, context_items: List[Dict[str, Any]], 
                                  response: str) -> float:
        """Calculate confidence score for the response."""
        try:
            confidence_factors = []
            
            # Factor 1: Number of relevant sources
            num_sources = len(context_items)
            source_score = min(1.0, num_sources / 3.0)  # Optimal around 3 sources
            confidence_factors.append(source_score)
            
            # Factor 2: Average relevance of sources
            if context_items:
                avg_relevance = sum(item['relevance_score'] for item in context_items) / len(context_items)
                confidence_factors.append(avg_relevance)
            else:
                confidence_factors.append(0.0)
            
            # Factor 3: Response length (not too short, not too long)
            response_length = len(response.split())
            length_score = 1.0 if 20 <= response_length <= 200 else 0.7
            confidence_factors.append(length_score)
            
            # Factor 4: Citation usage
            citation_count = len(re.findall(r'\[\d+\]', response))
            citation_score = min(1.0, citation_count / max(1, len(context_items)))
            confidence_factors.append(citation_score)
            
            # Calculate weighted average
            weights = [0.3, 0.4, 0.1, 0.2]  # Emphasize source relevance
            confidence = sum(w * f for w, f in zip(weights, confidence_factors))
            
            return round(confidence, 2)
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.5  # Default moderate confidence
    
    async def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of conversation history."""
        if session_id not in self.conversation_history:
            return {'exchanges': 0, 'topics': []}
        
        history = self.conversation_history[session_id]
        
        return {
            'exchanges': len(history),
            'topics': [exchange['query'][:50] + "..." if len(exchange['query']) > 50 
                      else exchange['query'] for exchange in history[-5:]],
            'last_activity': history[-1]['timestamp'] if history else None
        }