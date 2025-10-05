import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
import whisper
import librosa
import numpy as np
from pydub import AudioSegment
from sentence_transformers import SentenceTransformer

from ..models import (
    DocumentMetadata, AudioSegment as AudioSegmentModel, 
    ModalityType, ProcessingStatus
)
from ..config import settings

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        # Load Whisper model for speech-to-text
        self.whisper_model = whisper.load_model(settings.whisper_model)
        
        # Load embedding model for text embeddings
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        
        # Supported audio formats
        self.supported_formats = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma', '.aac'}
        
        # Audio processing parameters
        self.segment_length = 30  # seconds
        self.overlap_length = 5   # seconds
    
    async def process_audio(self, file_path: str, filename: str) -> tuple[DocumentMetadata, List[AudioSegmentModel]]:
        """Process an audio file and extract transcription with timestamps."""
        try:
            # Create metadata
            file_size = os.path.getsize(file_path)
            metadata = DocumentMetadata(
                filename=filename,
                file_path=file_path,
                modality_type=ModalityType.AUDIO,
                file_size=file_size,
                processing_status=ProcessingStatus.PROCESSING
            )
            
            # Load and analyze audio
            audio_info = await self._analyze_audio_file(file_path)
            metadata.duration = audio_info['duration']
            metadata.custom_metadata.update(audio_info)
            
            # Convert to format suitable for Whisper if needed
            processed_audio_path = await self._prepare_audio_for_whisper(file_path)
            
            # Transcribe audio with timestamps
            transcription_result = await self._transcribe_with_whisper(processed_audio_path)
            
            # Create audio segments with embeddings
            audio_segments = await self._create_audio_segments(
                transcription_result, metadata.id
            )
            
            # Generate embeddings for segments
            await self._generate_segment_embeddings(audio_segments)
            
            metadata.processing_status = ProcessingStatus.COMPLETED
            logger.info(f"Successfully processed audio: {filename}")
            
            # Clean up temporary file if created
            if processed_audio_path != file_path:
                try:
                    os.remove(processed_audio_path)
                except:
                    pass
            
            return metadata, audio_segments
            
        except Exception as e:
            logger.error(f"Error processing audio {filename}: {str(e)}")
            metadata.processing_status = ProcessingStatus.FAILED
            return metadata, []
    
    async def _analyze_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze audio file to extract metadata."""
        try:
            # Load audio with librosa for analysis
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Extract audio features
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            
            return {
                'duration': duration,
                'sample_rate': sr,
                'tempo': float(tempo),
                'average_spectral_centroid': float(np.mean(spectral_centroids)),
                'average_zero_crossing_rate': float(np.mean(zero_crossing_rate)),
                'length_samples': len(y)
            }
            
        except Exception as e:
            logger.warning(f"Audio analysis failed: {e}")
            # Fallback to basic duration estimation
            try:
                audio = AudioSegment.from_file(file_path)
                return {
                    'duration': len(audio) / 1000.0,  # Convert to seconds
                    'sample_rate': audio.frame_rate,
                    'channels': audio.channels
                }
            except:
                return {'duration': 0}
    
    async def _prepare_audio_for_whisper(self, file_path: str) -> str:
        """Convert audio to format suitable for Whisper if needed."""
        try:
            # Check if file is already in a good format
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.wav', '.mp3', '.flac']:
                return file_path
            
            # Convert to WAV for better Whisper compatibility
            audio = AudioSegment.from_file(file_path)
            
            # Create temporary WAV file
            temp_dir = Path(settings.data_dir) / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            temp_path = temp_dir / f"temp_audio_{os.getpid()}.wav"
            audio.export(temp_path, format="wav")
            
            return str(temp_path)
            
        except Exception as e:
            logger.warning(f"Audio conversion failed, using original: {e}")
            return file_path
    
    async def _transcribe_with_whisper(self, file_path: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper with detailed timestamps."""
        try:
            # Use Whisper to transcribe with word-level timestamps
            result = self.whisper_model.transcribe(
                file_path,
                word_timestamps=True,
                verbose=False
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return {'segments': [], 'text': ''}
    
    async def _create_audio_segments(self, transcription_result: Dict[str, Any], 
                                   document_id: str) -> List[AudioSegmentModel]:
        """Create audio segments from Whisper transcription."""
        segments = []
        
        if 'segments' not in transcription_result:
            return segments
        
        for i, segment in enumerate(transcription_result['segments']):
            audio_segment = AudioSegmentModel(
                document_id=document_id,
                transcript=segment.get('text', '').strip(),
                start_timestamp=segment.get('start', 0.0),
                end_timestamp=segment.get('end', 0.0),
                confidence=self._calculate_segment_confidence(segment),
                metadata={
                    'segment_id': segment.get('id', i),
                    'words': segment.get('words', []),
                    'language': transcription_result.get('language', 'unknown')
                }
            )
            
            if audio_segment.transcript:  # Only add non-empty segments
                segments.append(audio_segment)
        
        return segments
    
    def _calculate_segment_confidence(self, segment: Dict[str, Any]) -> float:
        """Calculate confidence score for a segment."""
        try:
            # If word-level confidence is available, average it
            words = segment.get('words', [])
            if words and all('confidence' in word for word in words):
                confidences = [word['confidence'] for word in words]
                return sum(confidences) / len(confidences)
            
            # Fallback: use segment-level confidence if available
            return segment.get('confidence', 0.8)  # Default reasonable confidence
            
        except:
            return 0.8
    
    async def _generate_segment_embeddings(self, segments: List[AudioSegmentModel]):
        """Generate embeddings for audio segment transcripts."""
        if not segments:
            return
        
        # Extract transcript texts
        texts = [segment.transcript for segment in segments]
        
        # Generate embeddings in batch
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        
        # Assign embeddings to segments
        for segment, embedding in zip(segments, embeddings):
            segment.embedding_vector = embedding.tolist()
    
    def is_supported_format(self, filename: str) -> bool:
        """Check if the audio format is supported."""
        ext = Path(filename).suffix.lower()
        return ext in self.supported_formats
    
    async def search_audio_by_text(self, query: str, 
                                 audio_segments: List[tuple[str, str, float, float, List[float]]]) -> List[tuple[str, float, float, float]]:
        """Search audio segments by text query."""
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0]
            
            # Calculate similarities
            similarities = []
            for segment_id, transcript, start_time, end_time, embedding in audio_segments:
                if embedding:
                    # Calculate cosine similarity
                    segment_embedding = np.array(embedding)
                    similarity = np.dot(query_embedding, segment_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(segment_embedding)
                    )
                    similarities.append((segment_id, float(similarity), start_time, end_time))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities
            
        except Exception as e:
            logger.error(f"Audio search failed: {e}")
            return []
    
    async def get_audio_segment_at_time(self, file_path: str, start_time: float, 
                                      end_time: float) -> Optional[str]:
        """Extract audio segment at specific time range."""
        try:
            audio = AudioSegment.from_file(file_path)
            
            # Convert times to milliseconds
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            # Extract segment
            segment = audio[start_ms:end_ms]
            
            # Save to temporary file
            temp_dir = Path(settings.data_dir) / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            temp_path = temp_dir / f"segment_{start_time}_{end_time}.wav"
            segment.export(temp_path, format="wav")
            
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"Audio segment extraction failed: {e}")
            return None

class SpeakerDiarization:
    """Optional speaker diarization capabilities."""
    
    def __init__(self):
        # This would require additional models like pyannote.audio
        # For now, we'll implement a simple placeholder
        pass
    
    async def identify_speakers(self, audio_path: str, segments: List[AudioSegmentModel]) -> List[AudioSegmentModel]:
        """Identify different speakers in audio segments."""
        # Placeholder implementation
        # In a full implementation, you would use models like pyannote.audio
        
        # Simple heuristic: assume speaker changes on longer pauses
        for i, segment in enumerate(segments):
            if i > 0:
                prev_segment = segments[i-1]
                gap = segment.start_timestamp - prev_segment.end_timestamp
                
                if gap > 2.0:  # More than 2 seconds gap
                    segment.speaker = f"Speaker_{i % 3 + 1}"  # Rotate between 3 speakers
                else:
                    segment.speaker = prev_segment.speaker
            else:
                segment.speaker = "Speaker_1"
        
        return segments