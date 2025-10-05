# 🚂 Railway Deployment Guide

Deploy your Multimodal RAG System to Railway in minutes!

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **Cerebras API Key**: Get one at [cerebras.ai](https://cerebras.ai)

## 🚀 Quick Deploy

### Method 1: Deploy from GitHub (Recommended)

1. **Visit Railway Dashboard**
   - Go to [railway.app/new](https://railway.app/new)
   - Click "Deploy from GitHub repo"

2. **Connect Repository**
   - Authorize Railway to access your GitHub
   - Select `WeMakeDevs-Hackathon` repository

3. **Configure Environment Variables**
   Click "Variables" and add:
   ```env
   CEREBRAS_API_KEY=your_actual_cerebras_api_key_here
   PORT=8000
   PYTHONUNBUFFERED=1
   DEBUG=false
   VECTOR_DB_PATH=/app/data/chroma_db
   ```

4. **Deploy!**
   - Railway will automatically detect the `Dockerfile.railway`
   - Build process takes ~5-10 minutes (downloading ML models)
   - Your app will be live at `https://your-app.up.railway.app`

### Method 2: Deploy with Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Link to your project
railway link

# Set environment variables
railway variables set CEREBRAS_API_KEY=your_key_here
railway variables set PORT=8000
railway variables set DEBUG=false

# Deploy
railway up
```

## ⚙️ Configuration Details

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CEREBRAS_API_KEY` | Your Cerebras API key | `csk-xxxxx` |
| `PORT` | Application port (Railway sets this) | `8000` |
| `DEBUG` | Debug mode (set to false in prod) | `false` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_FILE_SIZE` | Max upload size in bytes | `104857600` (100MB) |
| `WHISPER_MODEL` | Whisper model size | `base` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `MAX_RETRIEVED_DOCS` | Number of docs for RAG | `5` |
| `FFMPEG_PATH` | Path to FFmpeg (auto-detected) | `ffmpeg` |

## 📦 What Gets Deployed

The Railway deployment includes:
- ✅ FastAPI application
- ✅ ChromaDB (embedded mode)
- ✅ FFmpeg for video processing
- ✅ OpenAI Whisper for transcription
- ✅ CLIP for image embeddings
- ✅ Meta Llama via Cerebras API
- ✅ All ML models (auto-downloaded)

## 🔧 Build Process

Railway will:
1. Use `Dockerfile.railway` for containerization
2. Install system dependencies (FFmpeg, Tesseract OCR, etc.)
3. Install Python packages from `requirements.txt`
4. Download ML models on first run (~2GB):
   - Whisper base model
   - Sentence transformers
   - CLIP model
5. Start the FastAPI server

**Build time**: 5-10 minutes (first deployment)  
**Subsequent builds**: 2-3 minutes (cached layers)

## 🌐 Accessing Your App

After deployment:
1. Railway provides a URL: `https://your-app-name.up.railway.app`
2. Visit the URL to access the web interface
3. Upload files and start querying!

### Custom Domain (Optional)

1. Go to Railway dashboard → Settings → Domains
2. Add your custom domain
3. Configure DNS records as shown

## 📊 Monitoring & Logs

### View Logs
```bash
railway logs
```

Or in Railway dashboard:
- Click on your deployment
- Navigate to "Deployments" tab
- Click on active deployment
- View real-time logs

### Metrics
Railway provides:
- CPU usage
- Memory usage
- Network traffic
- Request/response times

## 🔄 Updates & Redeployment

### Automatic Deployments
Railway auto-deploys on every push to main branch:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

### Manual Redeploy
In Railway dashboard:
- Click "Deploy" → "Redeploy"

### Rollback
- Go to "Deployments" tab
- Click on previous successful deployment
- Click "Redeploy"

## 💰 Pricing Considerations

### Railway Free Tier
- $5 free credits/month
- Enough for development and testing
- Sleeps after inactivity

### Resource Usage
This app requires:
- **RAM**: 2-4GB (ML models)
- **Storage**: 3-5GB (models + data)
- **CPU**: Medium usage

**Recommendation**: Use Railway's Hobby plan ($5/month) for consistent uptime.

### Cost Optimization Tips
1. **Use smaller models**:
   ```env
   WHISPER_MODEL=tiny  # Instead of 'base'
   ```
2. **Limit file uploads**:
   ```env
   MAX_FILE_SIZE=52428800  # 50MB instead of 100MB
   ```
3. **Enable sleep mode** for dev environments

## 🐛 Troubleshooting

### Build Failures

**Issue**: Out of memory during build
```bash
# Solution: Use smaller models in environment variables
WHISPER_MODEL=tiny
```

**Issue**: FFmpeg not found
```bash
# The Dockerfile.railway includes FFmpeg, but verify:
railway logs | grep ffmpeg
```

### Runtime Issues

**Issue**: App crashes after deployment
```bash
# Check logs
railway logs

# Common causes:
# 1. Missing CEREBRAS_API_KEY
# 2. Insufficient memory (upgrade plan)
# 3. Model download failed (redeploy)
```

**Issue**: Slow response times
```bash
# Cerebras API should be fast. Check:
# 1. Network latency
# 2. Railway region (use same as Cerebras)
# 3. Model size (use smaller models)
```

### Health Check Failures

Railway pings `/health` endpoint:
```bash
# Test locally first
curl https://your-app.up.railway.app/health

# Should return: {"status": "healthy"}
```

## 🔒 Security Best Practices

1. **Never commit `.env` files**
   - Use Railway's environment variables UI

2. **Use Railway's secrets**
   ```bash
   railway variables set CEREBRAS_API_KEY=xxx --secret
   ```

3. **Enable HTTPS**
   - Railway provides SSL by default

4. **Limit file uploads**
   - Set `MAX_FILE_SIZE` appropriately

5. **Monitor logs**
   - Check for suspicious activity

## 📱 Testing the Deployment

After deployment, test these features:

### 1. Upload a PDF
```bash
curl -X POST https://your-app.up.railway.app/upload \
  -F "file=@test.pdf"
```

### 2. Query the system
```bash
curl -X POST https://your-app.up.railway.app/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?", "session_id": "test-123"}'
```

### 3. Check health
```bash
curl https://your-app.up.railway.app/health
```

## 🎯 Performance Optimization

### 1. Use CDN for Static Files
Serve frontend assets via CDN:
- Upload `frontend/` to Cloudflare Pages
- Update API URLs

### 2. Enable Caching
Railway automatically caches Docker layers.

### 3. Database Optimization
For large-scale use:
- Deploy ChromaDB separately
- Use managed Redis
- Update connection strings

### 4. Horizontal Scaling
For high traffic:
```bash
railway scale --replicas 3
```

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Cerebras API Docs](https://inference-docs.cerebras.ai/)
- [Project GitHub](https://github.com/temburuakhil/WeMakeDevs-Hackathon)

## 🆘 Support

Having issues? Try these:

1. **Check Railway Status**: [status.railway.app](https://status.railway.app)
2. **Review Logs**: `railway logs --tail 100`
3. **Railway Community**: [Discord](https://discord.gg/railway)
4. **Project Issues**: [GitHub Issues](https://github.com/temburuakhil/WeMakeDevs-Hackathon/issues)

## 🎉 Success Checklist

- [ ] Railway account created
- [ ] Repository connected
- [ ] Environment variables configured
- [ ] Cerebras API key added
- [ ] Deployment successful
- [ ] Health check passing
- [ ] Can upload files
- [ ] Can query and get responses
- [ ] Custom domain configured (optional)

---

**Deployed successfully?** 🚀 Share your deployment URL and celebrate! 🎊

For local development, see [README.md](README.md).
