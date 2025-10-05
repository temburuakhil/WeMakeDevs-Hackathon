# 🚂 Railway Deployment Checklist

Use this checklist to ensure a successful Railway deployment.

## Pre-Deployment

### Code Preparation
- [ ] All files committed to git
- [ ] Code pushed to GitHub repository
- [ ] `.env` file NOT committed (use `.env.example`)
- [ ] All dependencies in `requirements.txt`
- [ ] Dockerfile tested locally (optional)

### API Keys & Credentials
- [ ] Cerebras API key obtained ([cerebras.ai](https://cerebras.ai))
- [ ] API key tested locally
- [ ] `.env.example` file updated with all required variables

### Railway Account
- [ ] Railway account created ([railway.app](https://railway.app))
- [ ] GitHub account connected to Railway
- [ ] Payment method added (for production use)

## Deployment

### Initial Setup
- [ ] Visited [railway.app/new](https://railway.app/new)
- [ ] Selected "Deploy from GitHub repo"
- [ ] Repository `WeMakeDevs-Hackathon` connected
- [ ] Dockerfile detected correctly

### Configuration
- [ ] Environment variables configured:
  - [ ] `CEREBRAS_API_KEY` (required)
  - [ ] `PORT` (set to 8000)
  - [ ] `DEBUG` (set to false)
  - [ ] `PYTHONUNBUFFERED` (set to 1)
  - [ ] `VECTOR_DB_PATH` (optional: /app/data/chroma_db)
  - [ ] `WHISPER_MODEL` (optional: base)
  - [ ] `MAX_FILE_SIZE` (optional: 104857600)

### Build Process
- [ ] Deployment initiated
- [ ] Build started (check "Deployments" tab)
- [ ] Docker image built successfully
- [ ] System dependencies installed (FFmpeg, etc.)
- [ ] Python packages installed
- [ ] ML models downloaded (~2GB)
- [ ] Build completed (5-10 minutes)

### Post-Deployment
- [ ] Deployment URL received
- [ ] Health check passing (`/health` endpoint)
- [ ] Application accessible via URL
- [ ] SSL certificate active (HTTPS)

## Testing

### Basic Functionality
- [ ] Homepage loads correctly
- [ ] Can upload a PDF file
- [ ] Can upload an image file
- [ ] Can upload an audio file
- [ ] Can upload a video file (with FFmpeg)
- [ ] Can query uploaded content
- [ ] Responses generated via Cerebras API
- [ ] Citations working correctly
- [ ] "New Chat" button functional

### API Endpoints
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `POST /upload` accepts files
- [ ] `POST /query` returns responses
- [ ] `GET /documents` lists uploaded files
- [ ] Error handling works correctly

### Performance
- [ ] Response time < 3 seconds for queries
- [ ] File upload completes successfully
- [ ] No memory errors
- [ ] No timeout errors
- [ ] Cerebras API responding quickly

## Monitoring

### Logs & Metrics
- [ ] Logs accessible in Railway dashboard
- [ ] No error messages in logs
- [ ] CPU usage reasonable (<80%)
- [ ] Memory usage stable
- [ ] No crashes or restarts

### Health Monitoring
- [ ] Set up uptime monitoring (optional)
- [ ] Configure alerts for failures (optional)
- [ ] Monitor API usage costs

## Optional Enhancements

### Custom Domain
- [ ] Custom domain purchased
- [ ] Domain added in Railway settings
- [ ] DNS records configured
- [ ] SSL certificate issued

### GitHub Actions
- [ ] `RAILWAY_TOKEN` added to GitHub secrets
- [ ] Workflow tested with a commit
- [ ] Auto-deployment working

### Performance Optimization
- [ ] Considered using smaller models (if needed)
- [ ] Enabled caching (Railway does this)
- [ ] Reviewed file size limits
- [ ] Database optimization (if scaling)

## Troubleshooting

If any issues occur:

### Build Failures
- [ ] Checked build logs in Railway dashboard
- [ ] Verified `Dockerfile.railway` syntax
- [ ] Confirmed all dependencies in `requirements.txt`
- [ ] Checked for sufficient memory allocation

### Runtime Errors
- [ ] Verified `CEREBRAS_API_KEY` is set correctly
- [ ] Checked application logs for errors
- [ ] Tested health endpoint
- [ ] Verified FFmpeg is available

### Performance Issues
- [ ] Reviewed memory usage
- [ ] Checked Cerebras API status
- [ ] Considered upgrading Railway plan
- [ ] Optimized model sizes

## Success Criteria

Deployment is successful when:
- ✅ Application accessible via Railway URL
- ✅ All file types upload and process correctly
- ✅ Queries return accurate responses with citations
- ✅ No errors in logs
- ✅ Response times acceptable
- ✅ Health check passing consistently

## Next Steps

After successful deployment:
- [ ] Share deployment URL with team
- [ ] Update project README with live demo link
- [ ] Test with real-world data
- [ ] Monitor costs and usage
- [ ] Plan for scaling (if needed)
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring/alerting
- [ ] Document any deployment-specific configurations

## Resources

- **Railway Dashboard**: [railway.app/dashboard](https://railway.app/dashboard)
- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Deployment Guide**: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- **Cerebras API**: [cerebras.ai/api](https://cerebras.ai)
- **Support**: [discord.gg/railway](https://discord.gg/railway)

---

**Deployment Date**: _______________

**Deployment URL**: _______________

**Deployed By**: _______________

**Notes**:
_______________________________________________
_______________________________________________
_______________________________________________
