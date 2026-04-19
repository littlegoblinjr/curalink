# Hybrid Deployment Guide: Cloud UI + Local LLM 🌐💻

This guide explains how to host Curalink on **Hugging Face Spaces** while running the **LM Studio LLM** on your local laptop to save costs.

## Architecture
1.  **Frontend/Backend**: Hosted on Hugging Face Spaces (Docker).
2.  **LLM**: Hosted on your Laptop (LM Studio).
3.  **Bridge**: A secure tunnel (Cloudflare) that lets Hugging Face "talk" to your localhost.

---

## 🛠️ Step 1: Create a Secure Tunnel on your Laptop
Since Hugging Face cannot see your `localhost`, you must create a public door to your LM Studio.

1.  **Download Cloudflared**: [Download here](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).
2.  **Open Terminal** and run:
    ```bash
    cloudflared.exe tunnel --url http://localhost:1234
    ```
3.  **Copy the URL**: It will look like `https://random-words-here.trycloudflare.com`. 
    > [!IMPORTANT]
    > This URL is the "Bridge" Hugging Face will use to reach your laptop. Keep this terminal open while you are testing!

---

## 🚀 Step 2: Deploy to Hugging Face Spaces
1.  **Create a New Space**: Choose "Docker" and "Blank".
2.  **Add Secrets**: Go to **Settings > Variables and Secrets**.
    - Add `LM_STUDIO_URL`: Paste your Cloudflare URL (e.g., `https://.../v1`).
    - Add `MONGODB_URI`: Your MongoDB Atlas connection string.
3.  **Upload the Codebase**: Put your project files in the Space.

---

## 📦 Step 3: Deployment Dockerfile
Create a file named `Dockerfile` (no extension) in your root directory:

```dockerfile
# Build Frontend
FROM node:18 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Setup Backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
# Copy static frontend build to backend to serve via FastAPI
COPY --from=frontend-build /app/frontend/dist /app/static

# Run it
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

---

## ✅ Success Criteria
- [ ] Laptop terminal is running `cloudflared` tunnel.
- [ ] Hugging Face Space shows "Running".
- [ ] Asking a question in the HF UI triggers your Laptop's GPU (LM Studio logs).
