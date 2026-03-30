# 🚀 Deployment Guide (Free Tier)

Deploy your Malaysia Fuel Dashboard in 5 minutes using Render + Vercel (both free!)

---

## **Option 1: Deploy to Render (Backend API)**

### Step 1: Push to GitHub
```bash
cd /home/zafri/.openclaw/workspace
git remote add origin https://github.com/yourusername/malaysia-fuel-dashboard.git
git push -u origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repo
5. Select the repo
6. Fill in:
   - **Name:** malaysia-fuel-api
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Add Environment Variables:
   ```
   ENVIRONMENT=production
   SECRET_KEY=(auto-generated)
   CORS_ORIGINS=https://yourdomain.vercel.app
   ```
8. Click "Create Web Service"
9. Wait ~5 min for deployment

**Your API URL will be:** `https://malaysia-fuel-api.onrender.com`

### Step 3: Database on Render
1. In Render dashboard, click "New" → "PostgreSQL"
2. Name: `fuel-db`
3. Copy the connection string
4. Add to Web Service environment variable:
   ```
   DATABASE_URL=(your-connection-string)
   ```

---

## **Option 2: Deploy Frontend to Vercel**

### Step 1: Push Frontend Folder
```bash
cd /home/zafri/.openclaw/workspace/projects/malaysia-fuel-dashboard
git add frontend/
git commit -m "feat: add React dashboard frontend"
git push
```

### Step 2: Deploy on Vercel
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Import Project"
4. Select your repo
5. Configure:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Start Command:** `npm start`
6. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://malaysia-fuel-api.onrender.com
   ```
7. Click "Deploy"

**Your dashboard URL will be:** `https://yourusername-fuel-dashboard.vercel.app`

---

## **Step-by-Step (Copy-Paste)**

### Push to GitHub
```bash
# In your workspace
git remote add origin https://github.com/yourusername/malaysia-fuel-dashboard.git
git branch -M main
git push -u origin main
```

### Render (API)
```
1. Visit render.com
2. "New Web Service"
3. Connect GitHub → select repo
4. Fill:
   - Name: malaysia-fuel-api
   - Build: pip install -r backend/requirements.txt
   - Start: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
5. Environment:
   - ENVIRONMENT=production
   - SECRET_KEY=generate_this_yourself
   - CORS_ORIGINS=https://your-vercel-url.vercel.app
6. Deploy!
```

### Vercel (Frontend)
```
1. Visit vercel.com
2. "Import Project"
3. Select repo
4. Root Directory: frontend
5. Environment:
   - NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com
6. Deploy!
```

---

## **After Deployment**

1. **Test API:**
   ```
   https://malaysia-fuel-api.onrender.com/health
   ```

2. **Test Dashboard:**
   ```
   https://your-username-fuel-dashboard.vercel.app
   ```

3. **View API Docs:**
   ```
   https://malaysia-fuel-api.onrender.com/docs
   ```

---

## **Troubleshooting**

### API not working
- Check CORS_ORIGINS is set correctly
- Verify DATABASE_URL is set in Render
- Check Render logs: dashboard → service → logs

### Dashboard not loading
- Verify NEXT_PUBLIC_API_URL points to Render API
- Check browser console for CORS errors
- Test API health endpoint manually

### Database connection failed
- Make sure PostgreSQL is created on Render
- Copy correct connection string
- Set DATABASE_URL in API service

---

## **Costs**

- **Render (API + DB):** FREE (free tier with limits)
- **Vercel (Frontend):** FREE (free tier)

**Total:** $0/month 🎉

---

## **Next Steps**

1. Add real fuel price data (implement scrapers)
2. Setup automatic price updates (Celery tasks)
3. Add email alerts
4. Mobile app (React Native)

**You're live!** 🚀🇲🇾
