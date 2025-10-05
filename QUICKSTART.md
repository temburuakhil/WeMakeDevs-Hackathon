# Quick Start Guide - Multimodal RAG System

## 🚀 Get Started in 3 Steps

### Step 1: Set Your API Key
Edit the `.env` file and add your Cerebras API key:
```
CEREBRAS_API_KEY=csk-your-actual-key-here
```

### Step 2: Start the System

**Option A - With Docker (Easiest):**
```powershell
.\start.ps1 docker
```
Wait ~2 minutes for build to complete.

**Option B - Locally (Faster start, but need Python):**
```powershell
.\start.ps1 local
```

### Step 3: Open Your Browser
Visit: **http://localhost:8000** or **http://localhost**

---

## 📤 Upload Files

Drag and drop or click to upload:
- 📄 PDF or DOCX documents
- 🖼️ Images (PNG, JPG)
- 🎵 Audio files (MP3, WAV, M4A)

---

## 💬 Ask Questions

Try these example queries:

```
"What does the document say about Q3 performance?"
"Show me images with charts"
"Find the audio where we discussed the budget"
"What are the key findings in the report?"
```

---

## 🛑 Stop the System

```powershell
.\start.ps1 stop
```

---

## 📊 Check Status

```powershell
.\start.ps1 status
```

---

## 🧪 Run Tests

```powershell
# Make sure system is running first!
.\start.ps1 test
```

---

## ⚡ Troubleshooting

### Docker build fails?
- Make sure Docker Desktop is running
- Try: `docker-compose down` then `.\start.ps1 docker` again

### Port already in use?
- Stop existing services: `.\start.ps1 stop`
- Or change ports in `docker-compose.yml`

### Can't access localhost?
- Check if services are running: `.\start.ps1 status`
- Try port 8000 directly: `http://localhost:8000`

### Python errors?
- Make sure you have Python 3.11+: `python --version`
- Reinstall dependencies: `pip install -r requirements.txt`

---

## 📚 Features

✅ **Multimodal Search** - Find content across PDFs, images, and audio  
✅ **AI Answers** - Get intelligent responses powered by Meta Llama  
✅ **Citations** - Every answer includes numbered source references  
✅ **Cross-Modal** - Search images with text, find audio by content  
✅ **Fast** - Cerebras API for ultra-fast inference  

---

## 🆘 Need Help?

- View logs: `docker-compose logs -f multimodal-rag`
- Check health: `curl http://localhost:8000/health`
- See full docs: `README.md`

---

**That's it! Start uploading files and asking questions!** 🎉