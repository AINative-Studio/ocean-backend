# Railway Quick Start Guide

## 5-Minute Railway Deployment

This guide will get your Ocean backend deployed to Railway in 5 minutes.

### Prerequisites

- Railway account: https://railway.app
- Railway CLI: `npm install -g @railway/cli`
- ZeroDB credentials (project ID and API key)

### Quick Deploy

**Option 1: Automated Script** (Recommended)

```bash
cd /Users/aideveloper/ocean-backend
./scripts/railway_setup.sh
```

This script will:
1. Check Railway CLI installation
2. Prompt for environment variables
3. Generate secret key
4. Configure Railway environment
5. Deploy your application
6. Run smoke tests

**Option 2: Manual Setup**

```bash
# 1. Login to Railway
railway login

# 2. Create project
railway init
# Name: ocean-backend-staging

# 3. Link GitHub repo (via Railway dashboard)
# Go to https://railway.app/new
# Click "Deploy from GitHub repo"
# Select: AINative-Studio/ocean-backend

# 4. Set environment variables
railway variables set ZERODB_API_URL=https://api.ainative.studio
railway variables set ZERODB_PROJECT_ID=your_project_id
railway variables set ZERODB_API_KEY=your_api_key
railway variables set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 5. Deploy
railway up

# 6. Get your URL
railway domain
```

### Verify Deployment

```bash
# Set your Railway URL
export RAILWAY_STAGING_URL=https://your-app.up.railway.app

# Run smoke tests
./scripts/smoke_tests.sh
```

Expected output:
```
✓ All smoke tests passed!

Deployment is ready for use:
  - API: https://your-app.up.railway.app
  - Docs: https://your-app.up.railway.app/docs
  - Health: https://your-app.up.railway.app/health
```

### Common Issues

**Issue: "Railway CLI not found"**
```bash
npm install -g @railway/cli
```

**Issue: "Environment variable not set"**
```bash
railway variables list  # Check current variables
railway variables set VARIABLE_NAME=value
```

**Issue: "Health check failing"**
```bash
railway logs  # Check application logs
railway status  # Check deployment status
```

### Next Steps

1. **Set up CI/CD**: Push to main branch triggers auto-deploy
2. **Configure domain**: `railway domain` or add custom domain
3. **Monitor**: Check Railway dashboard for metrics and logs
4. **Production**: Create production environment with `railway environment create production`

### Support

- **Documentation**: See `docs/DEPLOYMENT.md` for full guide
- **Railway Docs**: https://docs.railway.app
- **Issues**: https://github.com/AINative-Studio/ocean-backend/issues
