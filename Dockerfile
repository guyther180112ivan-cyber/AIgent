FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements-minimal.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy frontend
COPY frontend /app/frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# Copy backend
WORKDIR /app
COPY backend /app/backend

# Expose port
EXPOSE 8000

# Run the application (both frontend and backend)
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
