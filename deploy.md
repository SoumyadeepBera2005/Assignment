# 🚀 Quick Deployment Guide: Vercel & Render (Zero Config Files)

This guide shows how to deploy your **Home Credit AI Voice Agent** using **Vercel** for the frontend and **Render** for the Python FastAPI backend **without needing any configuration files** (`render.yaml` and `vercel.json` are NOT required).

---

## 🔍 Why Did Vercel Show "404 NOT FOUND"?

If you saw the Vercel error:
```
This page doesn't exist
404: NOT_FOUND
```
**The Cause:** Vercel looks for `index.html` at the **root of your repository** (`./index.html`). Because `index.html` was previously located inside the `static/` subfolder, Vercel could not find a default entry page to serve.

**The Fix:** We have added `index.html` directly to the project root. Once pushed to GitHub, Vercel will automatically detect and serve your dashboard with **zero configuration required**!

---

## 🛠️ Step 1: Push Code to GitHub

Open your terminal in the project directory and push the updated files:

```bash
git add .
git commit -m "Add root index.html and enable direct Render connection"
git push origin main
```

---

## 🐍 Step 2: Deploy Backend on Render (Web Service)

Render hosts your Python FastAPI agent, maintains in-memory conversation state, and handles API requests.

1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** ➔ **Web Service**.
2. Connect your GitHub repository: `SoumyadeepBera2005/Assignment`.
3. Set the service details:
   - **Name**: `home-credit-voice-agent` (or any name you choose)
   - **Region**: Closest to you (e.g., `Singapore` or `Frankfurt`)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: **Free**
4. Under **Environment Variables**, add:
   - `AGENT_NAME`: `Priya`
   - `COMPANY_NAME`: `Home Credit`
   - `MAX_LOAN_LIMIT`: `7500000`
   - `PYTHON_VERSION`: `3.10.12`
   - *(Optional)* `GEMINI_API_KEY`: *(your Gemini key if using LLM)*
   - *(Optional)* `RETELL_API_KEY`: *(your Retell key if using telephony)*
5. Click **Deploy Web Service**.
6. When deployment finishes, copy your live backend URL (e.g. `https://home-credit-voice-agent.onrender.com`).

> **Verify Backend:** Open `https://<YOUR-RENDER-URL>.onrender.com/docs` to see the live Swagger API docs.

---

## 🌐 Step 3: Deploy Frontend on Vercel

1. Go to [Vercel](https://vercel.com/new).
2. Click **Import** next to `SoumyadeepBera2005/Assignment`.
3. Leave all settings at their defaults:
   - **Framework Preset**: `Other`
   - **Root Directory**: `./`
   - **Build Command**: *(leave empty)*
   - **Output Directory**: *(leave empty)*
4. Click **Deploy**.
5. In ~15 seconds, Vercel gives you your live site URL:
   `https://assignment-xxxx.vercel.app`

---

## 🔗 Step 4: Connect Vercel to Render in 1 Click

1. Open your live Vercel site in the browser.
2. In the top navigation bar, click the **⚙️ Backend** button.
3. Paste your Render backend URL:
   ```
   https://home-credit-voice-agent.onrender.com
   ```
4. Click **⚡ Test Connection** to verify it responds with `✅ Backend online`.
5. Click **Save**.

The URL is saved in your browser, and the button badge will change to **Connected** (green). Your Vercel frontend is now fully wired up to your Render backend!

---

## 📞 Step 5: Retell AI / Bolna Voice Webhook (Optional)

In your Retell AI or Bolna dashboard, point the Custom LLM / Webhook endpoint to your Render server:
```
https://<YOUR-RENDER-URL>.onrender.com/api/retell-webhook
```

---

## 🧪 Step 6: Testing & Sanity Checks

1. **Send a Chat Message:** Type *"Hi, I want a 40 Lakh loan for residential property"* — Priya will respond and update the 7 eligibility checklist badges.
2. **Run the 16-Test Matrix:** Click **🧪 Run Test Matrix (16 Tests)** in the header to execute the complete test suite directly from your deployed backend.
3. **Voice Input (STT) & Speech (TTS):** Click the 🎙️ mic icon (works automatically because Vercel provides HTTPS).
