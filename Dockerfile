# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    netcat-openbsd \
    curl \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . .

# Build Tailwind CSS (standalone CLI, no Node.js needed)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then \
      TW_ARCH="linux-arm64"; \
    else \
      TW_ARCH="linux-x64"; \
    fi && \
    curl -sLO "https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-${TW_ARCH}" && \
    chmod +x "tailwindcss-${TW_ARCH}" && \
    "./tailwindcss-${TW_ARCH}" -i static/css/input.css -o static/css/tailwind.css --minify && \
    rm "tailwindcss-${TW_ARCH}"

# Create necessary directories
RUN mkdir -p /app/media/elephants /app/staticfiles /app/logs && \
    chmod +x /app/entrypoint.sh

# Run entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
