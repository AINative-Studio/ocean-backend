# Ocean Backend - Railway Deployment Guide

## Overview

This guide covers deploying the Ocean backend to Railway staging and production environments.

**Technology Stack:**
- **Framework:** FastAPI + Python 3.11
- **Database:** ZeroDB (serverless NoSQL + vector search)
- **Platform:** Railway
- **CI/CD:** GitHub Actions
- **Domain:** TBD (will be configured in Railway)

---

## Prerequisites

Before deploying, ensure you have:

1. **Railway Account**
   - Sign up at https://railway.app
   - Install Railway CLI: `npm install -g @railway/cli`
   - Login: `railway login`

2. **GitHub Repository**
   - Repository: https://github.com/AINative-Studio/ocean-backend
   - Access to repository settings for secrets

3. **ZeroDB Credentials**
   - Project ID (from ZeroDB dashboard)
   - API Key (from ZeroDB dashboard)
   - API URL: https://api.ainative.studio

4. **Secret Key**
   - Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

---

## Railway Project Setup

### Step 1: Create Railway Project

```bash
# Option A: Via Railway CLI
railway login
railway init
# Enter project name: ocean-backend-staging

# Option B: Via Railway Dashboard
# 1. Go to https://railway.app/new
# 2. Click "Empty Project"
# 3. Name: ocean-backend-staging
```

### Step 2: Link GitHub Repository

**Via Railway Dashboard:**
1. Go to your project: https://railway.app/project/your-project-id
2. Click "+ New Service"
3. Select "GitHub Repo"
4. Authorize Railway to access your GitHub account
5. Select repository: `AINative-Studio/ocean-backend`
6. Railway will auto-detect Python and start building

**Via Railway CLI:**
```bash
cd /Users/aideveloper/ocean-backend
railway link
# Select your project: ocean-backend-staging
```

### Step 3: Configure Environment

**Create staging environment:**
```bash
railway environment create staging
railway environment switch staging
```

---

## Environment Variables Configuration

### Required Variables

Set these in Railway Dashboard → Variables tab or via CLI:

```bash
# Core ZeroDB Configuration
railway variables set ZERODB_API_URL=https://api.ainative.studio
railway variables set ZERODB_PROJECT_ID=your_project_id_here
railway variables set ZERODB_API_KEY=your_api_key_here

# Application Configuration
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
railway variables set PROJECT_NAME="Ocean Backend"
railway variables set DEBUG=false

# Embeddings Configuration
railway variables set OCEAN_EMBEDDINGS_MODEL=BAAI/bge-base-en-v1.5
railway variables set OCEAN_EMBEDDINGS_DIMENSIONS=768

# API Configuration
railway variables set API_V1_STR=/api/v1

# CORS Origins (add your frontend URLs)
railway variables set BACKEND_CORS_ORIGINS='["http://localhost:3000","http://localhost:5173","https://your-frontend.vercel.app"]'

# Railway automatically provides:
# - PORT (Railway assigns this)
# - RAILWAY_ENVIRONMENT
# - RAILWAY_SERVICE_NAME
```

### Environment Variables Checklist

Use this checklist when setting up a new environment:

- [ ] `ZERODB_API_URL` - ZeroDB API endpoint
- [ ] `ZERODB_PROJECT_ID` - Your ZeroDB project ID
- [ ] `ZERODB_API_KEY` - Your ZeroDB API key
- [ ] `SECRET_KEY` - Random 32-byte key for JWT signing
- [ ] `OCEAN_EMBEDDINGS_MODEL` - Embeddings model name
- [ ] `OCEAN_EMBEDDINGS_DIMENSIONS` - Embeddings dimensions (768)
- [ ] `BACKEND_CORS_ORIGINS` - Allowed frontend origins
- [ ] `DEBUG` - Set to `false` in production

---

## GitHub Actions Setup

### Required GitHub Secrets

Add these secrets in GitHub → Settings → Secrets and variables → Actions:

```bash
# Railway Deployment
RAILWAY_TOKEN              # Get from: railway tokens create
RAILWAY_PROJECT_ID         # Get from: railway status
RAILWAY_STAGING_URL        # Format: https://ocean-backend-staging.up.railway.app

# ZeroDB Test Environment (for CI tests)
ZERODB_API_URL            # https://api.ainative.studio
ZERODB_PROJECT_ID_TEST    # Separate test project ID
ZERODB_API_KEY_TEST       # Separate test API key
SECRET_KEY_TEST           # Random key for tests
```

### Getting Railway Secrets

```bash
# Get Railway token
railway tokens create
# Copy the token to GitHub secret: RAILWAY_TOKEN

# Get Railway project ID
railway status
# Copy project ID to GitHub secret: RAILWAY_PROJECT_ID

# Get Railway staging URL
railway domain
# Copy domain to GitHub secret: RAILWAY_STAGING_URL
```

---

## Deployment Process

### Automatic Deployment (Recommended)

When you push to `main` branch:

1. **GitHub Actions triggers**
   - Runs linting (flake8)
   - Runs type checking (mypy)
   - Runs full test suite with coverage
   - Uploads coverage to Codecov

2. **If tests pass:**
   - Deploys to Railway staging
   - Waits 30 seconds for deployment
   - Runs health check
   - Runs smoke tests
   - Notifies on success/failure

3. **If deployment fails:**
   - Railway keeps previous deployment active
   - GitHub Actions workflow fails
   - Check logs for errors

### Manual Deployment

```bash
# Link to Railway project
railway link

# Deploy to staging
railway environment switch staging
railway up

# Deploy to production (after testing)
railway environment switch production
railway up

# Watch logs
railway logs
```

---

## Health Checks and Monitoring

### Health Check Endpoint

```bash
# Check if service is healthy
curl https://your-app.up.railway.app/health

# Expected response:
{
  "status": "healthy",
  "service": "ocean-backend",
  "version": "0.1.0",
  "zerodb": {
    "project_id": "your_project_id",
    "api_url": "https://api.ainative.studio",
    "embeddings_model": "BAAI/bge-base-en-v1.5"
  }
}
```

### Monitoring

**Railway Dashboard:**
- Metrics: https://railway.app/project/your-project-id/metrics
- Logs: https://railway.app/project/your-project-id/logs
- Deployments: https://railway.app/project/your-project-id/deployments

**Key Metrics to Monitor:**
- HTTP response times
- Error rates
- Memory usage
- CPU usage
- Active connections

---

## Smoke Tests

After deployment, verify these endpoints:

```bash
export STAGING_URL=https://your-app.up.railway.app

# 1. Health check
curl $STAGING_URL/health

# 2. Root endpoint
curl $STAGING_URL/

# 3. API info
curl $STAGING_URL/api/v1/info

# 4. API docs
curl $STAGING_URL/docs

# 5. Create test page
curl -X POST $STAGING_URL/api/v1/ocean/pages \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Page","content":"Testing deployment"}'

# 6. Search (should return results)
curl "$STAGING_URL/api/v1/ocean/search?query=test&limit=5"
```

---

## Rollback Procedures

### Automatic Rollback

Railway keeps previous deployments active. If health checks fail, Railway automatically serves the previous version.

### Manual Rollback

```bash
# View deployments
railway deployments list

# Rollback to specific deployment
railway rollback <deployment-id>

# Or via Railway Dashboard:
# 1. Go to Deployments tab
# 2. Find working deployment
# 3. Click "Redeploy"
```

### Emergency Rollback

If you need to rollback immediately:

```bash
# Option 1: Revert git commit
git revert HEAD
git push origin main
# GitHub Actions will auto-deploy previous version

# Option 2: Manual Railway rollback
railway deployments list
railway rollback <previous-deployment-id>
```

---

## Troubleshooting

### Deployment Fails

**Check logs:**
```bash
railway logs
```

**Common issues:**
- Missing environment variables → Check `railway variables list`
- Build failure → Check `requirements.txt` and Python version
- Health check timeout → Check `railway.json` healthcheck settings
- Port binding → Ensure app uses `$PORT` environment variable

### Tests Fail in CI

**Run tests locally:**
```bash
cd /Users/aideveloper/ocean-backend
pytest tests/ -v --cov=app
```

**Check GitHub Actions logs:**
- Go to repository → Actions tab
- Click failed workflow
- Review logs for each step

### Health Check Fails

**Check ZeroDB connection:**
```bash
# SSH into Railway container
railway run bash

# Test ZeroDB connection
python -c "
from app.config import settings
print(f'API URL: {settings.ZERODB_API_URL}')
print(f'Project ID: {settings.ZERODB_PROJECT_ID}')
"
```

### High Error Rates

**Check Railway logs:**
```bash
railway logs --filter error
```

**Check ZeroDB status:**
- Verify API key is valid
- Check rate limits
- Verify project quota

---

## Configuration Files

### railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### railway.toml (alternative)

```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

---

## Production Deployment

### Before Going to Production

- [ ] All tests passing in staging
- [ ] Smoke tests verified
- [ ] Load testing completed (if applicable)
- [ ] Environment variables reviewed
- [ ] CORS origins updated for production frontend
- [ ] Monitoring and alerts configured
- [ ] Backup/restore procedures documented
- [ ] Rate limiting configured (if needed)

### Production Environment Setup

```bash
# Create production environment
railway environment create production

# Switch to production
railway environment switch production

# Set production variables (use different values!)
railway variables set ZERODB_PROJECT_ID=prod_project_id
railway variables set ZERODB_API_KEY=prod_api_key
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
railway variables set DEBUG=false

# Deploy to production
railway up
```

---

## Cost Optimization

**Railway Pricing:**
- Free tier: $5 credit/month
- Hobby: $5/month + usage
- Pro: $20/month + usage

**Cost Optimization Tips:**
1. Use staging for testing, production for live traffic
2. Enable auto-sleep for staging (Railway settings)
3. Monitor usage in Railway dashboard
4. Use ZeroDB efficiently (batch operations)
5. Set up proper caching if needed

---

## Security Best Practices

1. **Never commit secrets to git**
   - Use `.env.example` template only
   - All secrets via Railway environment variables

2. **Rotate secrets regularly**
   - Generate new `SECRET_KEY` every 90 days
   - Rotate ZeroDB API keys if compromised

3. **Use separate environments**
   - Staging uses test ZeroDB project
   - Production uses production ZeroDB project

4. **Enable HTTPS only**
   - Railway provides HTTPS by default
   - Never disable HTTPS in production

5. **Monitor access logs**
   - Review Railway logs regularly
   - Set up alerts for unusual patterns

---

## Support and Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **ZeroDB Docs:** https://www.ainative.studio/docs
- **Ocean Backend Issues:** https://github.com/AINative-Studio/ocean-backend/issues

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing locally
- [ ] Code reviewed and merged to main
- [ ] Environment variables configured
- [ ] Railway project created
- [ ] GitHub secrets configured
- [ ] Documentation updated

### Deployment

- [ ] Push to main triggers GitHub Actions
- [ ] Tests pass in CI
- [ ] Deployment succeeds
- [ ] Health check passes
- [ ] Smoke tests pass

### Post-Deployment

- [ ] Verify staging URL works
- [ ] Test all API endpoints
- [ ] Check Railway logs for errors
- [ ] Monitor metrics for 24 hours
- [ ] Update team on deployment status

---

**Last Updated:** 2024-12-24
**Status:** Ready for deployment
**Issue:** #21
