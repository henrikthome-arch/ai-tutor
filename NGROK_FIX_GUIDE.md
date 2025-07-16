# 🔧 ngrok Setup Fix

## Issue: Sophos Antivirus Blocking ngrok

**Root Cause:** Sophos antivirus is blocking ngrok.exe (common with enterprise antivirus)

The error shows two problems:
1. **Permission issue** - Sophos/Windows is blocking ngrok.exe
2. **Wrong command syntax** - Missing the `authtoken` subcommand

## Quick Fix Steps:

### Step 1: Sophos Antivirus Workaround

**Option A: Whitelist ngrok in Sophos**
1. Open Sophos Central/Endpoint
2. Go to "Threat Protection" → "Exclusions"
3. Add `C:\Users\henri\Dropbox\Temp\ngrok.exe` to exclusions
4. Save and restart

**Option B: Use Alternative Location**
1. Create folder: `C:\tools\ngrok\`
2. Move ngrok.exe there
3. Add to Windows Defender exclusions (if dual protection)

**Option C: Run PowerShell as Administrator**
1. Right-click PowerShell → "Run as Administrator"
2. Navigate to your ngrok folder: `cd C:\Users\henri\Dropbox\Temp`

### Step 2: Correct Command Syntax
Your token: `2zxKBJWS1HoIX08zBwV3EBwW9zG_4eqPsW3HcuBKr56u4KHQo`

**Correct commands:**
```powershell
# First, authenticate (run this once)
.\ngrok.exe authtoken 2zxKBJWS1HoIX08zBwV3EBwW9zG_4eqPsW3HcuBKr56u4KHQo

# Then start the tunnel
.\ngrok.exe http 3000
```

### Step 3: Sophos-Friendly Alternatives (Recommended)

**🌟 BEST OPTION: LocalTunnel** (Usually not blocked by Sophos)
```powershell
# Install Node.js first from https://nodejs.org
# Then install localtunnel:
npm install -g localtunnel

# Start tunnel:
lt --port 3000
# Will give you URL like: https://abc-123.loca.lt
```

**Option B: Cloudflare Tunnel** (Free, enterprise-friendly)
```powershell
# Download cloudflared.exe from GitHub
# https://github.com/cloudflare/cloudflared/releases
# Place in C:\tools\cloudflared\

# Run tunnel:
cloudflared tunnel --url http://localhost:3000
```

**Option C: SSH Tunnel** (If you have a VPS/server)
```powershell
# Using PuTTY or OpenSSH
ssh -R 3000:localhost:3000 user@your-server.com
```

**Option D: Install ngrok differently**
```powershell
# Via winget (may bypass Sophos)
winget install ngrok

# Via chocolatey (may bypass Sophos)
choco install ngrok
```

### Step 4: Test Connection

After authentication, run:
```powershell
.\ngrok.exe http 3000
```

You should see:
```
ngrok by @inconshreveable

Session Status                online
Account                      (your email)
Version                      3.x.x
Region                       United States (us)
Forwarding                   https://abc123.ngrok.io -> http://localhost:3000
Forwarding                   http://abc123.ngrok.io -> http://localhost:3000

Connections                  ttl     opn     rt1     rt5     p50     p90
                             0       0       0.00    0.00    0.00    0.00
```

**📋 Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Step 5: Test Your Tunnel

Open browser and visit: `https://YOUR_NGROK_URL.ngrok.io/health`

Should return: `{"status": "healthy", "server": "Python AI Tutor Server"}`

## Alternative Solutions

### Option A: 🚀 Use LocalTunnel (RECOMMENDED for Sophos)
LocalTunnel is rarely blocked by corporate antivirus:

1. **Install Node.js:** https://nodejs.org (LTS version)
2. **Install LocalTunnel:**
   ```powershell
   npm install -g localtunnel
   ```
3. **Start tunnel:**
   ```powershell
   lt --port 3000
   ```
4. **Copy the URL** (e.g., `https://abc-123.loca.lt`)

### Option B: Use Cloudflare Tunnel (Enterprise-friendly)
```powershell
# Download from: https://github.com/cloudflare/cloudflared/releases
# Get cloudflared-windows-amd64.exe, rename to cloudflared.exe
cloudflared tunnel --url http://localhost:3000
```

### Option C: Test Locally First
You can test the OpenAI Assistant setup using `http://localhost:3000` first, but it won't work with OpenAI's servers. This is just for local testing of the data flow.

### Option D: Corporate Network Bypass
If your company blocks all tunneling:
1. **Mobile Hotspot:** Connect to phone's internet
2. **VPN:** Use approved corporate VPN
3. **Home Network:** Work from home for testing

## ✅ Next Steps

Once you have a working tunnel URL (from LocalTunnel, Cloudflare, or ngrok):

1. **Test the tunnel:** Visit `https://YOUR-TUNNEL-URL/health`
2. **Should return:** `{"status": "healthy", "server": "Python AI Tutor Server"}`
3. **Continue with OpenAI Assistant setup** from `FINAL_SETUP_GUIDE.md` using your tunnel URL

## 🎯 Recommended Path for Sophos Users:
1. ✅ Try LocalTunnel first (least likely to be blocked)
2. ✅ If blocked, try Cloudflare Tunnel
3. ✅ If both blocked, request IT to whitelist tunneling tools
4. ✅ Last resort: Use mobile hotspot for initial testing