# 🤖 Multimodal RAG System for WeMakeDevs Hackathon

An intelligent search and retrieval system that seamlessly handles documents (PDF/DOCX), images, audio recordings, and videos using Retrieval-Augmented Generation (RAG) with multimodal capabilities powered by Meta Llama via Cerebras API.

## 🏆 Hackathon Highlights

### 🚀 Best Use of Cerebras API
Our system leverages **Cerebras Cloud SDK** for ultra-fast LLM inference:
- **Lightning-fast responses**: Meta Llama 3.1-8B runs at incredible speeds via Cerebras inference
- **Optimized parameters**: `temperature=0.8`, `top_p=0.95`, `max_tokens=2048` for natural conversations
- **Conversation context**: Maintains session-based chat history with warm TCP connections
- **Fallback architecture**: Seamlessly switches between Cerebras API and local models
- **Real-time processing**: Generates responses while users are still reading previous answers

```python
# Example: Ultra-fast inference with Cerebras
chat_completion = self.cerebras_client.chat.completions.create(
    messages=[{"role": "system", "content": "..."},
              {"role": "user", "content": prompt}],
    model="llama3.1-8b",
    max_tokens=2048,
    temperature=0.8,
    top_p=0.95
)
```

### 🧠 Best Use of Llama (Meta's Open-Source LLM)
**Meta Llama 3.1-8B** powers our intelligent RAG system:
- **Multimodal understanding**: Processes context from PDFs, images (via OCR), and audio transcripts
- **Cross-modal reasoning**: Connects information across different content types
- **Natural conversations**: Cleaned output without citation markers or markdown
- **Context-aware responses**: Maintains conversation history for follow-up questions
- **Dual-model architecture**: 
  - Primary: Llama 3.1 via Cerebras (production speed)
  - Fallback: DialoGPT-medium (offline capability)
- **Smart prompting**: Custom RAG prompts that avoid hallucinations and ensure grounded answers

### 🐳 Most Creative Usage of Docker MCP Gateway
**Innovative Docker architecture** for seamless development:
- **Hybrid deployment**: Docker for dependencies (ChromaDB, Redis), local Python for rapid development
- **Minimal footprint**: Only essential services containerized, avoiding heavy ML model downloads
- **Smart service orchestration**: `docker-compose.simple.yml` for lean, fast startup
- **Developer-friendly**: Instant code changes without rebuilding containers
- **MCP integration ready**: Architecture supports Model Context Protocol gateway patterns
- **Production-ready**: Easy switch to full Docker deployment via `docker-compose.yml`

```yaml
# Lightweight Docker setup - only what's needed
services:
  chromadb:    # Vector database
  redis:       # Session storage
# Python app runs locally for speed!
```

## 🌟 Features

### Core Capabilities
- **📄 Document Processing**: Extract text from PDF and DOCX files with formatting preservation
- **🖼️ Image Understanding**: Generate visual embeddings with CLIP, extract text via OCR (EasyOCR)
- **🎵 Audio Transcription**: Speech-to-text with OpenAI Whisper, timestamp preservation
- **🎥 Video Processing**: Extract audio from videos (MP4, AVI, MOV, MKV) and transcribe
- **🔍 Cross-Modal Search**: Find content across all modalities with semantic search
- **🧠 RAG-Powered Answers**: Generate natural, conversational responses with Meta Llama 3.1
- **� Chat Interface**: Beautiful modern UI with conversation memory and session management

### Advanced Features
- **🎯 Cross-Reference Detection**: Find related content across different modalities
- **💬 Conversation Context**: Maintains chat history for context-aware follow-up questions
- **🚀 Ultra-Fast Inference**: Cerebras API integration for lightning-fast responses
- **🎨 Beautiful UI**: Modern gradient design with chat bubbles and smooth animations
- **🔄 Session Management**: New Chat feature to start fresh conversations
- **🧹 Clean Responses**: No citation markers or markdown formatting - just natural answers

## 🏗️ Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                     WEB INTERFACE (Modern Chat UI)              │
│  Beautiful Gradient • Chat Bubbles • Session Management         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│  • File Upload Endpoints  • Query Processing  • Health Checks   │
└─────┬───────────────┬────────────────┬──────────────────────────┘
      │               │                │
      ▼               ▼                ▼
┌───────────┐  ┌────────────┐  ┌─────────────┐
│ Document  │  │   Image    │  │   Audio/    │
│ Processor │  │ Processor  │  │   Video     │
│           │  │            │  │  Processor  │
│ PyPDF2    │  │ CLIP       │  │ Whisper     │
│ pdfplumber│  │ EasyOCR    │  │ FFmpeg      │
└─────┬─────┘  └─────┬──────┘  └──────┬──────┘
      │              │                │
      └──────────────┴────────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │   EMBEDDING & VECTORIZATION  │
      │ Sentence Transformers (384d) │
      │    CLIP ViT-B-32 (512d)     │
      └──────────────┬───────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │      CHROMADB (Docker)       │
      │  • text_embeddings           │
      │  • document_embeddings       │
      │  • image_embeddings          │
      │  • audio_embeddings          │
      └──────────────┬───────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │   CROSS-MODAL RETRIEVAL      │
      │  Semantic Search + Ranking   │
      └──────────────┬───────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │      RAG SYSTEM              │
      │ ┌──────────────────────────┐ │
      │ │   CEREBRAS API           │ │
      │ │ Meta Llama 3.1-8B        │ │
      │ │ Ultra-Fast Inference     │ │
      │ └──────────────────────────┘ │
      │ ┌──────────────────────────┐ │
      │ │  Fallback: DialoGPT      │ │
      │ │  Local Model (863MB)     │ │
      │ └──────────────────────────┘ │
      └──────────────┬───────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │    RESPONSE CLEANING         │
      │  Remove citations & markdown │
      │  Natural conversation style  │
      └──────────────┬───────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │     USER RESPONSE            │
      │  Session-based conversation  │
      │  Context-aware follow-ups    │
      └──────────────────────────────┘
```

### Docker Architecture (Hybrid Approach)
```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER CONTAINERS                         │
│  ┌─────────────────┐          ┌──────────────────┐         │
│  │   ChromaDB      │          │      Redis       │         │
│  │  Port: 8001     │          │   Port: 6379     │         │
│  │  Vector Storage │          │  Session Cache   │         │
│  └─────────────────┘          └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ Network Bridge
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   LOCAL PYTHON APP                           │
│  • FastAPI Server (Port 8000)                               │
│  • Hot-reload for rapid development                         │
│  • Direct GPU access (CUDA)                                 │
│  • No container rebuild needed                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- FFmpeg (for video/audio processing)
- Docker & Docker Compose (for ChromaDB and Redis)
- At least 8GB RAM (16GB+ recommended)
- NVIDIA GPU (optional, for faster inference)
- Cerebras API Key ([Get one here](https://cerebras.ai/))

### 1. Clone the Repository
```bash
git clone https://github.com/temburuakhil/WeMakeDevs-Hackathon.git
cd WeMakeDevs-Hackathon
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Cerebras API key
# CEREBRAS_API_KEY=your_cerebras_api_key_here
```

### 3. Install FFmpeg

**Windows (PowerShell):**
```powershell
winget install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg tesseract-ocr
```

### 4. Start Services

**Option A: Quick Local Setup (Recommended for Development)**

```powershell
# Windows PowerShell
.\run-local.ps1
```

```bash
# Mac/Linux
./run-local.sh
```

This will:
- Start ChromaDB and Redis in Docker
- Install Python dependencies
- Start the FastAPI server on http://localhost:8000

**Option B: Full Docker Deployment**

```bash
# Start all services
docker-compose up --build

# Access the application
open http://localhost
```

## 🎨 User Interface

The application features a beautiful modern web interface with:
- **Gradient purple-blue background**
- **Chat-style message bubbles** (user messages in blue on right, AI on left)
- **Smooth animations** for message appearance
- **File upload** with drag-and-drop support
- **"New Chat" button** to start fresh conversations
- **Session-based conversation** memory

Visit `http://localhost:8000` after starting the server!

## 📚 Supported File Types

### Documents
- PDF (`.pdf`)
- Word Documents (`.docx`)
- Text Files (`.txt`)

### Images
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- BMP (`.bmp`)
- WebP (`.webp`)

### Audio
- MP3 (`.mp3`)
- WAV (`.wav`)
- FLAC (`.flac`)
- M4A (`.m4a`)

### Video
- MP4 (`.mp4`)
- AVI (`.avi`)
- MOV (`.mov`)
- MKV (`.mkv`)

*Videos are processed by extracting audio and transcribing with Whisper*

## 🔧 Usage Examples

### 1. Upload Files
Simply drag and drop or select files through the web interface at `http://localhost:8000`

### 2. Ask Questions
Type your question in the chat box. The system will:
- Search across all your uploaded documents, images, and audio/video transcriptions
- Generate a natural, conversational answer using Meta Llama 3.1
- Maintain conversation context for follow-up questions

### 3. Start New Conversation
Click the "🔄 New Chat" button to clear conversation history and start fresh

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern web framework for building APIs
- **Python 3.12**: Core programming language
- **ChromaDB**: Vector database for embeddings storage
- **Redis**: Caching and session management

### AI/ML Models
- **Meta Llama 3.1 (8B)**: LLM via Cerebras API for ultra-fast inference
- **Microsoft DialoGPT**: Fallback local model
- **OpenAI Whisper**: Audio transcription
- **CLIP ViT-B-32**: Image-text cross-modal embeddings
- **Sentence Transformers**: Text embeddings (all-MiniLM-L6-v2)
- **EasyOCR**: Optical character recognition

### Document Processing
- **PyPDF2 & pdfplumber**: PDF text extraction
- **python-docx**: Word document processing
- **Pillow**: Image manipulation
- **FFmpeg**: Video/audio processing

### Frontend
- **HTML5/CSS3/JavaScript**: Modern web interface
- **Beautiful gradient design**: Purple to blue theme
- **Responsive chat UI**: Message bubbles with animations

## 🏗️ Project Structure

```
WeMakeDevs-Hackathon/
├── src/
│   ├── api/              # FastAPI application
│   │   └── main.py       # API endpoints & web UI
│   ├── ingestion/        # File processors
│   │   ├── document_processor.py
│   │   ├── image_processor.py
│   │   └── audio_processor.py
│   ├── retrieval/        # Search & retrieval
│   │   ├── vector_database.py
│   │   └── cross_modal_search.py
│   ├── rag/              # RAG system
│   │   └── llama_rag.py
│   ├── citations/        # Citation tracking
│   └── models.py         # Data models
├── docker-compose.simple.yml  # Minimal Docker setup
├── requirements.txt      # Python dependencies
├── run-local.ps1        # Windows startup script
├── .env.example         # Environment template
└── README.md

```
- **mcp-gateway**: Docker MCP Gateway for service orchestration
- **nginx**: Reverse proxy and load balancer
- **document-processor**: Microservice for document processing
- **image-processor**: Microservice for image processing
- **audio-processor**: Microservice for audio processing

### Service Health Monitoring
```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs multimodal-rag

# Monitor MCP Gateway
docker-compose logs mcp-gateway
```

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
CEREBRAS_API_KEY=your_cerebras_key
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Vector Database
VECTOR_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Model Configuration
WHISPER_MODEL=base
CLIP_MODEL=ViT-B/32
MAX_CONTEXT_LENGTH=4096
MAX_RETRIEVED_DOCS=5
```

### Custom Model Configuration
```python
# src/config.py
class Settings(BaseSettings):
    # Use larger Whisper model for better accuracy
    whisper_model: str = "medium"  # base, small, medium, large
    
    # Use different CLIP model
    clip_model: str = "ViT-L/14"  # ViT-B/32, ViT-L/14
    
    # Adjust retrieval parameters
    max_retrieved_docs: int = 10
```

## 🎯 API Endpoints

### Core Endpoints
- `GET /` - Web UI (chat interface)
- `POST /upload` - Upload files (PDF, DOCX, images, audio, video)
- `POST /query` - Query the RAG system with conversation context
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger)

### Example API Usage
```bash
# Upload a file
curl -X POST "http://localhost:8000/upload" \
     -F "file=@document.pdf"

# Query the system with session
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is the main topic?",
       "session_id": "user123"
     }'
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```env
# Cerebras API
CEREBRAS_API_KEY=your_cerebras_api_key_here

# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Vector Database
VECTOR_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Model Configuration
WHISPER_MODEL=base
MAX_RETRIEVED_DOCS=5
```

## 🎓 How It Works

1. **File Upload**: Users upload documents, images, audio, or video files
2. **Processing**:
   - PDFs/DOCX → Text extraction
   - Images → CLIP embeddings + OCR text extraction
   - Audio/Video → Whisper transcription with timestamps
3. **Vector Storage**: All content is embedded and stored in ChromaDB
4. **Query Processing**: 
   - User query is embedded using sentence-transformers
   - Cross-modal search retrieves relevant content
   - Retrieved context is sent to Meta Llama via Cerebras API
5. **Response Generation**: 
   - Llama generates natural, conversational answers
   - Responses are cleaned (no citations or markdown)
   - Conversation context is maintained for follow-ups

## 🚧 Troubleshooting

### FFmpeg not found
```powershell
# Windows
winget install ffmpeg

# Restart terminal and verify
ffmpeg -version
```

### ChromaDB connection error
```bash
# Restart Docker containers
docker-compose -f docker-compose.simple.yml restart
```

### Python package issues
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 📝 License

This project was created for the WeMakeDevs Hackathon.

## 🙏 Acknowledgments

- **WeMakeDevs** for organizing the hackathon
- **Cerebras** for ultra-fast LLM inference API
- **Meta** for Llama models
- **OpenAI** for Whisper
- **ChromaDB** for vector database
- All open-source contributors

## 👨‍💻 Author

**Akhil Temburu**
- GitHub: [@temburuakhil](https://github.com/temburuakhil)
- Project: [WeMakeDevs-Hackathon](https://github.com/temburuakhil/WeMakeDevs-Hackathon)

---

Made with ❤️ for WeMakeDevs Hackathon 🚀
curl -X POST "http://localhost:8000/add-note" \
     -F "title=Meeting Notes" \
     -F "content=Discussed project timeline" \
     -F "author=John Doe" \
     -F "tags=meeting,timeline"
```

## 📊 Citation System

The system provides transparent source attribution:

### Citation Types
- **[1] Document page 5** - PDF/DOCX with page reference
- **[2] Image: chart.png** - Image with filename
- **[3] Audio transcript at 2:45** - Audio with timestamp

### Citation Metadata
```json
{
  "citations": [
    {
      "number": 1,
      "source": "Document page 5",
      "modality": "document",
      "relevance_score": 0.89,
      "content_preview": "The key findings indicate...",
      "page": 5,
      "document_id": "uuid"
    }
  ]
}
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_document_processor.py
pytest tests/test_image_processor.py
pytest tests/test_rag_system.py
```

### Integration Tests
```bash
# Test full pipeline
python scripts/test_pipeline.py

# Test with sample files
python scripts/run_examples.py
```

## 🚀 Performance Optimization

### Recommended Hardware
- **CPU**: 8+ cores (Intel i7/AMD Ryzen 7+)
- **RAM**: 16GB+ (32GB for large models)
- **GPU**: NVIDIA RTX 3080+ (optional, for faster inference)
- **Storage**: SSD with 50GB+ free space

### Model Optimization
```python
# Use quantized models for faster inference
WHISPER_MODEL = "base"  # Smaller model
CLIP_MODEL = "ViT-B/32"  # Faster than ViT-L/14

# Batch processing for better throughput
BATCH_SIZE = 8
MAX_CONCURRENT_UPLOADS = 3
```

## 🔒 Security Considerations

### File Upload Security
- File size limits (100MB default)
- File type validation
- Virus scanning (implement with ClamAV)
- Rate limiting on uploads

### API Security
- CORS configuration
- Request rate limiting
- Input validation and sanitization
- Authentication (implement JWT tokens)

## 📈 Monitoring and Logging

### Application Metrics
- Request latency and throughput
- File processing times
- Vector database performance
- Citation accuracy rates

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8001/api/v1/heartbeat

# Service monitoring
docker-compose exec mcp-gateway curl http://localhost:8080/status
```

## 🛠️ Development

### Project Structure
```
multimodal-rag/
├── src/
│   ├── api/          # FastAPI application
│   ├── ingestion/    # File processing modules
│   ├── retrieval/    # Vector database and search
│   ├── rag/          # RAG system with Llama
│   └── citations/    # Citation tracking
├── tests/            # Test files
├── scripts/          # Utility scripts
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Adding New Modalities
1. Create processor in `src/ingestion/`
2. Add models to `src/models.py`
3. Update vector database schema
4. Implement search in retrieval engine
5. Add API endpoints

### Custom Embeddings
```python
# Add custom embedding model
from sentence_transformers import SentenceTransformer

class CustomEmbedder:
    def __init__(self):
        self.model = SentenceTransformer('your-custom-model')
    
    def encode(self, texts):
        return self.model.encode(texts)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests before committing
pytest && black . && flake8
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Meta Llama** for the language model
- **Cerebras** for fast inference API
- **OpenAI Whisper** for speech recognition
- **OpenAI CLIP** for image understanding
- **ChromaDB** for vector storage
- **Docker** for containerization

## 🐛 Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce batch sizes or use smaller models
2. **Slow Processing**: Enable GPU acceleration or use Cerebras API
3. **Import Errors**: Check Python path and virtual environment
4. **Docker Issues**: Ensure sufficient disk space and memory

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m uvicorn src.api.main:app --log-level debug
```

### Support
- 📧 Email: [your-email]
- 💬 Discord: [your-discord]
- 📝 Issues: [GitHub Issues](https://github.com/your-repo/issues)

---

**Built for WeMakeDevs Hackathon** 🚀

*Demonstrating the power of multimodal AI with RAG, citations, and containerized deployment.*