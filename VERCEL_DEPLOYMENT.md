# 🚀 Vercel Deployment Guide

## Quick Deploy to Vercel

### Prerequisites
1. **Cerebras API Key** - Get from [Cerebras Cloud](https://cloud.cerebras.ai/)
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
3. **External Services** (Required for Vercel serverless):
   - Redis: [Upstash Redis](https://upstash.com/) (Free tier available)
   - ChromaDB: [Railway](https://railway.app/) or [Render](https://render.com/)

---

## 📋 Step-by-Step Deployment

### Step 1: Setup External Services

#### A. Setup Redis (Upstash)

1. Go to [Upstash Console](https://console.upstash.com/)
2. Click "Create Database"
3. Choose region closest to your users
4. Copy the connection details:
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`

#### B. Setup ChromaDB (Railway)

1. Go to [Railway](https://railway.app/)
2. Click "New Project" → "Empty Project"
3. Click "New" → "Docker Image"
4. Use image: `chromadb/chroma:latest`
5. Add environment variables:
   ```
   IS_PERSISTENT=TRUE
   PERSIST_DIRECTORY=/chroma/chroma
   ```
6. Add volume: `/chroma/chroma` (10GB)
7. Generate domain and copy the URL

---

### Step 2: Deploy to Vercel

#### Option A: Deploy via Vercel Dashboard (Recommended)

1. **Push code to GitHub** (already done ✅)

2. **Go to Vercel Dashboard**:
   - Visit [vercel.com/new](https://vercel.com/new)
   - Click "Import Project"
   - Select your GitHub repository: `WeMakeDevs-Hackathon`

3. **Configure Project**:
   - Framework Preset: `Other`
   - Root Directory: `./`
   - Build Command: (leave empty)
   - Output Directory: (leave empty)

4. **Add Environment Variables**:
   ```
   CEREBRAS_API_KEY=your_cerebras_api_key_here
   REDIS_HOST=your-redis.upstash.io
   REDIS_PORT=6379
   REDIS_PASSWORD=your_upstash_password
   CHROMADB_HOST=your-chromadb.railway.app
   CHROMADB_PORT=443
   ```

5. **Click "Deploy"** 🚀

#### Option B: Deploy via Vercel CLI

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Navigate to project
cd "d:\WeMakeDevs Project"

# 4. Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? (Select your account)
# - Link to existing project? No
# - Project name? multimodal-rag
# - Directory? ./
# - Override settings? No

# 5. Add environment variables
vercel env add CEREBRAS_API_KEY
vercel env add REDIS_HOST
vercel env add REDIS_PORT
vercel env add REDIS_PASSWORD
vercel env add CHROMADB_HOST
vercel env add CHROMADB_PORT

# 6. Deploy to production
vercel --prod
```

---

### Step 3: Update Code for Vercel

The `vercel.json` and `api/index.py` files are already configured! But you need to make one small change to handle serverless limitations:

**Update `src/config.py`** to use environment variables properly:

```python
import os
from dotenv import load_dotenv

# Load .env only in local development
if os.path.exists('.env'):
    load_dotenv()

# Configuration
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))
```

---

## ⚠️ Important Vercel Limitations

### 1. **File Upload Size Limit**
- Vercel has a **4.5MB** request body limit on Hobby plan
- **Solution**: Use **Vercel Pro** ($20/month) for 100MB limit
- Or implement file upload to external storage (S3, Cloudinary)

### 2. **Execution Time Limit**
- Hobby: 10 seconds
- Pro: 60 seconds
- **Solution**: Process large files asynchronously

### 3. **Serverless Nature**
- Cannot store files persistently
- **Solution**: All uploads go to external storage (already using ChromaDB)

### 4. **Cold Starts**
- First request may be slow
- **Solution**: Keep function warm with scheduled pings

---

## 🎯 Recommended Architecture for Vercel

```
┌─────────────────────────────────────────┐
│           Vercel (Frontend + API)       │
│   • FastAPI endpoints                   │
│   • Static file serving                 │
│   • Serverless functions                │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────┐      ┌──────────┐
│  Upstash │      │ Railway  │
│  Redis   │      │ ChromaDB │
│  (Cache) │      │ (Vector) │
└──────────┘      └──────────┘
```

---

## 🔧 Alternative: Hybrid Deployment

If Vercel limitations are too restrictive, consider:

**Option 1: Vercel Frontend + Railway Backend**
- Deploy UI to Vercel
- Deploy API to Railway (no limits)

**Option 2: Full Railway Deployment**
- Deploy everything to Railway
- Use Railway's built-in Redis and ChromaDB

---

## 🧪 Testing Your Deployment

After deployment:

```bash
# Get your Vercel URL
vercel ls

# Test health endpoint
curl https://your-project.vercel.app/

# Test upload (small file)
curl -X POST https://your-project.vercel.app/upload \
  -F "file=@small-test.pdf"

# Test query
curl -X POST https://your-project.vercel.app/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test question",
    "session_id": "test123"
  }'
```

---

## 💡 Tips for Success

1. **Use Vercel Pro** if you need:
   - Larger file uploads (>4.5MB)
   - Longer execution times
   - Commercial license

2. **Monitor Usage**:
   - Vercel Dashboard → Analytics
   - Check function execution times
   - Monitor bandwidth usage

3. **Optimize for Serverless**:
   - Keep functions lightweight
   - Use caching aggressively
   - Lazy load ML models

4. **Custom Domain** (Optional):
   - Vercel Dashboard → Settings → Domains
   - Add your custom domain
   - Automatic HTTPS

---

## 📊 Cost Estimate

### Free Tier (Hobby)
- ✅ 100GB bandwidth/month
- ✅ Unlimited deployments
- ✅ Automatic HTTPS
- ⚠️ 4.5MB body size limit
- ⚠️ 10s execution time

**External Services:**
- Upstash Redis: Free tier (10,000 commands/day)
- Railway ChromaDB: $5/month credit

**Total: FREE** (within limits)

### Pro Plan ($20/month)
- ✅ 1TB bandwidth
- ✅ 100MB body size limit
- ✅ 60s execution time
- ✅ Priority support

**Total: ~$20-25/month**

---

## 🚀 Quick Deploy Button

Add this to your README.md:

```markdown
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/temburuakhil/WeMakeDevs-Hackathon&env=CEREBRAS_API_KEY,REDIS_HOST,REDIS_PORT,CHROMADB_HOST,CHROMADB_PORT)
```

---

## 🆘 Troubleshooting

### Error: "Module not found"
```bash
# Make sure requirements.txt is up to date
vercel dev  # Test locally first
```

### Error: "Function timeout"
- Reduce model size
- Optimize processing
- Use Vercel Pro for longer timeouts

### Error: "Body size exceeded"
- Upgrade to Vercel Pro
- Or implement chunked uploads

### Error: "Environment variable not set"
```bash
# Add missing env vars
vercel env add VARIABLE_NAME
vercel --prod  # Redeploy
```

---

## 📞 Next Steps

1. ✅ Deploy external services (Redis, ChromaDB)
2. ✅ Configure environment variables
3. ✅ Deploy to Vercel
4. ✅ Test all endpoints
5. ✅ Add custom domain (optional)
6. ✅ Share with hackathon judges!

**Your Vercel URL will be:** `https://multimodal-rag-{random}.vercel.app`

Good luck! 🎉
