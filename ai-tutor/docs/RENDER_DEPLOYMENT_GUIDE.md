# 🚀 Render.com Deployment - Step by Step

## 🎯 Quick Deploy to Render.com (5 minutes)

Railway.app changed their free tier, but Render.com offers an excellent alternative with a generous free plan.

---

## ✅ Step 1: Sign Up to Render.com

1. **Go to:** https://render.com
2. **Click "Get Started"**
3. **Sign up with GitHub** (connects to your `henrikthome-arch/ai-tutor` repo)
4. **Authorize Render** to access your repositories

---

## ✅ Step 2: Create PostgreSQL Database

1. **Click "New +"** → **"PostgreSQL"**
2. **Configure database:**
   ```
   Name: ai-tutor-db
   Database: ai_tutor
   User: (leave default)
   Region: Oregon (US West) or Frankfurt (Europe)
   PostgreSQL Version: 14
   Plan Type: Free
   ```
3. **Click "Create Database"**
4. **Wait for creation** (2-3 minutes)
5. **Copy the Internal Database URL** (you'll need this for your web service)
6. **Important**: Change `postgres://` to `postgresql://` in the URL for SQLAlchemy compatibility

---

## ✅ Step 3: Create New Web Service

1. **Click "New +"** → **"Web Service"**
2. **Connect Repository:** Select `henrikthome-arch/ai-tutor`
3. **Configure deployment:**

```
Name: ai-tutor
Environment: Python 3
Region: (same as your database)
Branch: main
Root Directory: (leave empty)
Build Command: pip install -r requirements.txt && python -m flask db upgrade
Start Command: python run.py
```

**Important**: Ensure your `requirements.txt` includes `Flask-Migrate` for database migrations. The application will automatically handle database migrations during startup, but the build command also includes a migration step to ensure tables are created before the application starts.

4. **Add Environment Variables**:
   - Click "Advanced" → "Add Environment Variable"
   - Add `DATABASE_URL` with the value of your Internal Database URL (with `postgresql://`)
   - Add other required environment variables from `config/render-production.env`
   - Set `FLASK_ENV` to `production`

---

## ✅ Step 4: Deploy & Get URL

1. **Click "Create Web Service"**
2. **Wait for deployment** (2-3 minutes)
3. **Your app will be live at:** `https://ai-tutor.onrender.com` (or similar)
4. **Copy your Render URL**

---

## ✅ Step 5: Set Up Persistent Disk

1. **Go to your web service** in the Render dashboard
2. **Navigate to "Disks"** in the sidebar
3. **Click "New Disk"**
4. **Configure disk:**
   ```
   Name: ai-tutor-data
   Mount Path: /opt/render/project/src/ai-tutor/data
   Size: 1 GB (or more as needed)
   ```
5. **Click "Create Disk"**
6. **Trigger a new deployment** for the changes to take effect

---

## ✅ Step 6: Test Your Deployed System

**Test these URLs (replace with your actual Render URL):**

```
Health Check:
https://ai-tutor.onrender.com/health
Expected: {"status": "healthy"}

Admin Dashboard:
https://ai-tutor.onrender.com/admin
Expected: Login page for the admin dashboard
```

---

## ✅ Step 7: Update Integration Script

Edit [`ai_tutor_integration.py`](ai_tutor_integration.py) line 13:

```python
# Replace this line:
TUNNEL_URL = ""

# With your Render URL:
TUNNEL_URL = "https://ai-tutor.onrender.com"  # Your actual Render URL
```

---

## 🎉 Success Criteria

✅ **Render deployment successful**  
✅ **PostgreSQL database connected**  
✅ **Persistent disk configured**  
✅ **Health endpoint returns server status**  
✅ **Admin dashboard accessible**  
✅ **Integration script updated with Render URL**  

**Next:** Create OpenAI Assistant using your Render URL!

---

## 💡 Render.com Free Tier Benefits

- **750 hours/month** (enough for development and testing)
- **Automatic HTTPS** and SSL certificates
- **GitHub integration** for automatic deploys
- **No sleep after 15 minutes** (unlike some platforms)
- **Custom domains** available
- **Same workflow** as Railway but actually free
- **Free PostgreSQL database** (1 GB storage)

---

## 🔧 Troubleshooting

**If deployment fails:**
1. Check logs in Render dashboard
2. Verify `requirements.txt` exists
3. Ensure `run.py` is in root directory

**If database connection fails:**
1. Check the `DATABASE_URL` environment variable
2. Ensure you changed `postgres://` to `postgresql://`
3. Verify the database is running in the Render dashboard

**If persistent disk issues:**
1. Verify the mount path is correct
2. Check if the disk is properly attached
3. Trigger a new deployment after creating the disk

Your AI tutor system will be live on the internet in just a few minutes!