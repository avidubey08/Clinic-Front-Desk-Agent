# 100% Free Deployment Guide (Vercel / Netlify + Render)

This guide shows you how to host both the **Python FastAPI Backend** and the **React Frontend** online with **zero cost ($0.00)** and **no credit card required**.

---

## 🎯 Architecture Overview

```
[ User Browser ]
       │
       ├──► Frontend (React / Vite)   ──► Hosted on Vercel or Netlify (100% Free)
       │
       └──► Backend (Python FastAPI)  ──► Hosted on Render.com (100% Free Web Service)
```

---

## 🛠️ Step 1: Push Code to GitHub

Make sure your project is pushed to a public GitHub repository:

```bash
git add .
git commit -m "feat: complete SwasthiQ Clinic Front Desk Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

---

## 🐍 Step 2: Deploy Backend to Render.com (100% Free, No Card Needed)

1. Go to [https://render.com](https://render.com) and click **Sign Up with GitHub**.
2. Click the **"New +"** button in the top right and select **"Web Service"**.
3. Connect your GitHub repository (`YOUR_REPO_NAME`).
4. Fill in the deployment settings:
   - **Name**: `sunrise-clinic-backend` (or any name you choose)
   - **Region**: Choose the closest region (e.g. *Singapore* or *Frankfurt*)
   - **Branch**: `main`
   - **Root Directory**: *(leave blank)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Select **Free ($0/month)**
5. Click **"Deploy Web Service"**.
6. Wait 1–2 minutes for the build to finish.
7. Copy your live backend URL from the top of the page.  
   *(Example: `https://sunrise-clinic-backend.onrender.com`)*

> **Verification**: Open `https://your-backend.onrender.com/docs` in your browser. You should see the interactive Swagger API documentation.

---

## ⚡ Step 3: Deploy Frontend to Vercel OR Netlify

You can choose either Vercel or Netlify. Both are 100% free.

### Option A: Deploy on Vercel (Recommended)

1. Go to [https://vercel.com](https://vercel.com) and **Log In with GitHub**.
2. Click **"Add New..."** -> **"Project"**.
3. Find your repository and click **"Import"**.
4. In the configuration screen:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select **`frontend`**
   - **Build Command**: `npm run build` *(default)*
   - **Output Directory**: `dist` *(default)*
5. Expand the **"Environment Variables"** section and add:
   - **Key**: `VITE_API_URL`
   - **Value**: Your live backend URL from Step 2 (e.g. `https://sunrise-clinic-backend.onrender.com`)
   *(Do NOT include a trailing slash `/`)*
6. Click **"Deploy"**.
7. In ~30 seconds, Vercel gives you your live link!  
   *(Example: `https://sunrise-clinic.vercel.app`)*

---

### Option B: Deploy on Netlify

1. Go to [https://netlify.com](https://netlify.com) and **Log In with GitHub**.
2. Click **"Add new site"** -> **"Import an existing project"** -> **"GitHub"**.
3. Select your repository.
4. Configure the build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
5. Expand **"Environment variables"** and add:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://sunrise-clinic-backend.onrender.com`
6. Click **"Deploy site"**.
7. In ~30 seconds, Netlify gives you your live link!

---

## ✅ Step 4: Test Your Live App

1. Open your live frontend URL in your browser.
2. You will see the **Handoff Queue** and **Conversation Detail** screens.
3. Click the floating **"📞 Talk to AI Receptionist"** button in the bottom right corner.
4. Say:
   > *"Dr. Rao ke saath appointment chahiye tha kal subah."*
5. The live frontend will call your live Render backend, run the ground truth tools, and respond in real time!

---

## 📌 Checklist for Your Email Submission

When submitting to `hiring@swasthiq.in`:
- **Repository URL**: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME`
- **Live App URL**: `https://YOUR_APP.vercel.app`
- **Video Link**: Loom / Google Drive link
