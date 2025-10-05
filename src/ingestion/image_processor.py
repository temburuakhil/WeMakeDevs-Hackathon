import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from PIL import Image
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import easyocr
import cv2

from ..models import (
    DocumentMetadata, ImageData, ModalityType, 
    ProcessingStatus
)
from ..config import settings

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        # Load CLIP-like model for image embeddings
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model = SentenceTransformer('clip-ViT-B-32')
        
        # Initialize OCR reader
        self.ocr_reader = easyocr.Reader(['en'])  # Can be extended for multiple languages
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    async def process_image(self, file_path: str, filename: str) -> tuple[DocumentMetadata, ImageData]:
        """Process an image file and extract visual embeddings and text."""
        try:
            # Create metadata
            file_size = os.path.getsize(file_path)
            metadata = DocumentMetadata(
                filename=filename,
                file_path=file_path,
                modality_type=ModalityType.IMAGE,
                file_size=file_size,
                processing_status=ProcessingStatus.PROCESSING
            )
            
            # Load and process image
            image = Image.open(file_path).convert('RGB')
            width, height = image.size
            
            metadata.dimensions = {"width": width, "height": height}
            
            # Generate thumbnail
            thumbnail_path = await self._create_thumbnail(file_path, filename)
            
            # Extract text using OCR
            extracted_text = await self._extract_text_from_image(file_path)
            
            # Generate CLIP embedding
            embedding_vector = await self._generate_image_embedding(image)
            
            # Create ImageData object
            image_data = ImageData(
                document_id=metadata.id,
                image_path=file_path,
                thumbnail_path=thumbnail_path,
                extracted_text=extracted_text,
                embedding_vector=embedding_vector,
                width=width,
                height=height,
                metadata={
                    'format': image.format,
                    'mode': image.mode,
                    'has_text': bool(extracted_text and extracted_text.strip())
                }
            )
            
            metadata.processing_status = ProcessingStatus.COMPLETED
            logger.info(f"Successfully processed image: {filename}")
            
            return metadata, image_data
            
        except Exception as e:
            logger.error(f"Error processing image {filename}: {str(e)}")
            metadata.processing_status = ProcessingStatus.FAILED
            return metadata, None
    
    async def _create_thumbnail(self, file_path: str, filename: str) -> str:
        """Create a thumbnail for the image."""
        try:
            thumbnail_dir = Path(settings.data_dir) / "thumbnails"
            thumbnail_dir.mkdir(exist_ok=True)
            
            # Create thumbnail filename
            name = Path(filename).stem
            thumbnail_filename = f"{name}_thumb.jpg"
            thumbnail_path = thumbnail_dir / thumbnail_filename
            
            # Create thumbnail
            with Image.open(file_path) as image:
                # Calculate thumbnail size (max 200x200 while maintaining aspect ratio)
                image.thumbnail((200, 200), Image.Resampling.LANCZOS)
                image.save(thumbnail_path, "JPEG", quality=85)
            
            return str(thumbnail_path)
            
        except Exception as e:
            logger.warning(f"Failed to create thumbnail for {filename}: {e}")
            return ""
    
    async def _extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            # Use EasyOCR for text extraction
            results = self.ocr_reader.readtext(file_path)
            
            # Extract text with confidence filtering
            extracted_texts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filter low-confidence detections
                    extracted_texts.append(text)
            
            return " ".join(extracted_texts)
            
        except Exception as e:
            logger.warning(f"OCR failed for image: {e}")
            return ""
    
    async def _generate_image_embedding(self, image: Image.Image) -> list[float]:
        """Generate CLIP embedding for the image."""
        try:
            # Convert PIL image to the format expected by sentence-transformers
            # sentence-transformers CLIP model expects PIL images
            embedding = self.clip_model.encode(image, convert_to_numpy=True)
            
            return embedding.flatten().tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate image embedding: {e}")
            return []
    
    def is_supported_format(self, filename: str) -> bool:
        """Check if the image format is supported."""
        ext = Path(filename).suffix.lower()
        return ext in self.supported_formats
    
    async def search_images_by_text(self, query: str, image_embeddings: list[tuple[str, list[float]]]) -> list[tuple[str, float]]:
        """Search images using text query via CLIP."""
        try:
            # Encode text query using sentence-transformers CLIP model
            text_embedding = self.clip_model.encode(query, convert_to_numpy=True).flatten()
            
            # Calculate similarities
            similarities = []
            for image_id, image_embedding in image_embeddings:
                if image_embedding:
                    similarity = np.dot(text_embedding, image_embedding)
                    similarities.append((image_id, float(similarity)))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to search images by text: {e}")
            return []
    
    async def get_image_similarity(self, image1_embedding: list[float], image2_embedding: list[float]) -> float:
        """Calculate similarity between two images."""
        try:
            if not image1_embedding or not image2_embedding:
                return 0.0
            
            # Convert to numpy arrays
            emb1 = np.array(image1_embedding)
            emb2 = np.array(image2_embedding)
            
            # Calculate cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate image similarity: {e}")
            return 0.0

class ImageAnalyzer:
    """Additional image analysis capabilities."""
    
    def __init__(self):
        pass
    
    async def analyze_image_content(self, image_path: str) -> Dict[str, Any]:
        """Analyze image content for additional metadata."""
        try:
            image = cv2.imread(image_path)
            
            analysis = {
                'brightness': self._calculate_brightness(image),
                'dominant_colors': self._get_dominant_colors(image),
                'has_faces': self._detect_faces(image),
                'edge_density': self._calculate_edge_density(image)
            }
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Image analysis failed: {e}")
            return {}
    
    def _calculate_brightness(self, image) -> float:
        """Calculate average brightness of the image."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))
    
    def _get_dominant_colors(self, image, k=3) -> list[list[int]]:
        """Get dominant colors in the image."""
        data = image.reshape((-1, 3))
        data = np.float32(data)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        return centers.astype(int).tolist()
    
    def _detect_faces(self, image) -> bool:
        """Simple face detection."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            return len(faces) > 0
        except:
            return False
    
    def _calculate_edge_density(self, image) -> float:
        """Calculate edge density for image complexity measure."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return float(np.sum(edges > 0) / edges.size)