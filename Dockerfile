# Build Frontend
FROM node:20 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
# The HF Space URL suffix / will be handled by the relative build
RUN npm run build

# Setup Backend
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
# Bake embedding weights so cold start on Render/HF does not download at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
# Copy static frontend build to backend/static to be served by FastAPI
COPY --from=frontend-build /app/frontend/dist /app/static

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
