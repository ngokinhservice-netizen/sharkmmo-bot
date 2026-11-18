FROM python:3.12-slim

# Create user with UID 1000 (standard for Hugging Face Spaces & security)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY --chown=user:user backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=user:user backend /home/user/app/backend
COPY --chown=user:user .python-version /home/user/app/.python-version

# Create data directory and set permissions
RUN mkdir -p /home/user/app/data && chown -R user:user /home/user/app

USER user

# Set environment
ENV PYTHONPATH=/home/user/app
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

EXPOSE 7860

# Start backend (FastAPI + aiogram Bot polling)
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860} --proxy-headers"]
