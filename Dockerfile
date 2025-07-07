# Multi-stage build for production deployment

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
COPY frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY frontend/ ./
RUN yarn build

# Stage 2: Setup Python backend
FROM python:3.9-slim AS backend-setup
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY processors/ ./processors/
COPY scrapers/ ./scrapers/
COPY models/ ./models/
COPY api/ ./api/
COPY advisory_engine/ ./advisory_engine/

# Copy built frontend
COPY --from=frontend-build /app/frontend/build ./static/

# Create non-root user
RUN useradd --create-home --shell /bin/bash nextstep
RUN chown -R nextstep:nextstep /app
USER nextstep

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/api/health || exit 1

# Start the application
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]