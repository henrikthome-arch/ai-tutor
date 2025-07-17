# 🚀 Railway.app Deployment Guide

## Why Railway? (Recommended)

**Railway.app is the best choice because:**
- ✅ **Fastest deployment** - 2-3 minutes from GitHub to live URL
- ✅ **More generous free tier** - $5/month credit, no sleep limitations
- ✅ **Simpler interface** - Less configuration needed
- ✅ **Better Python support** - Automatic detection and setup
- ✅ **Reliable uptime** - No cold starts or sleeping like Heroku
- ✅ **Automatic HTTPS** - Secure by default

**vs Render.com:**
- Render has 750 hour/month limit on free tier
- Render apps "sleep" after 15 minutes of inactivity
- Railway keeps your app alive longer

---

## 📋 Step-by-Step Railway Deployment

### Step 1: Prepare Your Code
✅ Already done! You have:
- [`simple-server-fixed.py`](simple-server-fixed.py) - Your server
- [`requirements.txt`](requirements.txt) - Dependencies
- [`Procfile`](Procfile) - Start command
- `data/` folder - All your student data

### Step 2: Create GitHub Repository
1. **Initialize Git** (if not already):
   ```bash
   git init
   git add .
   git commit -m "AI Tutor System - Initial commit"
   ```

2. **Create GitHub repo**:
   - Go to https://github.com/new
   - Name: `ai-tutor-system`
   - Make it Private (contains student data)
   - Don't initialize with README

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/ai-tutor-system.git
   git branch -M main
   git push -u origin main
   ```

### Step 3: Deploy to Railway
1. **Go to Railway**: https://railway.app
2. **Sign up** with GitHub account
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your `ai-tutor-system` repository**
6. **Railway will automatically:**
   - Detect Python app
   - Install requirements.txt
   - Use Procfile for startup
   - Assign a public URL

### Step 4: Get Your URL
After deployment (2-3 minutes):
1. Click on your project
2. Go to "Settings" → "Domains"
3. Copy the Railway URL (e.g., `https://ai-tutor-system-production.up.railway.app`)

### Step 5: Test Your Deployed Server
Visit these URLs:
- **Health check**: `https://your-railway-url.railway.app/health`
- **Student data**: `https://your-railway-url.railway.app/mcp/get-student-context?student_id=emma_smith`

---

## 🔧 Configuration Details

### Port Configuration
Railway automatically sets the `PORT` environment variable. Your server should use:
```python
port = int(os.environ.get('PORT', 3000))
```

**✅ Good news:** Your [`simple-server-fixed.py`](simple-server-fixed.py) already handles this correctly!

### Environment Variables (if needed)
In Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add any needed environment variables

---

## 📱 Quick Commands

```bash
# Initialize and deploy (run these in your project folder)
git init
git add .
git commit -m "AI Tutor System"

# Add your GitHub repo URL here
git remote add origin https://github.com/YOUR-USERNAME/ai-tutor-system.git
git push -u origin main

# Then deploy on Railway website
```

---

## 🎯 After Deployment

1. **✅ Test your Railway URL**
2. **📝 Update [`ai_tutor_integration.py`](ai_tutor_integration.py)**:
   ```python
   TUNNEL_URL = "https://your-railway-url.railway.app"
   ```
3. **🤖 Create OpenAI Assistant** with your Railway URL
4. **🎉 Start tutoring!**

---

## 💡 Pro Tips

- **Free tier**: $5/month credit (very generous for this app)
- **Custom domain**: Add your own domain in Railway settings
- **Logs**: View real-time logs in Railway dashboard
- **Auto-deploys**: Every GitHub push automatically deploys
- **Scaling**: Easy to upgrade when you need more resources

**Deployment time: ~5 minutes total!**

---

## 🚨 Important Notes

- **Keep repo private** - Contains student data
- **Test thoroughly** - Verify all endpoints work
- **Monitor usage** - Check Railway dashboard for resource usage
- **Backup data** - Your GitHub repo is your backup

Your AI tutor will be live on the internet and ready for OpenAI integration!