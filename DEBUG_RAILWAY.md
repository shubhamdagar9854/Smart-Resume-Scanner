# 🚨 Railway Debug Guide

## ❌ Error: "Application failed to respond"

## 🔍 Debug Steps:

### Step 1: Check Railway Logs
1. Go to Railway dashboard
2. Click on your project
3. Go to "Logs" tab
4. Check error messages

### Step 2: Common Issues & Fixes

#### Issue 1: Port Problem
**Error:** App running on wrong port
**Fix:** Add port binding to app.py

#### Issue 2: Missing Dependencies  
**Error:** Module not found
**Fix:** Update requirements.txt

#### Issue 3: Database Permission
**Error:** Can't create database
**Fix:** Fix database path

#### Issue 4: Environment Variables
**Error:** Missing env vars
**Fix:** Add proper environment variables

### Step 3: Quick Fixes to Try

#### Fix 1: Add Port Binding
```python
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

#### Fix 2: Update Requirements
```
Flask==2.3.3
PyPDF2==3.0.1
python-docx==0.8.11
Werkzeug==2.3.7
cloudinary==1.41.0
gunicorn==23.0.0
```

#### Fix 3: Add Environment Variables
In Railway dashboard:
```
PYTHON_VERSION=3.9.0
FLASK_ENV=production
PORT=5000
```

### Step 4: Check Specific Error
Look for these in logs:
- "ModuleNotFoundError"
- "Permission denied"  
- "Address already in use"
- "Database locked"

## 🎯 Action Plan:
1. Check Railway logs for specific error
2. Apply appropriate fix
3. Redeploy
4. Test again
