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

## ✅ Step 2: Create New Web Service

1. **Click "New +"** → **"Web Service"**
2. **Connect Repository:** Select `henrikthome-arch/ai-tutor`
3. **Configure deployment:**

```
Name: ai-tutor
Environment: Python 3
Region: Oregon (US West) or Frankfurt (Europe)
Branch: main
Root Directory: (leave empty)
Build Command: pip install -r requirements.txt
Start Command: python simple-server-fixed.py
```

---

## ✅ Step 3: Deploy & Get URL

1. **Click "Create Web Service"**
2. **Wait for deployment** (2-3 minutes)
3. **Your app will be live at:** `https://ai-tutor.onrender.com` (or similar)
4. **Copy your Render URL**

---

## ✅ Step 4: Test Your Deployed System

**Test these URLs (replace with your actual Render URL):**

```
Health Check:
https://ai-tutor.onrender.com/health
Expected: {"status": "healthy", "server": "Python AI Tutor Server"}

Student Data:
https://ai-tutor.onrender.com/mcp/get-student-context?student_id=emma_smith
Expected: Complete Emma Smith profile, progress, and curriculum data
```

---

## ✅ Step 5: Update Integration Script

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
✅ **Health endpoint returns server status**  
✅ **Student data endpoint returns Emma's profile**  
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

---

## 🔧 Troubleshooting

**If deployment fails:**
1. Check logs in Render dashboard
2. Verify `requirements.txt` exists
3. Ensure `simple-server-fixed.py` is in root directory

**If endpoints don't work:**
1. Check if app is running in Render dashboard
2. Verify the correct port configuration
3. Test health endpoint first

Your AI tutor system will be live on the internet in just a few minutes!