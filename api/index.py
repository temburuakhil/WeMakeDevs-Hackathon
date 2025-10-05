"""
Vercel Serverless Function Handler
This file is the entry point for Vercel deployment
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the FastAPI app
from src.api.main import app

# Export app for Vercel
# Vercel will automatically handle ASGI/WSGI
handler = app
