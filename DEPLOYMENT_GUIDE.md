# 🚀 Synapse Deployment Guide

## Step-by-Step Deployment Instructions

### Part 1: Frontend Deployment (Vercel)

#### Prerequisites
- GitHub account with synapse repo pushed
- Vercel account (free at vercel.com)

#### Steps

**1. Connect GitHub to Vercel**
```
1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Select "Continue with GitHub"
4. Authorize Vercel to access your GitHub
5. Find and select "iamsoura005/Synapse"
```

**2. Configure Build Settings**
```
Project Name: synapse (or your choice)
Framework Preset: Next.js
Root Directory: frontend/web
Build Command: npm run build
Output Directory: .next
Development Command: npm run dev
```

**3. Add Environment Variables**
```
Click "Environment Variables"
Add new variable:
  Name: NEXT_PUBLIC_API_URL
  Value: http://localhost:8010  (for now)
  
Later, after backend deployment:
  Value: https://your-backend-api.railway.app
```

**4. Deploy**
```
Click "Deploy"
Wait for build to complete (~2-3 minutes)
You'll get a Vercel URL: https://synapse-xxx.vercel.app
```

#### Post-Deployment
- Test at: https://synapse-xxx.vercel.app
- Any push to `main` branch auto-deploys
- Update `NEXT_PUBLIC_API_URL` env var with your backend URL

---

### Part 2: Backend Deployment (Railway)

#### Prerequisites
- GitHub account with synapse repo pushed
- Railway account (free at railway.app)
- PostgreSQL database (create in Railway)

#### Steps

**1. Connect GitHub to Railway**
```
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to GitHub
5. Select "iamsoura005/Synapse"
```

**2. Configure Build Settings**
```
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**3. Add PostgreSQL Service**
```
1. In Railway dashboard, click "Add Service"
2. Select "+ Add"
3. Select "PostgreSQL"
4. Railway creates DB automatically
5. Environment variables auto-populated:
   - DATABASE_URL
   - POSTGRES_DB
   - POSTGRES_PASSWORD
   - POSTGRES_USER
```

**4. Configure Environment Variables**
```
Click "Variables" tab
Add these variables:

DEMO_MODE=false
FRONTEND_ORIGINS=https://synapse-xxx.vercel.app
JWT_SECRET_KEY=<generate-secure-32-char-key>

# AI Keys (optional for demo)
GEMINI_API_KEY=
TAVILY_API_KEY=

# OAuth (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=

# Blockchain (optional)
POLYGON_RPC_URL=https://polygon-rpc.com
POLYGON_PRIVATE_KEY=

# The DATABASE_URL is already set by PostgreSQL service
```

**5. Deploy**
```
Railway auto-deploys on push to main
Wait for build (~3-5 minutes)
You'll get a Railway URL: https://synapse-xxxx.railway.app
```

#### Post-Deployment
```
1. Test backend health:
   curl https://synapse-xxxx.railway.app/health

2. View API docs:
   https://synapse-xxxx.railway.app/docs

3. Update Vercel frontend env var:
   NEXT_PUBLIC_API_URL=https://synapse-xxxx.railway.app

4. Any push to `main` branch auto-deploys
```

---

### Part 3: Production Verification Checklist

#### Frontend (Vercel)
- [ ] Dashboard loads at https://synapse-xxx.vercel.app
- [ ] Can view relationships list
- [ ] Can view negotiations list
- [ ] Can view contracts list
- [ ] Integration toggles appear
- [ ] No CORS errors in console
- [ ] API calls show correct backend URL

#### Backend (Railway)
- [ ] Health check: `curl https://api.railway.app/health`
- [ ] Returns: `{"status": "ok", "mode": "production"}`
- [ ] API docs available: /docs endpoint
- [ ] Database connected: No DB errors in logs
- [ ] Relationships endpoint responds: `/api/v1/relationships?user_id=test`
- [ ] Negotiations endpoint responds: `/api/v1/negotiations?user_id=test`
- [ ] Contracts endpoint responds: `/api/v1/contracts?user_id=test`

#### Full Integration
- [ ] Frontend loads without errors
- [ ] Dashboard fetches real data from API
- [ ] Creating relationships works
- [ ] Approving negotiations works
- [ ] Manual negotiation creation works
- [ ] Contract creation works
- [ ] Integration toggles work

---

## 🔄 Auto-Deployment Pipeline

### How It Works

```
Your Computer
     ↓
  git push
     ↓
GitHub (main branch)
     ↓
┌─────────────────────┬──────────────────┐
│                     │                  │
↓                     ↓                  ↓
Vercel (Frontend)   Railway (Backend)   Tests
     ↓                    ↓              ↓
Auto-build         Auto-build        (optional)
Auto-test          Auto-deploy
Auto-deploy             ↓
     ↓            New version live
New URL
```

**Deployment Times:**
- Frontend: 2-3 minutes
- Backend: 3-5 minutes
- Full cycle: 5-8 minutes

### Triggering Deployments

**Manual trigger in Vercel:**
```
1. Dashboard → Select project
2. Deployments tab
3. Click "..." on latest commit
4. Select "Redeploy"
```

**Manual trigger in Railway:**
```
1. Dashboard → Select project
2. Deployments tab
3. Click "Deploy" button next to latest
```

**Automatic (on push to main):**
```
git add .
git commit -m "Your message"
git push origin main
# Both services auto-deploy in ~5-8 minutes
```

---

## 🐛 Troubleshooting

### Frontend Issues

**CORS Error in Console**
```
Error: Access to XMLHttpRequest blocked by CORS policy

Solution:
1. Check FRONTEND_ORIGINS in Railway backend env
2. Should include: https://synapse-xxx.vercel.app
3. Wait 1-2 mins for Railway to restart with new env
```

**API Returns 404**
```
Error: 404 Not Found when calling /api/v1/...

Solution:
1. Verify backend is running: curl {backend-url}/health
2. Check if DEMO_MODE=false in Railway env
3. Verify PostgreSQL is connected
```

**Blank Dashboard**
```
Page loads but no data appears

Solution:
1. Open browser DevTools (F12) → Console
2. Look for error messages
3. Check Network tab → API requests
4. Verify NEXT_PUBLIC_API_URL in Vercel env
```

### Backend Issues

**Database Connection Error**
```
Error: could not connect to server

Solution:
1. Go to Railway dashboard
2. Click PostgreSQL service
3. Verify status is "Running"
4. Check DATABASE_URL in env vars
5. Restart the backend service
```

**Build Failed**
```
Error during deployment

Solution:
1. Click "View Logs" in Railway
2. Look for error message
3. Common: Missing Python packages
   → Push backend/requirements.txt with all deps
```

**Health Check Shows "demo" Mode**
```
{"status": "ok", "mode": "demo"}

Solution:
1. Set DEMO_MODE=false in Railway env
2. Wait for service to restart
3. Check: curl {url}/health
```

### Database Issues

**No Data Persisting**
```
Solution:
1. Ensure DEMO_MODE=false
2. Verify DATABASE_URL points to PostgreSQL
3. Run migrations (if needed)
```

**Database Out of Space**
```
Solution:
1. Rails Dashboard → PostgreSQL → Metrics
2. Check disk usage
3. May need to upgrade plan
```

---

## 🔐 Environment Variables Reference

### Critical for Production

| Variable | Value | Required |
|----------|-------|----------|
| `DEMO_MODE` | `false` | ✓ Yes |
| `DATABASE_URL` | PostgreSQL URL | ✓ Yes |
| `FRONTEND_ORIGINS` | Your Vercel URL | ✓ Yes |
| `JWT_SECRET_KEY` | 32-char random | ✓ Yes |

### Optional but Recommended

| Variable | Value | For Feature |
|----------|-------|------------|
| `GEMINI_API_KEY` | Google API key | AI insights |
| `TAVILY_API_KEY` | Tavily key | Search integration |
| `POLYGON_RPC_URL` | RPC endpoint | Blockchain proofs |
| `REDIS_URL` | Redis URL | Fast caching |
| `NEO4J_URI` | Neo4j URL | Graph queries |

### Generate Secure Keys

**JWT_SECRET_KEY (32 chars):**
```bash
# Linux/Mac
openssl rand -hex 16

# Windows (Python)
python -c "import secrets; print(secrets.token_hex(16))"
```

---

## 📊 Monitoring

### Vercel Dashboard
- Real-time analytics
- Request metrics
- Error tracking
- Performance insights

### Railway Dashboard
- Log viewer
- Metrics (CPU, Memory, Network)
- Deployment history
- Service status

### Manual Monitoring

**Backend Health:**
```bash
curl https://your-backend.railway.app/health
# Should return: {"status": "ok", "mode": "production"}
```

**Check Logs:**
```bash
# Railway: Dashboard → Logs tab
# Vercel: Dashboard → Deployments → View Logs
```

---

## 🎯 Next Steps

1. Deploy frontend to Vercel
2. Deploy backend to Railway
3. Update FRONTEND_ORIGINS in Railway with Vercel URL
4. Update NEXT_PUBLIC_API_URL in Vercel with Railway URL
5. Test full integration
6. Monitor logs for any issues
7. Set up monitoring alerts (optional)

**Estimated Time: 15-20 minutes**

Good luck! 🚀
